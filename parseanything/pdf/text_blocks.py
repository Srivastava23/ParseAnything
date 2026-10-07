import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region
from parseanything.registry import register_region_extractor, get_ocr_backend

class TextRegionExtractor:
    name = "text_extractor"
    handles = {"text", "title", "list", "caption", "footnote", "paragraph", "heading"}

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        text_content = ""
        
        if ctx.kind == "digital" and ctx.pdf_page:
            try:
                text_page = ctx.pdf_page.get_textpage()
                b = region.bbox
                # pdfium uses left, top, right, bottom
                text_content = text_page.get_text_bounded(left=b.x0, top=b.y0, right=b.x1, bottom=b.y1)
            except Exception:
                pass
                
        if not text_content.strip() and ctx.image:
            # Fallback to OCR if no text found or it's a scanned page
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(ctx.image, region.bbox)
                text_content = "\n".join([line.text for line in lines])
                
        block_type = BlockType.PARAGRAPH
        if region.label in ["title", "heading"]:
            block_type = BlockType.HEADING
        elif region.label == "list":
            block_type = BlockType.LIST
        elif region.label == "caption":
            block_type = BlockType.CAPTION
        elif region.label == "footnote":
            block_type = BlockType.FOOTNOTE
            
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            page=ctx.page_number,
            bbox=region.bbox,
            content=text_content.strip(),
            confidence=region.score,
            source_extractor=self.name
        )
        
        return [block]

extractor = TextRegionExtractor()
register_region_extractor(extractor)
