from parseanything.interfaces import LayoutBackend, PageContext, Region
from parseanything.schema import BBox
from parseanything.registry import register_layout

class DoclingLayoutBackend:
    name = "docling"
    
    def __init__(self):
        self._predictor = None
        
    def detect(self, ctx: PageContext) -> list[Region]:
        try:
            from docling.models.layout_model import LayoutPredictor
            if not self._predictor:
                self._predictor = LayoutPredictor()
                
            # Assume predictor takes PIL Image and returns objects with bbox and label
            preds = self._predictor.predict(ctx.image)
            
            regions = []
            label_map = {
                "Text": "text", "Title": "heading", "Section-header": "heading",
                "Table": "table", "Picture": "figure", "Figure": "figure",
                "Formula": "equation", "Caption": "caption", "List-item": "list",
                "Page-header": "header", "Page-footer": "footer", "Footnote": "footnote"
            }
            
            for p in preds:
                lbl = label_map.get(p.label, "other")
                regions.append(Region(
                    bbox=BBox(x0=p.bbox[0], y0=p.bbox[1], x1=p.bbox[2], y1=p.bbox[3]),
                    label=lbl,
                    score=getattr(p, "confidence", 1.0)
                ))
            return regions
        except ImportError:
            return RuleBasedLayoutBackend().detect(ctx)
        except Exception as e:
            return RuleBasedLayoutBackend().detect(ctx)

class RuleBasedLayoutBackend:
    name = "rule_based"
    
    def detect(self, ctx: PageContext) -> list[Region]:
        regions = []
        if ctx.kind != "digital" or not ctx.pdf_page:
            # Fallback to single block for images/scanned
            regions.append(Region(
                bbox=BBox(x0=0, y0=0, x1=ctx.width, y1=ctx.height),
                label="text",
                score=0.5
            ))
            return regions
            
        try:
            text_page = ctx.pdf_page.get_textpage()
            # Very basic clustering: every 50 pixels vertically is a new block
            # pypdfium2 get_rectboxes() returns (left, top, right, bottom)
            rects = text_page.get_rectboxes()
            
            if not rects:
                 regions.append(Region(bbox=BBox(x0=0, y0=0, x1=ctx.width, y1=ctx.height), label="text", score=0.5))
                 return regions
                 
            # Sort by top (y0)
            rects = sorted(rects, key=lambda r: r[1])
            
            current_block = None
            for r in rects:
                if current_block is None:
                    current_block = [r[0], r[1], r[2], r[3]]
                else:
                    # If vertical gap > 20, new block
                    if r[1] - current_block[3] > 20:
                        regions.append(Region(
                            bbox=BBox(x0=current_block[0], y0=current_block[1], x1=current_block[2], y1=current_block[3]),
                            label="text",
                            score=0.8
                        ))
                        current_block = [r[0], r[1], r[2], r[3]]
                    else:
                        # Expand block
                        current_block[0] = min(current_block[0], r[0])
                        current_block[2] = max(current_block[2], r[2])
                        current_block[3] = max(current_block[3], r[3])
                        
            if current_block:
                regions.append(Region(
                    bbox=BBox(x0=current_block[0], y0=current_block[1], x1=current_block[2], y1=current_block[3]),
                    label="text",
                    score=0.8
                ))
                
        except Exception:
            regions.append(Region(bbox=BBox(x0=0, y0=0, x1=ctx.width, y1=ctx.height), label="text", score=0.5))
            
        return regions

register_layout(DoclingLayoutBackend())
register_layout(RuleBasedLayoutBackend())
