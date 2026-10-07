import uuid
from parseanything.interfaces import RegionExtractor, PageContext
from parseanything.schema import Block, BlockType, Region, TableData, TableCell
from parseanything.registry import register_region_extractor, get_ocr_backend

class TableRegionExtractor(RegionExtractor):
    name = "table_extractor"
    handles = {"table"}

    def _generate_markdown(self, table_data: TableData) -> str:
        if not table_data.cells:
            return ""
            
        # Group by row
        rows = {}
        for cell in table_data.cells:
            if cell.row not in rows:
                rows[cell.row] = []
            rows[cell.row].append(cell)
            
        md = []
        for r in range(table_data.n_rows):
            if r not in rows:
                continue
            cells = sorted(rows[r], key=lambda c: c.col)
            row_md = "| " + " | ".join(c.text.replace("\n", " ").replace("|", "\\|") for c in cells) + " |"
            md.append(row_md)
            if r == table_data.header_rows - 1 or (table_data.header_rows == 0 and r == 0):
                md.append("|" + "|".join(["---"] * len(cells)) + "|")
        return "\n".join(md)
        
    def _generate_html(self, table_data: TableData) -> str:
        if not table_data.cells:
            return ""
            
        # Group by row
        rows = {}
        for cell in table_data.cells:
            if cell.row not in rows:
                rows[cell.row] = []
            rows[cell.row].append(cell)
            
        html = ["<table>"]
        for r in range(table_data.n_rows):
            if r not in rows:
                continue
            html.append("  <tr>")
            cells = sorted(rows[r], key=lambda c: c.col)
            for c in cells:
                tag = "th" if c.is_header else "td"
                rowspan = f' rowspan="{c.rowspan}"' if c.rowspan > 1 else ""
                colspan = f' colspan="{c.colspan}"' if c.colspan > 1 else ""
                html.append(f"    <{tag}{rowspan}{colspan}>{c.text}</{tag}>")
            html.append("  </tr>")
        html.append("</table>")
        return "\n".join(html)

    def _extract_grid_and_cells(self, ctx: PageContext, region: Region, block: Block) -> TableData:
        cells = []
        n_rows = 1
        n_cols = 1
        
        try:
            if getattr(ctx, "source_path", "").lower().endswith(".pdf"):
                import pdfplumber
                with pdfplumber.open(ctx.source_path) as pdf:
                    if ctx.page_number - 1 < len(pdf.pages):
                        plumber_page = pdf.pages[ctx.page_number - 1]
                        tables = plumber_page.find_tables()
                        if tables:
                            b = region.bbox
                            scale = getattr(ctx, "scale", 1.0)
                            bx0, by0, bx1, by1 = b.x0 / scale, b.y0 / scale, b.x1 / scale, b.y1 / scale
                            best_table = None
                            max_area = 0
                            for t in tables:
                                tx0, ty0, tx1, ty1 = t.bbox
                                ix0 = max(bx0, tx0)
                                iy0 = max(by0, ty0)
                                ix1 = min(bx1, tx1)
                                iy1 = min(by1, ty1)
                                if ix1 > ix0 and iy1 > iy0:
                                    area = (ix1 - ix0) * (iy1 - iy0)
                                    if area > max_area:
                                        max_area = area
                                        best_table = t
                            if best_table:
                                extracted_table = best_table.extract()
                                n_rows = len(extracted_table)
                                n_cols = max(len(row) for row in extracted_table) if n_rows > 0 else 0
                                for r_idx, row in enumerate(extracted_table):
                                    for c_idx, cell_text in enumerate(row):
                                        if cell_text is not None:
                                            cells.append(TableCell(
                                                row=r_idx, col=c_idx, rowspan=1, colspan=1,
                                                text=str(cell_text).strip(), is_header=(r_idx == 0)
                                            ))
        except Exception as e:
            block.meta["PDFPLUMBER_ERROR"] = str(e)

        if not cells:
            text_content = ""
            try:
                if ctx.image:
                    b = region.bbox
                    crop = ctx.image.crop((b.x0, b.y0, b.x1, b.y1))
                    ocr = get_ocr_backend("rapidocr") or get_ocr_backend("tesseract")
                    if ocr:
                        lines = ocr.ocr(crop)
                        text_content = "\n".join([line.text for line in lines])
                if not text_content and ctx.kind == "digital" and hasattr(ctx, "_pdf"):
                    text_page = ctx.pdf_page.get_textpage()
                    b = region.bbox
                    text_content = text_page.get_text_bounded(left=b.x0, top=b.y0, right=b.x1, bottom=b.y1)
            except Exception as e:
                block.flagged = True
                block.flag_reason = f"Table fallback extraction failed: {str(e)}"
            cells = [TableCell(row=0, col=0, rowspan=1, colspan=1, text=text_content, is_header=True)]
            n_rows = 1
            n_cols = 1

        table_data = TableData(
            n_rows=n_rows,
            n_cols=n_cols,
            cells=cells,
            header_rows=1 if n_rows > 0 else 0,
            pages=[ctx.page_number]
        )
        table_data.markdown = self._generate_markdown(table_data)
        table_data.html = self._generate_html(table_data)
        return table_data

    def extract(self, ctx: PageContext, region: Region) -> list[Block]:
        block = Block(
            id=str(uuid.uuid4()),
            type=BlockType.TABLE,
            page=ctx.page_number,
            bbox=region.bbox,
            confidence=region.score,
            source_extractor=self.name
        )
        table_data = self._extract_grid_and_cells(ctx, region, block)
        block.table = table_data
        block.content = table_data.markdown if table_data.markdown else ""
        
        from parseanything.tables.numbers import validate_financial_numbers
        block = validate_financial_numbers(block)
        
        return [block]

extractor = TableRegionExtractor()
register_region_extractor(extractor)
