import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region
from parseanything.registry import register_region_extractor, get_ocr_backend

class EquationRegionExtractor(RegionExtractor):
    name = "equation_extractor"
    handles = {"equation", "math"}

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        crop = None
        if ctx.image:
            b = region.bbox
            crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
            
        latex_code = None
        content = ""
        flagged = False
        flag_reason = None
        meta = {}
        
        # 1. Try pix2tex (LaTeX-OCR)
        if crop:
            try:
                from pix2tex.cli import LatexOCR
                model = LatexOCR()
                latex_code = model(crop)
            except ImportError:
                meta["BACKEND_UNAVAILABLE"] = "pix2tex (LaTeX-OCR) not installed."
            except Exception as e:
                meta["BACKEND_ERROR"] = f"pix2tex error: {str(e)}"
                    
        # 2. OCR Fallback
        if not latex_code and crop:
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(crop)
                content = "\n".join([line.text for line in lines])
                flagged = True
                flag_reason = "Math LaTeX extraction failed, fell back to standard OCR."
                
        if latex_code:
            content = f"$${latex_code}$$"
            
        block = Block(
            id=str(uuid.uuid4()),
            type=BlockType.EQUATION,
            page=ctx.page_number,
            bbox=region.bbox,
            latex=latex_code,
            content=content,
            confidence=region.score,
            flagged=flagged,
            flag_reason=flag_reason,
            meta=meta,
            source_extractor=self.name
        )
        return [block]

extractor = EquationRegionExtractor()
register_region_extractor(extractor)
