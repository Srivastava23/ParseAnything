from typing import Protocol, Any, Optional
from pydantic import BaseModel
from parseanything.schema import BBox, Block, ChartData, Document, Region

class PageContext:
    def __init__(self, page_number: int, width: float, height: float, image: Any, scale: float, pdf_page: Optional[Any], kind: str):
        self.page_number = page_number
        self.width = width
        self.height = height
        self.image = image
        self.scale = scale
        self.pdf_page = pdf_page
        self.kind = kind

class OCRLine(BaseModel):
    text: str
    bbox: BBox
    confidence: float

class OCRBackend(Protocol):
    name: str
    def ocr(self, image: Any, bbox: Optional[BBox] = None) -> list[OCRLine]: ...

class LayoutBackend(Protocol):
    name: str
    def detect(self, ctx: PageContext) -> list[Region]: ...

class VLMBackend(Protocol):
    name: str
    def describe_chart(self, image: Any) -> ChartData: ...
    def read_equation(self, image: Any) -> str: ...

class RegionExtractor(Protocol):
    name: str
    handles: set[str]
    def extract(self, ctx: PageContext, region: Region) -> list[Block]: ...

class FormatParser(Protocol):
    name: str
    extensions: set[str]
    mime: set[str]
    def parse(self, path: str, opts: Any) -> Document: ...
