from parseanything.schema import Document, Anomaly
from parseanything.registry import get_anomaly_rules

def run_all_rules(doc: Document) -> list[Anomaly]:
    all_anomalies = []
    rules = get_anomaly_rules()
    for rule in rules:
        try:
            anomalies = rule.evaluate(doc)
            all_anomalies.extend(anomalies)
        except Exception:
            pass
            
    if "anomalies" not in doc.analysis:
        doc.analysis["anomalies"] = []
    doc.analysis["anomalies"].extend([a.model_dump() for a in all_anomalies])
        
    return all_anomalies
