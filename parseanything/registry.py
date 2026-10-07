from typing import Optional
from parseanything.interfaces import (
    OCRBackend, LayoutBackend, VLMBackend, RegionExtractor, FormatParser,
    LLMBackend, Embedder, Retriever, TTSBackend, Exporter, SensitiveDetector, Redactor, AnomalyRule
)

_ocr_backends: dict[str, OCRBackend] = {}
_layout_backends: dict[str, LayoutBackend] = {}
_vlm_backends: dict[str, VLMBackend] = {}
_region_extractors: dict[str, list[RegionExtractor]] = {}
_format_parsers: dict[str, FormatParser] = {}
_llm_backends: dict[str, LLMBackend] = {}
_embedders: dict[str, Embedder] = {}
_retrievers: dict[str, Retriever] = {}
_tts_backends: dict[str, TTSBackend] = {}
_exporters: dict[str, Exporter] = {}
_sensitive_detectors: dict[str, SensitiveDetector] = {}
_redactors: dict[str, Redactor] = {}
_anomaly_rules: dict[str, AnomalyRule] = {}
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

def register_llm(backend: LLMBackend):
    _llm_backends[backend.name] = backend

def register_embedder(backend: Embedder):
    _embedders[backend.name] = backend

def register_retriever(backend: Retriever):
    _retrievers[backend.name] = backend

def register_tts(backend: TTSBackend):
    _tts_backends[backend.name] = backend

def register_exporter(exporter: Exporter):
    _exporters[exporter.name] = exporter

def register_sensitive_detector(detector: SensitiveDetector):
    _sensitive_detectors[detector.name] = detector

def register_redactor(redactor: Redactor):
    _redactors[redactor.name] = redactor

def register_anomaly_rule(rule: AnomalyRule):
    _anomaly_rules[rule.name] = rule

def get_ocr_backend(name: str) -> Optional[OCRBackend]:
    return _ocr_backends.get(name)

def get_layout_backend(name: str) -> Optional[LayoutBackend]:
    if name in _layout_backends:
        return _layout_backends[name]
    if name in ["heuristic", "rule_based"]:
        return _layout_backends.get("heuristic") or _layout_backends.get("rule_based")
    for k, v in _layout_backends.items():
        if k != "stub_layout":
            return v
    return _layout_backends.get("stub_layout")

def get_vlm_backend(name: str) -> Optional[VLMBackend]:
    return _vlm_backends.get(name)

def get_region_extractors(label: str) -> list[RegionExtractor]:
    return _region_extractors.get(label, [])

def get_format_parser(name: str) -> Optional[FormatParser]:
    return _format_parsers.get(name)

def get_llm_backend(name: str) -> Optional[LLMBackend]:
    return _llm_backends.get(name)

def get_embedder(name: str) -> Optional[Embedder]:
    return _embedders.get(name)

def get_retriever(name: str) -> Optional[Retriever]:
    return _retrievers.get(name)

def get_tts_backend(name: str) -> Optional[TTSBackend]:
    return _tts_backends.get(name)

def get_exporter(name: str) -> Optional[Exporter]:
    return _exporters.get(name)

def get_sensitive_detector(name: str) -> Optional[SensitiveDetector]:
    return _sensitive_detectors.get(name)

def get_redactor(name: str) -> Optional[Redactor]:
    return _redactors.get(name)

def get_anomaly_rules() -> list[AnomalyRule]:
    return list(_anomaly_rules.values())
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
