import json
from typing import Any
from parseanything.interfaces import LLMBackend
from parseanything.config import Options

class OllamaLLMBackend(LLMBackend):
    name = "ollama"

    def __init__(self, opts: Options):
        self.model = opts.llm.model
        self.base_url = opts.llm.base_url or "http://localhost:11434"
        try:
            import ollama
            self.client = ollama.Client(host=self.base_url)
            self._has_pkg = True
        except ImportError:
            self._has_pkg = False

    def generate(self, prompt: str) -> str:
        if self._has_pkg:
            res = self.client.generate(model=self.model, prompt=prompt)
            return res['response']
        else:
            import urllib.request
            import urllib.error
            data = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req) as response:
                    res = json.loads(response.read().decode())
                    return res.get("response", "")
            except Exception as e:
                return f"Error: {str(e)}"

    def generate_json(self, prompt: str, schema: Any) -> Any:
        if self._has_pkg:
            res = self.client.generate(model=self.model, prompt=prompt, format=schema.model_json_schema())
            return schema.model_validate_json(res['response'])
        else:
            import urllib.request
            data = json.dumps({
                "model": self.model, 
                "prompt": prompt, 
                "stream": False,
                "format": schema.model_json_schema()
            }).encode("utf-8")
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode())
                return schema.model_validate_json(res.get("response", "{}"))

class OpenAILLMBackend(LLMBackend):
    name = "openai"

    def __init__(self, opts: Options):
        self.model = opts.llm.model
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=opts.llm.api_key, base_url=opts.llm.base_url)
            self._has_pkg = True
        except ImportError:
            self._has_pkg = False

    def generate(self, prompt: str) -> str:
        if not self._has_pkg:
            return "Error: openai package not installed"
        res = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content or ""

    def generate_json(self, prompt: str, schema: Any) -> Any:
        if not self._has_pkg:
            raise ImportError("openai package not installed")
        res = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema
        )
        return res.choices[0].message.parsed
