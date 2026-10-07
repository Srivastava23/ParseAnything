import os
import yaml
from parseanything.schema import Document

class DomainClassifier:
    def __init__(self, profiles_dir: str = None):
        if not profiles_dir:
            profiles_dir = os.path.join(os.path.dirname(__file__), "profiles")
        self.profiles = {}
        for fname in os.listdir(profiles_dir):
            if fname.endswith(".yaml"):
                with open(os.path.join(profiles_dir, fname), "r") as f:
                    data = yaml.safe_load(f)
                    self.profiles[data["name"]] = data
                    
    def classify(self, doc: Document) -> str:
        text_snippets = []
        for page in doc.pages[:3]:
            for block in page.blocks:
                if block.type in ["paragraph", "heading"]:
                    text_snippets.append(block.content.lower())
        
        full_text = " ".join(text_snippets)
        if not full_text.strip():
            return "general"
            
        from parseanything.registry import get_llm_backend
        from pydantic import BaseModel
        
        class ClassificationResponse(BaseModel):
            domain: str
            
        llm = get_llm_backend("ollama")
        if not llm:
            return "general"
            
        available_domains = [name for name in self.profiles.keys() if name != "general"]
        prompt = f"Analyze the following document text and classify its domain into exactly one of these categories: {available_domains}. If it does not strongly fit any of these, return 'general'. Output JSON with a 'domain' key.\n\nText:\n{full_text[:3000]}"
        
        try:
            res = llm.generate_json(prompt, ClassificationResponse)
            detected = res.domain.lower()
            if detected in self.profiles:
                return detected
            return "general"
        except Exception:
            return "general"
