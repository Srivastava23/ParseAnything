from pydantic import BaseModel, Field

class Options(BaseModel):
    dpi: int = 200
    workers: int = 4
    confidence_threshold: float = 0.6
    ocr_backend: str = "rapidocr"
    layout_backend: str = "heuristic"
    vlm_backend: str = "stub_vlm"
    enable_cloud_fallbacks: bool = False
