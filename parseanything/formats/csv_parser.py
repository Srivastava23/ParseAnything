import os
import csv
from typing import Any
from parseanything.interfaces import FormatParser
from parseanything.schema import Document, Page, Block, BlockType, TableData, TableCell
from parseanything.registry import register_format_parser
from parseanything.errors import ErrorCode, ParseError

class CSVParser(FormatParser):
    name = "csv"
    extensions = {"csv"}
    mime = {"text/csv"}

    def parse(self, path: str, opts: Any) -> Document:
        doc = Document(source=os.path.basename(path), format="csv")
        
        cells = []
        max_row = 0
        max_col = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for r, row in enumerate(reader):
                    max_row = r + 1
                    max_col = max(max_col, len(row))
                    for c, val in enumerate(row):
                        if val is not None and val != "":
                            cells.append(TableCell(
                                row=r,
                                col=c,
                                text=str(val)
                            ))
        except Exception as e:
            doc.errors.append(ParseError(code=ErrorCode.CORRUPT_FILE, message=str(e)))
            return doc
            
        page = Page(number=1, width=0, height=0, kind="virtual")
        
        # Add filename as title
        page.blocks.append(Block(
            id="p1_b1",
            type=BlockType.HEADING,
            page=1,
            content=os.path.basename(path),
            level=1,
            reading_order=1
        ))
        
        if cells:
            table_data = TableData(
                n_rows=max_row,
                n_cols=max_col,
                cells=cells,
                header_rows=1 if max_row > 0 else 0
            )
            page.blocks.append(Block(
                id="p1_b2",
                type=BlockType.TABLE,
                page=1,
                locator="csv:main",
                table=table_data,
                reading_order=2
            ))
            
        doc.pages.append(page)
        doc.stats.pages = 1
        doc.stats.blocks = len(page.blocks)
        return doc

register_format_parser(CSVParser())
