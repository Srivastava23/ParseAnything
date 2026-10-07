import os
import yaml
from parseanything.schema import Document
from parseanything.registry import get_llm_backend
from parseanything.render.markdown import to_markdown

def extract_domain_schema(doc: Document, domain_name: str) -> dict:
    llm = get_llm_backend("ollama")
    if not llm:
        return {}
        
    profiles_dir = os.path.join(os.path.dirname(__file__), "profiles")
    profile_path = os.path.join(profiles_dir, f"{domain_name}.yaml")
    
    if not os.path.exists(profile_path):
        return {}
        
    with open(profile_path, "r") as f:
        profile = yaml.safe_load(f)
        
    schema = profile.get("schema", {})
    if not schema:
        return {}
        
    text_content = to_markdown(doc)
    # Truncate to avoid context limits
    text_content = text_content[:15000] 
    
    prompt = f"Extract information from the following document strictly conforming to the requested schema.\n\nDocument:\n{text_content}"
    
    try:
        result = llm.generate_json(prompt, schema)
        return result
    except Exception as e:
        return {"error": str(e)}
