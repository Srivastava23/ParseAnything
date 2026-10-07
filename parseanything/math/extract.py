import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region
from parseanything.registry import register_region_extractor, get_vlm_backend, get_ocr_backend

class EquationRegionExtractor:
    name = "equation_extractor"
    handles = {"equation", "math"}

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        crop = None
        if ctx.image:
            b = region.bbox
            crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
            
        latex_code = None
        content = ""
        
        for vlm_name in ["gpt4v", "gemini", "stub_vlm"]:
            vlm = get_vlm_backend(vlm_name)
            if vlm and crop:
                try:
                    latex_code = vlm.read_equation(crop)
                    if latex_code:
                        break
                except Exception:
                    pass
                    
        if not latex_code and crop:
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(crop)
                content = "\n".join([line.text for line in lines])
                
        block = Block(
            id=str(uuid.uuid4()),
            type=BlockType.EQUATION,
            page=ctx.page_number,
            bbox=region.bbox,
            latex=latex_code,
            content=content,
            confidence=region.score,
            source_extractor=self.name
        )
        return [block]

extractor = EquationRegionExtractor()
register_region_extractor(extractor)
