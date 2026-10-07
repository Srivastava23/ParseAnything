from typing import Any
from parseanything.schema import Document, SensitiveFinding
from parseanything.interfaces import Redactor
from parseanything.registry import get_sensitive_detector, register_redactor

class PipelineRedactor(Redactor):
    name = "pipeline"
    
    def __init__(self, mode="pseudonym"):
        self.mode = mode
        
    def redact(self, doc: Document, findings: list[Any]) -> Document:
        presidio = get_sensitive_detector("presidio")
        regex_fallback = get_sensitive_detector("regex_fallback")
            
        all_findings = []
        for page in doc.pages:
            for block in page.blocks:
                block_findings_raw = []
                if presidio:
                    block_findings_raw.extend(presidio.detect(block.content))
                
                # Always combine or fallback
                if not block_findings_raw and regex_fallback:
                    block_findings_raw.extend(regex_fallback.detect(block.content))
                    
                block_findings = []
                for bf in block_findings_raw:
                    finding_obj = SensitiveFinding(
                        type=bf["type"],
                        block_id=block.id,
                        start=bf["start"],
                        end=bf["end"],
                        confidence=bf["confidence"]
                    )
                    block_findings.append(finding_obj)
                    all_findings.append(finding_obj)
                    
                # Redact block.content
                if block_findings:
                    # Sort descending by start index to avoid shifting issues when replacing
                    block_findings.sort(key=lambda x: x.start, reverse=True)
                    text = block.content
                    for f in block_findings:
                        if self.mode == "pseudonym":
                            mask = f"[{f.type}]"
                        else:
                            mask = "*" * (f.end - f.start)
                            
                        orig_text = text[f.start:f.end]
                        text = text[:f.start] + mask + text[f.end:]
                        
                        # Also replace in table cells and raw text if applicable
                        if block.table:
                            if block.table.cells:
                                for cell in block.table.cells:
                                    if orig_text in cell.text:
                                        cell.text = cell.text.replace(orig_text, mask)
                            if block.table.markdown and orig_text in block.table.markdown:
                                block.table.markdown = block.table.markdown.replace(orig_text, mask)
                            if block.table.html and orig_text in block.table.html:
                                block.table.html = block.table.html.replace(orig_text, mask)
                                    
                    block.content = text
        
        # We store the findings inside the document analysis dictionary
        if "sensitive" not in doc.analysis:
            doc.analysis["sensitive"] = []
        doc.analysis["sensitive"].extend([f.model_dump() for f in all_findings])
        return doc

register_redactor(PipelineRedactor(mode="pseudonym"))
