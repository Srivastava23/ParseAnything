from parseanything.schema import Block, BlockType, Region, BBox
from parseanything.charts.extract import ChartRegionExtractor
from parseanything.interfaces import PageContext

class MockImage:
    def crop(self, bbox):
        return self

class MockContext(PageContext):
    def __init__(self):
        self.page_number = 1
        self.kind = "image"
        self.image = MockImage()

def test_chart_extractor_fallback():
    # Test when no VLM is available
    ctx = MockContext()
    region = Region(bbox=BBox(x0=0, y0=0, x1=100, y1=100), label="chart", score=0.9)
    extractor = ChartRegionExtractor()
    
    blocks = extractor.extract(ctx, region)
    assert len(blocks) == 1
    block = blocks[0]
    
    assert block.type == BlockType.CHART
    assert block.flagged == True
    assert "chart values not extracted" in block.flag_reason
    assert block.chart is not None
    assert block.chart.values_estimated == True
