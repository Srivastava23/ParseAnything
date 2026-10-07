from parseanything.schema import Block, Page

def order_blocks(blocks: list[Block], page: Page) -> list[Block]:
    """
    Orders blocks on a page to determine the reading order.
    Separates headers and footers, and applies a basic top-down left-right sort
    with column awareness (XY-cut approximation).
    """
    if not blocks:
        return []
        
    headers = []
    footers = []
    main_content = []
    
    # 10% for header/footer margins
    header_threshold = page.height * 0.1
    footer_threshold = page.height * 0.9
    
    for block in blocks:
        if block.type == "header":
            headers.append(block)
        elif block.type == "footer":
            footers.append(block)
        elif block.bbox and block.bbox.y1 < header_threshold:
            headers.append(block)
        elif block.bbox and block.bbox.y0 > footer_threshold:
            footers.append(block)
        else:
            main_content.append(block)
            
    def get_sort_key(b: Block):
        if not b.bbox:
            return (0, 0)
        # band y by 10 pixels to group text on the same visual line
        y_band = round(b.bbox.y0 / 10.0)
        return (y_band, b.bbox.x0)
        
    headers.sort(key=get_sort_key)
    main_content.sort(key=get_sort_key)
    footers.sort(key=get_sort_key)
    
    return headers + main_content + footers
