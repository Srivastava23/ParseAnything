import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region, ChartData
from parseanything.registry import register_region_extractor, get_vlm_backend, get_ocr_backend

class ChartRegionExtractor(RegionExtractor):
    name = "chart_extractor"
    handles = {"chart", "figure"}

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        crop = None
        if ctx.image:
            b = region.bbox
            crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
        
        chart_data = None
        content = ""
        flagged = False
        flag_reason = None
        
        is_chart = region.label == "chart"
        
        # 1. Digital PDF text layer (if available and digital)
        if is_chart and ctx.kind == "digital" and hasattr(ctx, "_pdf"):
            try:
                text_page = ctx.pdf_page.get_textpage()
                b = region.bbox
                content = text_page.get_text_bounded(left=b.x0, top=b.y0, right=b.x1, bottom=b.y1)
            except Exception:
                pass

        # 2. Try VLM
        if is_chart:
            # We want to try vlm_local, then vlm_gemini, then fallback
            for vlm_name in ["vlm_local", "vlm_gemini"]:
                vlm = get_vlm_backend(vlm_name)
                if vlm and crop:
                    try:
                        chart_data = vlm.describe_chart(crop)
                        if chart_data:
                            break
                    except Exception:
                        pass
                        
        # 3. No VLM available fallback (OCR)
        if is_chart and chart_data is None and crop:
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(crop)
                content = "\n".join([line.text for line in lines])
            
            # Create fallback ChartData
            chart_data = ChartData(
                chart_type="unknown",
                values_estimated=True,
                data_table_markdown=content,
            )
            flagged = True
            flag_reason = "chart values not extracted (no VLM)"
            
        if chart_data and chart_data.data_table_markdown:
            content_str = chart_data.data_table_markdown
            if chart_data.caption:
                content_str += f"\n\nCaption: {chart_data.caption}"
            content = content_str

        block_type = BlockType.CHART if is_chart else BlockType.FIGURE
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            page=ctx.page_number,
            bbox=region.bbox,
            chart=chart_data if is_chart else None,
            content=content,
            confidence=region.score,
            flagged=flagged,
            flag_reason=flag_reason,
            source_extractor=self.name
        )
        
        # Handle backend unavailable gracefully
        if is_chart and not chart_data and flagged:
            block.meta["BACKEND_UNAVAILABLE"] = "No VLM backend succeeded."

        return [block]

extractor = ChartRegionExtractor()
register_region_extractor(extractor)
