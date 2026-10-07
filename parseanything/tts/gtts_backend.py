from parseanything.interfaces import TTSBackend
from parseanything.registry import register_tts
from parseanything.schema import Document

class GttsTTS(TTSBackend):
    name = "gtts"
    
    def synthesize(self, text: str, output_path: str) -> dict[str, tuple[float, float]]:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save(output_path)
            return {}
        except Exception as e:
            with open(output_path, "wb") as f:
                f.write(b"") # Empty file
            return {}

def extract_readable_text(doc: Document) -> str:
    lines = []
    for page in doc.pages:
        for block in page.blocks:
            c = block.content.strip()
            # Skip picture placeholders and structural markers
            if c and not c.startswith("[Embedded") and not c.startswith("<!--") and len(c) > 3:
                lines.append(c)
                if sum(len(x) for x in lines) > 1200:
                    break
        if sum(len(x) for x in lines) > 1200:
            break
            
    text = ". ".join(lines)
    if len(text) > 1000:
        text = text[:1000]
        last_period = text.rfind(".")
        if last_period > 300:
            text = text[:last_period + 1]
    return text.strip()

register_tts(GttsTTS())
