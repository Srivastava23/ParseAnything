import re
from parseanything.schema import Document, Anomaly, BlockType
from parseanything.interfaces import AnomalyRule
from parseanything.registry import register_anomaly_rule

class TableMathRule(AnomalyRule):
    name = "table_math"
    
    def _extract_number(self, text: str):
        text = re.sub(r'[^\d.-]', '', text)
        if not text or text == "-" or text == ".": return None
        try:
            return float(text)
        except ValueError:
            return None

    def evaluate(self, doc: Document) -> list[Anomaly]:
        anomalies = []
        for page in doc.pages:
            for block in page.blocks:
                if block.type == BlockType.TABLE and block.table:
                    rows = {}
                    for cell in block.table.cells:
                        rows.setdefault(cell.row, []).append(cell)
                    
                    if not rows: continue
                    max_row = max(rows.keys())
                    last_row_cells = rows[max_row]
                    
                    is_total = any("total" in c.text.lower() for c in last_row_cells)
                    if is_total and max_row > 0:
                        col_sums = {}
                        for r in range(max_row):
                            if r in rows:
                                for c in rows[r]:
                                    num = self._extract_number(c.text)
                                    if num is not None:
                                        col_sums[c.col] = col_sums.get(c.col, 0) + num
                        
                        for c in last_row_cells:
                            total_num = self._extract_number(c.text)
                            if total_num is not None and c.col in col_sums:
                                calculated = col_sums[c.col]
                                if abs(total_num - calculated) > 1.0: # tolerate small rounding
                                    anomalies.append(Anomaly(
                                        rule=self.name,
                                        severity="high",
                                        explanation=f"Table Math Mismatch: Column {c.col} sums to {calculated} but total row specifies {total_num}.",
                                        block_ids=[block.id]
                                    ))
        return anomalies

class MissingPageRule(AnomalyRule):
    name = "missing_page"
    
    def evaluate(self, doc: Document) -> list[Anomaly]:
        anomalies = []
        expected = 1
        for page in sorted(doc.pages, key=lambda p: p.number):
            if page.number != expected:
                anomalies.append(Anomaly(
                    rule=self.name,
                    severity="high",
                    explanation=f"Missing page(s). Expected {expected}, got {page.number}.",
                    block_ids=[]
                ))
                expected = page.number + 1
            else:
                expected += 1
        return anomalies

class ConfidenceRule(AnomalyRule):
    name = "confidence_check"
    
    def evaluate(self, doc: Document) -> list[Anomaly]:
        anomalies = []
        for page in doc.pages:
            for block in page.blocks:
                if block.confidence < 0.6:
                    anomalies.append(Anomaly(
                        rule=self.name,
                        severity="medium",
                        explanation=f"Low extraction confidence ({block.confidence:.2f}).",
                        block_ids=[block.id]
                    ))
        return anomalies

register_anomaly_rule(TableMathRule())
register_anomaly_rule(MissingPageRule())
register_anomaly_rule(ConfidenceRule())
