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

class LLMBackend(Protocol):
    name: str
    def generate(self, prompt: str) -> str: ...
    def generate_json(self, prompt: str, schema: Any) -> Any: ...

class Embedder(Protocol):
    name: str
    def embed(self, text: str) -> list[float]: ...

class Retriever(Protocol):
    name: str
    def search(self, question: str, k: int) -> list[Any]: ...

class TTSBackend(Protocol):
    name: str
    def synthesize(self, text: str, output_path: str) -> dict[str, tuple[float, float]]: ...

class Exporter(Protocol):
    name: str
    def export(self, doc: Document, output_path: str, options: Any) -> None: ...

class SensitiveDetector(Protocol):
    name: str
    def detect(self, text: str) -> list[Any]: ...

class Redactor(Protocol):
    name: str
    def redact(self, doc: Document, findings: list[Any]) -> Document: ...

class AnomalyRule(Protocol):
    name: str
    def evaluate(self, doc: Document) -> list[Any]: ...
