from typing import Optional
from parseanything.interfaces import OCRBackend, LayoutBackend, VLMBackend, RegionExtractor, FormatParser

_ocr_backends: dict[str, OCRBackend] = {}
_layout_backends: dict[str, LayoutBackend] = {}
_vlm_backends: dict[str, VLMBackend] = {}
_region_extractors: dict[str, list[RegionExtractor]] = {}
_format_parsers: dict[str, FormatParser] = {}

def register_ocr(backend: OCRBackend):
    _ocr_backends[backend.name] = backend

def register_layout(backend: LayoutBackend):
    _layout_backends[backend.name] = backend

def register_vlm(backend: VLMBackend):
    _vlm_backends[backend.name] = backend

def register_region_extractor(extractor: RegionExtractor):
    for handle in extractor.handles:
        if handle not in _region_extractors:
            _region_extractors[handle] = []
        _region_extractors[handle].append(extractor)

def register_format_parser(parser: FormatParser):
    _format_parsers[parser.name] = parser

def get_ocr_backend(name: str) -> Optional[OCRBackend]:
    return _ocr_backends.get(name)

def get_layout_backend(name: str) -> Optional[LayoutBackend]:
    return _layout_backends.get(name)

def get_vlm_backend(name: str) -> Optional[VLMBackend]:
    return _vlm_backends.get(name)

def get_region_extractors(label: str) -> list[RegionExtractor]:
    return _region_extractors.get(label, [])

def get_format_parser(name: str) -> Optional[FormatParser]:
    return _format_parsers.get(name)

# stub backends implementation
class StubOCR:
    name = "stub_ocr"
    def ocr(self, image, bbox=None): return []

class StubLayout:
    name = "stub_layout"
    def detect(self, ctx): return []

class StubVLM:
    name = "stub_vlm"
    def describe_chart(self, image):
        from parseanything.schema import ChartData
        return ChartData(chart_type="stub")
    def read_equation(self, image): return ""

register_ocr(StubOCR())
register_layout(StubLayout())
register_vlm(StubVLM())
