import pytest
from parseanything.schema import Document, Page, Block, BlockType
from parseanything.config import Options
from parseanything.retrieval.store import SQLiteRetriever

def test_sqlite_retriever():
    opts = Options()
    opts.retrieval.use_vector = False
    
    b1 = Block(id="b1", type=BlockType.HEADING, page=1, content="Introduction")
    b2 = Block(id="b2", type=BlockType.PARAGRAPH, page=1, content="This is the first paragraph about apples.")
    b3 = Block(id="b3", type=BlockType.PARAGRAPH, page=2, content="This is about bananas.")
    
    doc = Document(source="test", format="pdf", pages=[
        Page(number=1, width=100, height=100, blocks=[b1, b2]),
        Page(number=2, width=100, height=100, blocks=[b3])
    ])
    
    retriever = SQLiteRetriever(doc, opts)
    results = retriever.search("apples", k=1)
    
    assert len(results) == 1
    assert results[0]["block"].id == "b2"
    assert results[0]["path"] == "Introduction"
    
def test_sqlite_retriever_no_match():
    opts = Options()
    opts.retrieval.use_vector = False
    b1 = Block(id="b1", type=BlockType.PARAGRAPH, page=1, content="Nothing here")
    doc = Document(source="test", format="pdf", pages=[Page(number=1, width=100, height=100, blocks=[b1])])
    
    retriever = SQLiteRetriever(doc, opts)
    results = retriever.search("apples", k=1)
    assert len(results) == 0
