from parseanything.interfaces import OCRBackend, OCRLine
from parseanything.schema import BBox
from parseanything.registry import register_ocr
from PIL import Image

class TesseractOCRBackend:
    name = "tesseract"
    
    def ocr(self, image: Image.Image, bbox: BBox = None) -> list[OCRLine]:
        try:
            import pytesseract
        except ImportError:
            return []
            
        if bbox:
            img = image.crop((bbox.x0, bbox.y0, bbox.x1, bbox.y1))
        else:
            img = image
            
        import os
        lang = os.getenv("TESSERACT_LANG", "eng")
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        
        lines = []
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            conf = int(data['conf'][i])
            if conf > -1:
                text = data['text'][i].strip()
                if not text:
                    continue
                    
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                if bbox:
                    x += bbox.x0
                    y += bbox.y0
                
                b = BBox(x0=x, y0=y, x1=x+w, y1=y+h)
                lines.append(OCRLine(text=text, bbox=b, confidence=conf/100.0))
                
        return lines

register_ocr(TesseractOCRBackend())
