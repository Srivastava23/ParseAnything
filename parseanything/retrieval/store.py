import sqlite3
from typing import Any, Optional
from parseanything.schema import Document, Block
from parseanything.interfaces import Retriever, Embedder
from parseanything.config import Options

class FastEmbedder(Embedder):
    name = "fastembed"
    def __init__(self):
        try:
            from fastembed import TextEmbedding
            self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._has_pkg = True
        except ImportError:
            self._has_pkg = False
            
    def embed(self, text: str) -> list[float]:
        if not self._has_pkg:
            return []
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

class SQLiteRetriever(Retriever):
    name = "sqlite"
    def __init__(self, doc: Document, opts: Options):
        self.doc = doc
        self.opts = opts
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        
        self.embedder = FastEmbedder()
        self.use_vector = opts.retrieval.use_vector and self.embedder._has_pkg
        
        try:
            if self.use_vector:
                import sqlite_vec
                self.conn.enable_load_extension(True)
                sqlite_vec.load(self.conn)
                self.conn.enable_load_extension(False)
        except Exception:
            self.use_vector = False
            
        self._build_index()

    def _build_index(self):
        c = self.conn.cursor()
        c.execute("CREATE VIRTUAL TABLE blocks_fts USING fts5(id UNINDEXED, text, section_path UNINDEXED)")
        if self.use_vector:
            c.execute("CREATE VIRTUAL TABLE blocks_vec USING vec0(id TEXT PRIMARY KEY, embedding float[384])")
            
        current_path = []
        for page in self.doc.pages:
            for block in page.blocks:
                if block.type == "heading":
                    level = block.level or 1
                    current_path = current_path[:level-1]
                    current_path.append(block.content.strip())
                    
                path_str = " > ".join(current_path)
                
                text = block.content
                if block.table and block.table.cells:
                    text += " " + " ".join([cell.text for cell in block.table.cells])
                    
                c.execute("INSERT INTO blocks_fts (id, text, section_path) VALUES (?, ?, ?)", (block.id, text, path_str))
                
                if self.use_vector:
                    emb = self.embedder.embed(text)
                    if emb:
                        import struct
                        emb_blob = struct.pack(f"{len(emb)}f", *emb)
                        c.execute("INSERT INTO blocks_vec (id, embedding) VALUES (?, ?)", (block.id, emb_blob))
                        
        self.conn.commit()

    def search(self, question: str, k: int = 5) -> list[Any]:
        c = self.conn.cursor()
        # Ensure FTS query syntax is safe
        query_safe = question.replace('"', '""')
        try:
            c.execute("SELECT id, text, section_path, bm25(blocks_fts) as score FROM blocks_fts WHERE blocks_fts MATCH ? ORDER BY score LIMIT ?", (f'"{query_safe}"', k*2))
            bm25_results = c.fetchall()
        except sqlite3.OperationalError:
            bm25_results = []
        
        scores = {}
        for idx, row in enumerate(bm25_results):
            scores[row['id']] = {"score": 1.0 / (idx + 60), "path": row['section_path']}
            
        if self.use_vector:
            emb = self.embedder.embed(question)
            if emb:
                import struct
                emb_blob = struct.pack(f"{len(emb)}f", *emb)
                try:
                    c.execute("SELECT id, distance FROM blocks_vec WHERE embedding MATCH ? AND k = ?", (emb_blob, k*2))
                    vec_results = c.fetchall()
                    for idx, row in enumerate(vec_results):
                        if row['id'] not in scores:
                            scores[row['id']] = {"score": 0, "path": ""}
                        scores[row['id']]["score"] += 1.0 / (idx + 60)
                except Exception:
                    pass
                    
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x]["score"], reverse=True)[:k]
        
        results = []
        for bid in sorted_ids:
            for page in self.doc.pages:
                for block in page.blocks:
                    if block.id == bid:
                        results.append({
                            "block": block,
                            "score": scores[bid]["score"],
                            "path": scores[bid]["path"]
                        })
                        break
        return results
