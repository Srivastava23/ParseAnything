from parseanything.schema import Block, BlockType, Region, BBox
from parseanything.math.extract import EquationRegionExtractor
from parseanything.interfaces import PageContext

class MockImage:
    def crop(self, bbox):
        return self

class MockContext(PageContext):
    def __init__(self):
        self.page_number = 1
        self.kind = "image"
        self.image = MockImage()

def test_math_extractor_fallback():
    ctx = MockContext()
    region = Region(bbox=BBox(x0=0, y0=0, x1=100, y1=100), label="equation", score=0.9)
    extractor = EquationRegionExtractor()
    
    blocks = extractor.extract(ctx, region)
    assert len(blocks) == 1
    block = blocks[0]
    
    assert block.type == BlockType.EQUATION
    # Without pix2tex installed in test environment, it should fallback to OCR or return no latex
    assert block.latex is None or "BACKEND_UNAVAILABLE" in block.meta
