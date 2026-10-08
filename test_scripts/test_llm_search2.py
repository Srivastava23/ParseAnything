import requests
from parseanything import parse
from parseanything.config import Options
doc = parse("test2.csv", options=Options())
res = requests.post("http://127.0.0.1:8000/search-document", json={"doc": doc.model_dump(), "query": "Sebastiano"})
print(res.text)
