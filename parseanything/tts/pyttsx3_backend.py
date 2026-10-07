from parseanything.interfaces import TTSBackend
from parseanything.registry import register_tts
from parseanything.schema import Document
import os

class Pyttsx3TTS(TTSBackend):
    name = "pyttsx3"
    
    def synthesize(self, text: str, output_path: str) -> dict[str, tuple[float, float]]:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            return {}
        except ImportError:
            # Fallback or error
            with open(output_path, "wb") as f:
                f.write(b"") # Empty file
            return {}

def extract_readable_text(doc: Document) -> str:
    lines = []
    for page in doc.pages:
        for block in page.blocks:
            if block.type in ["paragraph", "heading", "list"]:
                if block.content.strip():
                    lines.append(block.content)
    return "\n\n".join(lines)

register_tts(Pyttsx3TTS())
