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
        # Extract text from first 5 pages
        text_snippets = []
        for page in doc.pages[:5]:
            for block in page.blocks:
                if block.type in ["paragraph", "heading"]:
                    text_snippets.append(block.content.lower())
        
        full_text = " ".join(text_snippets)
        if not full_text.strip():
            return "general"
            
        best_match = "general"
        max_score = 0
        
        for name, profile in self.profiles.items():
            if name == "general":
                continue
            keywords = profile.get("keywords", [])
            score = sum(1 for kw in keywords if kw.lower() in full_text)
            if score > max_score:
                max_score = score
                best_match = name
                
        return best_match
