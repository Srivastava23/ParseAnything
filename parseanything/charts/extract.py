import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region
from parseanything.registry import register_region_extractor, get_vlm_backend, get_ocr_backend

class ChartRegionExtractor:
    name = "chart_extractor"
    handles = {"chart", "figure"}

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        crop = None
        if ctx.image:
            b = region.bbox
            crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
        
        chart_data = None
        content = ""
        
        # 1. Try VLM
        for vlm_name in ["gpt4v", "gemini", "stub_vlm"]:
            vlm = get_vlm_backend(vlm_name)
            if vlm and crop:
                try:
                    chart_data = vlm.describe_chart(crop)
                    if chart_data:
                        break
                except Exception:
                    pass
                    
        # 2. OCR Fallback
        if chart_data is None and crop:
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(crop)
                content = "\n".join([line.text for line in lines])

        block_type = BlockType.CHART if region.label == "chart" else BlockType.FIGURE
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            page=ctx.page_number,
            bbox=region.bbox,
            chart=chart_data,
            content=content,
            confidence=region.score,
            source_extractor=self.name
        )
        return [block]

extractor = ChartRegionExtractor()
register_region_extractor(extractor)
