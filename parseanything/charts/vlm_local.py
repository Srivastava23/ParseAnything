import os
import requests
from parseanything.schema import ChartData, Series, Point
from parseanything.registry import register_vlm

class LocalVLMBackend:
    name = "vlm_local"
    
    def __init__(self):
        self.url = os.environ.get("VLM_LOCAL_URL", "http://localhost:11434/api/generate")
        
    def describe_chart(self, image) -> ChartData:
        # Convert PIL image to base64
        import base64
        from io import BytesIO
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        prompt = "Describe this chart in JSON. Include chart_type, title, x_label, y_label, series (list of {name, points: [{x, y}]}), caption, data_table_markdown."
        
        try:
            resp = requests.post(self.url, json={
                "model": "qwen2.5-vl-7b",
                "prompt": prompt,
                "images": [img_str],
                "stream": False,
                "format": "json"
            }, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("response", "{}")
            import json
            parsed = json.loads(data)
            
            # Reconstruct ChartData
            series = []
            for s in parsed.get("series", []):
                points = [Point(x=p.get("x", ""), y=float(p.get("y", 0))) for p in s.get("points", [])]
                series.append(Series(name=s.get("name", ""), points=points))
                
            return ChartData(
                chart_type=parsed.get("chart_type", "unknown"),
                title=parsed.get("title"),
                x_label=parsed.get("x_label"),
                y_label=parsed.get("y_label"),
                series=series,
                data_table_markdown=parsed.get("data_table_markdown"),
                caption=parsed.get("caption"),
                values_estimated=True
            )
        except Exception:
            return None

backend = LocalVLMBackend()
register_vlm(backend)
