from parseanything.interfaces import PageContext, Region
from parseanything.schema import BBox

def classify_page(ctx: PageContext) -> tuple[str, list[Region]]:
    """
    Classifies a page as digital, scanned, or mixed.
    Returns the kind and a list of regions needing OCR (if any).
    """
    if not ctx.pdf_page:
        return "image", []
        
    try:
        text_page = ctx.pdf_page.get_textpage()
        text = text_page.get_text_bounded()
        
        # Simple heuristic based on text length
        if len(text.strip()) > 50:
            return "digital", []
        elif len(text.strip()) > 0:
            return "mixed", []
        else:
            full_page_region = Region(
                bbox=BBox(x0=0, y0=0, x1=ctx.width, y1=ctx.height),
                label="scanned_content",
                score=1.0
            )
            return "scanned", [full_page_region]
    except Exception:
        return "scanned", []
