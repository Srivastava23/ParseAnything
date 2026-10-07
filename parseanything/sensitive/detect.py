import os
from typing import List, Any
from parseanything.interfaces import SensitiveDetector
from parseanything.registry import register_sensitive_detector

class PresidioDetector(SensitiveDetector):
    name = "presidio"

    def __init__(self):
        # We will lazy-initialize to save time if not used
        self.analyzer = None

    def _init_analyzer(self):
        if self.analyzer is not None:
            return
            
        from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
        self.analyzer = AnalyzerEngine()
        
        # Add custom patterns
        # 1. PAN Card
        pan_pattern = Pattern(name="PAN", regex=r"[A-Z]{5}[0-9]{4}[A-Z]{1}", score=0.85)
        pan_rec = PatternRecognizer(supported_entity="IN_PAN", patterns=[pan_pattern])
        self.analyzer.registry.add_recognizer(pan_rec)
        
        # 2. Aadhaar
        aadhaar_pattern = Pattern(name="Aadhaar", regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", score=0.85)
        aadhaar_rec = PatternRecognizer(supported_entity="IN_AADHAAR", patterns=[aadhaar_pattern])
        self.analyzer.registry.add_recognizer(aadhaar_rec)
        
        # 3. IFSC
        ifsc_pattern = Pattern(name="IFSC", regex=r"^[A-Z]{4}0[A-Z0-9]{6}$", score=0.85)
        ifsc_rec = PatternRecognizer(supported_entity="IN_IFSC", patterns=[ifsc_pattern])
        self.analyzer.registry.add_recognizer(ifsc_rec)
        
    def detect(self, text: str) -> List[Any]:
        try:
            self._init_analyzer()
        except Exception:
            return []
            
        if not text.strip():
            return []
            
        try:
            results = self.analyzer.analyze(text=text, entities=[], language='en')
            findings = []
            for r in results:
                findings.append({
                    "type": r.entity_type,
                    "start": r.start,
                    "end": r.end,
                    "confidence": r.score
                })
            return findings
        except Exception:
            return []

class RegexDetector(SensitiveDetector):
    name = "regex_fallback"
    
    def __init__(self):
        import re
        self.patterns = {
            "IN_PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
            "IN_AADHAAR": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "IN_IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
            "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
        }
        
    def detect(self, text: str) -> List[Any]:
        findings = []
        if not text.strip(): return findings
        for entity_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                findings.append({
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.85
                })
        return findings

# We register an instance automatically
register_sensitive_detector(PresidioDetector())
register_sensitive_detector(RegexDetector())
