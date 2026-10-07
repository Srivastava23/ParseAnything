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
        
        import hashlib
        for idx, block in enumerate(page.blocks):
            # Stable deterministic hash
            bbox_str = f"{block.bbox.x0},{block.bbox.y0},{block.bbox.x1},{block.bbox.y1}" if block.bbox else "none"
            id_str = f"{doc.source}_{page.number}_{bbox_str}_{block.type.value}"
            block.id = hashlib.md5(id_str.encode()).hexdigest()[:12]
            
            # Fill provenance if not present
            if not block.provenance:
                from parseanything.schema import Provenance
                block.provenance = Provenance(
                    page=page.number,
                    bbox=block.bbox,
                    source_type=page.kind,
                    extractor=block.source_extractor,
                    confidence=block.confidence
                )
            block.reading_order = global_reading_order
            global_reading_order += 1
            blocks_count += 1
            if block.flagged:
                flagged_count += 1
                
    doc.stats.blocks = blocks_count
    doc.stats.flagged_blocks = flagged_count
