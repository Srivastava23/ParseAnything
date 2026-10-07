import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region, TableData, TableCell
from parseanything.registry import register_region_extractor, get_ocr_backend

class TableRegionExtractor:
    name = "table_extractor"
    handles = {"table"}

    def _extract_grid_and_cells(self, ctx: PageContext, region: Region) -> TableData:
        # Dummy heuristic for grid lines, rowspan, colspan
        # Real implementation would run a table structure recognition model (e.g. TableTransformer)
        
        # Simulate table extraction
        text_content = ""
        if ctx.kind == "digital" and ctx.pdf_page:
            try:
                text_page = ctx.pdf_page.get_textpage()
                b = region.bbox
                text_content = text_page.get_text_bounded(left=b.x0, top=b.y0, right=b.x1, bottom=b.y1)
            except Exception:
                pass
                
        if not text_content.strip() and ctx.image:
            b = region.bbox
            crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
            ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
            if ocr:
                lines = ocr.ocr(crop)
                text_content = "\n".join([line.text for line in lines])
                
        cells = [
            TableCell(row=0, col=0, rowspan=1, colspan=1, text=text_content, is_header=True)
        ]
        
        return TableData(
            n_rows=1,
            n_cols=1,
            cells=cells,
            header_rows=1,
            pages=[ctx.page_number]
        )

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        table_data = self._extract_grid_and_cells(ctx, region)
        
        block = Block(
            id=str(uuid.uuid4()),
            type=BlockType.TABLE,
            page=ctx.page_number,
            bbox=region.bbox,
            table=table_data,
            confidence=region.score,
            source_extractor=self.name
        )
        return [block]

extractor = TableRegionExtractor()
register_region_extractor(extractor)
