from parseanything.interfaces import LayoutBackend, PageContext
from parseanything.schema import Region, BBox
from parseanything.registry import register_layout

class RuleBasedLayoutBackend:
    name = "rule_based"
    
    def detect(self, ctx: PageContext) -> list[Region]:
        regions = []
        
        # A very basic rule-based layout detector
        # For a full implementation, this would use a vision model or deep PDF parsing.
        
        # Let's just return a full-page text region so the RegionExtractor is called.
        regions.append(Region(
            bbox=BBox(x0=0, y0=0, x1=ctx.width, y1=ctx.height),
            label="text",
            score=0.9
        ))
        
        return regions

# Register the backend
register_layout(RuleBasedLayoutBackend())
