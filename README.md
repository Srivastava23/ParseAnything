# ParseAnything

**ParseAnything** is a high-fidelity universal document ingestion engine designed for extracting structure from PDFs (digital and scanned), images, DOCX, XLSX, PPTX, legacy Office files, and emails. It produces clean **JSON + Markdown** while maintaining reading order, tabular structures, and domain awareness.

## 🔥 Implemented Features (DQCL Hackathon)

The engine now supports a fully automated document ingestion pipeline with the following capabilities:

1. **Typed Semantic Blocks:** Extracts headings, paragraphs, lists, tables, figures, charts, and equations.
2. **Reading Order & Layout:** Maintains correct reading order mapping across multi-column layouts, sidebars, footnotes, and headers/footers.
3. **Complex Tables & Excel Export:** Reconstructs merged cells, multi-row headers, and tables merged across page breaks. It includes a `POST /export/xlsx` endpoint to instantly download extracted tables as Excel workbooks.
4. **PII Redaction:** Detects and pseudonyms/masks Sensitive Data (PAN, Aadhaar, etc.) directly in the structured JSON and Markdown using `POST /redact`.
5. **Anomaly Detection:** Deterministic rules engine (`POST /anomalies`) flags mathematical inconsistencies in tables, missing pages, and low OCR confidence scores.
6. **Domain Classification:** Automatically identifies the document type (e.g., Financial, Legal, General) using keyword signals from YAML profiles to tailor extraction schemas.
7. **Local Text-to-Speech (TTS):** Generates playable audio files of the document's readable text using a local `pyttsx3` backend (`POST /tts`).
8. **Interactive Q&A & Fallbacks:** Generates suggested next questions (`POST /next-questions`) and retrieves answers directly from the document (`POST /answer`). 
   - *Zero-Hallucination Retriever:* Uses SQLite FTS5 (BM25 keyword search) to fetch the exact source text and citation `[B:id]` if the LLM is unavailable.

## 🛠 What's Left to Implement

While the core functionality is locked in, the following areas need attention:
- **Simplify Mode UI:** The `POST /simplify` endpoint is built, but it needs a button on individual blocks in the UI to let users simplify complex jargon into plain English.
- **VLM Chart Extraction:** The `stub_vlm` is currently a placeholder. Needs integration with LLaVA or Gemini Vision for reading data points out of bar/line charts.
- **LaTeX Math (`pix2tex`):** Needs to be fully wired into the block classification pipeline to convert image equations to LaTeX.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Srivastava23/ParseAnything.git
cd ParseAnything

# Install dependencies (requires a Python virtual environment)
pip install .
pip install pyttsx3 # Required for local TTS

# Run the API locally
uvicorn parseanything.api.server:app --host 127.0.0.1 --port 8000
```
Open `ui/index.html` via Live Server to access the interface!

---

## 🤖 Handover Prompt (For Developer with Local Ollama/Llama3)

Hey! The project is in a great state. The pipeline is fully integrated, the UI is looking slick, and the fallback systems (SQLite retriever, custom mock questions) are keeping things running smoothly even without an LLM. 

Since you have a local instance of Ollama running `llama3` on your laptop, your main focus should be stress-testing the actual LLM integration! 

**Here is your prompt to continue the work:**

> "I have a local instance of Ollama running `llama3` on port `11434`. Please help me do the following:
> 1. Disable the Hackathon Fallback mocks in `parseanything/retrieval/questions.py` and `parseanything/retrieval/answer.py` so that `OllamaLLMBackend` is directly queried for generating questions and answers.
> 2. Test the `POST /next-questions` and `POST /answer` endpoints using my running Llama 3 model. If Llama 3 hallucinates or struggles with the JSON schema, help me tweak the prompt templates in `answer.py`.
> 3. Implement the UI logic in `ui/index.html` to trigger the `POST /simplify` endpoint when a user hovers over a complex paragraph block in the 'Clean Markdown' tab.
> 4. If my machine can handle it, let's look into replacing `stub_vlm` with LLaVA via Ollama for chart extraction!"
