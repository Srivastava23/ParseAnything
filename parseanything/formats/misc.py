import os
from typing import Any
from parseanything.interfaces import FormatParser
from parseanything.schema import Document, Page, Block, BlockType
from parseanything.registry import register_format_parser
from parseanything.errors import ErrorCode, ParseError
from bs4 import BeautifulSoup

class HtmlParser(FormatParser):
    name = "html"
    extensions = {"html", "htm"}
    mime = {"text/html"}

    def parse(self, path: str, opts: Any) -> Document:
        doc = Document(source=os.path.basename(path), format="html")
        page = Page(number=1, width=0, height=0, kind="virtual")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except Exception as e:
            doc.errors.append(ParseError(code=ErrorCode.CORRUPT_FILE, message=str(e)))
            return doc
            
        blocks = []
        block_idx = 1
        
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            text = elem.get_text(strip=True)
            if not text:
                continue
                
            btype = BlockType.PARAGRAPH
            level = None
            if elem.name.startswith('h'):
                btype = BlockType.HEADING
                level = int(elem.name[1])
            elif elem.name == 'li':
                btype = BlockType.LIST
                
            blocks.append(Block(
                id=f"p1_b{block_idx}",
                type=btype,
                page=1,
                content=text,
                level=level,
                reading_order=block_idx
            ))
            block_idx += 1
            
        page.blocks = blocks
        doc.pages.append(page)
        doc.stats.pages = 1
        doc.stats.blocks = len(blocks)
        return doc

register_format_parser(HtmlParser())
