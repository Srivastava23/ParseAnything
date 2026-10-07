from parseanything.schema import Block, BlockType, TableData, TableCell, BBox
from parseanything.tables.merge import merge_cross_page_tables
from parseanything.tables.numbers import validate_financial_numbers

def test_merge_cross_page_tables():
    block1 = Block(
        id="1", type=BlockType.TABLE, page=1, bbox=BBox(x0=0, y0=0, x1=100, y1=100),
        table=TableData(
            n_rows=2, n_cols=2, header_rows=1, pages=[1],
            cells=[
                TableCell(row=0, col=0, text="H1", is_header=True),
                TableCell(row=0, col=1, text="H2", is_header=True),
                TableCell(row=1, col=0, text="A"),
                TableCell(row=1, col=1, text="B")
            ]
        )
    )
    block2 = Block(
        id="2", type=BlockType.TABLE, page=2, bbox=BBox(x0=0, y0=0, x1=100, y1=100),
        table=TableData(
            n_rows=2, n_cols=2, header_rows=1, pages=[2],
            cells=[
                TableCell(row=0, col=0, text="H1", is_header=True),
                TableCell(row=0, col=1, text="H2", is_header=True),
                TableCell(row=1, col=0, text="C"),
                TableCell(row=1, col=1, text="D")
            ]
        )
    )
    blocks_by_page = {1: [block1], 2: [block2]}
    merged = merge_cross_page_tables(blocks_by_page)
    
    assert len(merged[1]) == 1
    assert len(merged[2]) == 0
    
    table = merged[1][0].table
    assert table.n_rows == 3 # 1 header + 2 data rows
    assert len(table.cells) == 6
    assert table.pages == [1, 2]

def test_validate_financial_numbers():
    block = Block(
        id="1", type=BlockType.TABLE, page=1,
        table=TableData(
            n_rows=1, n_cols=2,
            cells=[
                TableCell(row=0, col=0, text="1O0"), # O instead of 0
                TableCell(row=0, col=1, text="200")
            ]
        )
    )
    validated = validate_financial_numbers(block)
    assert validated.flagged == True
    assert "Suspicious OCR characters" in validated.flag_reason
    assert validated.confidence == 0.8
