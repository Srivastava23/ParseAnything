import requests
import json
from parseanything import parse
from parseanything.config import Options
doc = parse("test.csv", options=Options())
res = requests.post("http://127.0.0.1:8000/search-document", json={"doc": doc.model_dump(), "query": "Sebastiano"})
print(res.text)
