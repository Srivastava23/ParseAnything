from parseanything.schema import Document

def assemble_document(doc: Document):
    try:
        from parseanything.pdf.reading_order import order_blocks
    except ImportError:
        def order_blocks(blocks, page): return sorted(blocks, key=lambda b: getattr(b.bbox, "y0", 0) if b.bbox else 0)

    try:
        from parseanything.tables.merge import merge_cross_page_tables
    except ImportError:
        def merge_cross_page_tables(blocks_by_page): return blocks_by_page

    blocks_by_page = {page.number: page.blocks for page in doc.pages}
    blocks_by_page = merge_cross_page_tables(blocks_by_page)
    
    global_reading_order = 0
    blocks_count = 0
    flagged_count = 0
    
    for page in doc.pages:
        page.blocks = blocks_by_page.get(page.number, page.blocks)
        page.blocks = order_blocks(page.blocks, page)
        
        for idx, block in enumerate(page.blocks):
            block.id = f"p{page.number}_b{idx}"
            block.reading_order = global_reading_order
            global_reading_order += 1
            blocks_count += 1
            if block.flagged:
                flagged_count += 1
                
    doc.stats.blocks = blocks_count
    doc.stats.flagged_blocks = flagged_count
