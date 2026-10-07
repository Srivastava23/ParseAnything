from parseanything.interfaces import OCRBackend, OCRLine
from parseanything.schema import BBox
from parseanything.registry import register_ocr
from PIL import Image
import numpy as np

class RapidOCRBackend:
    name = "rapidocr"
    
    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR()
        except ImportError:
            self.engine = None
            
    def ocr(self, image: Image.Image, bbox: BBox = None) -> list[OCRLine]:
        if not self.engine:
            return []
            
        if bbox:
            img = image.crop((bbox.x0, bbox.y0, bbox.x1, bbox.y1))
        else:
            img = image
            
        # RapidOCR requires numpy array
        img_array = np.array(img)
        result, _ = self.engine(img_array)
        
        lines = []
        if result:
            for dt_box, rec_text, rec_score in result:
                xs = [p[0] for p in dt_box]
                ys = [p[1] for p in dt_box]
                
                b = BBox(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))
                if bbox:
                    b.x0 += bbox.x0
                    b.x1 += bbox.x0
                    b.y0 += bbox.y0
                    b.y1 += bbox.y0
                    
                lines.append(OCRLine(text=rec_text, bbox=b, confidence=rec_score))
                
        return lines

register_ocr(RapidOCRBackend())
