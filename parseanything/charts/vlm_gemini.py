import os
from parseanything.schema import ChartData, Series, Point
from parseanything.registry import register_vlm

class GeminiVLMBackend:
    name = "vlm_gemini"
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.enabled = os.environ.get("ENABLE_GEMINI_VLM", "0") == "1"
        
    def describe_chart(self, image) -> ChartData:
        if not self.enabled or not self.api_key:
            return None
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = "Describe this chart in JSON. Include chart_type, title, x_label, y_label, series (list of {name, points: [{x, y}]}), caption, data_table_markdown."
            response = model.generate_content([prompt, image])
            
            import json
            text = response.text
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            parsed = json.loads(text.strip())
            
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

backend = GeminiVLMBackend()
register_vlm(backend)
