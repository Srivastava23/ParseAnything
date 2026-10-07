from parseanything.schema import Block
from typing import Optional

def combine(ocr_conf: Optional[float] = None, layout_score: Optional[float] = None, heuristics: float = 1.0) -> float:
    """
    Combines OCR confidence, layout score, and heuristics to produce a final confidence score.
    Formula:
    - If ocr_conf is missing, assume 1.0.
    - If layout_score is missing, assume 1.0.
    - Result = (ocr_conf * layout_score * heuristics)
    """
    conf = 1.0
    if ocr_conf is not None:
        conf *= ocr_conf
    if layout_score is not None:
        conf *= layout_score
    conf *= heuristics
    return max(0.0, min(1.0, conf))

def apply_flagging(block: Block, threshold: float):
    if block.confidence < threshold:
        block.flagged = True
        if not block.flag_reason:
            block.flag_reason = f"Confidence {block.confidence:.2f} < threshold {threshold}"
