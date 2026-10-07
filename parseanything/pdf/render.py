import pypdfium2 as pdfium
from PIL import Image
import os
from parseanything.interfaces import PageContext
from parseanything.imageparse.pipeline import render_image_page

def _is_image(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]

def get_page_count(path: str) -> int:
    if _is_image(path):
        return 1
    pdf = pdfium.PdfDocument(path)
    count = len(pdf)
    pdf.close()
    return count

def render_page(path: str, page_idx: int, dpi: int = 72) -> PageContext:
    if _is_image(path):
        return render_image_page(path, page_idx, dpi)
        
    pdf = pdfium.PdfDocument(path)
    page = pdf[page_idx - 1]
    scale = dpi / 72.0
    
    width, height = page.get_size()
    
    bitmap = page.render(scale=scale)
    image = bitmap.to_pil()
    
    ctx = PageContext(
        page_number=page_idx,
        width=width,
        height=height,
        image=image,
        scale=scale,
        pdf_page=page,
        kind="digital"
    )
    ctx._pdf = pdf 
    return ctx
