# ParseAnything

**ParseAnything** is a high-fidelity universal document ingestion engine designed for extracting structure from PDFs (digital and scanned), images, DOCX, XLSX, PPTX, legacy Office files, and emails. It produces clean **JSON + Markdown** while maintaining reading order, tabular structures, and domain awareness.

## 🔥 Implemented Features

The engine supports a fully automated document ingestion pipeline with the following capabilities:

1. **Modern Dual-Theme UI:** A sleek, responsive web interface in both dark mode and light mode, accessible via the root (`/`) endpoint.
2. **Local LLM Integration:** Powered by Ollama (`llama3`) for document Q&A, automatic summarization, and jargon simplification.
3. **Interactive Chat & Suggested Questions:** Automatically generates contextual questions based on the uploaded document. Unified chat experience allows users to ask custom questions or click suggested ones seamlessly.
4. **Automated Simplification & TTS:** Instantly simplifies document language, cleans up LLM preambles, and generates local Text-to-Speech (TTS) audio.
5. **Typed Semantic Blocks:** Extracts headings, paragraphs, lists, tables, figures, charts, and equations.
6. **Complex Tables & Excel Export:** Reconstructs merged cells and multi-row headers. Instantly download extracted tables as Excel workbooks.
7. **PII Redaction:** Detects and pseudonyms/masks Sensitive Data (PAN, Aadhaar, etc.) directly in the structured JSON and Markdown.
8. **Intelligent LLM Domain Classification:** Automatically analyzes text to detect domains (Engineering, Financial, Legal) using LLM reasoning instead of basic keywords.
9. **Advanced Engineering Mode:** When an engineering document is detected, the UI instantly generates an interactive dashboard featuring a Mermaid.js Dependency Map, Architecture Components, API/Database Extraction, Incident/RCA Timelines, and Impact Analysis.
10. **Anomaly Detection:** Flags mathematical inconsistencies in tables, missing pages, and low OCR confidence scores.

## 📂 Project Architecture

The codebase follows a highly modular, decoupled architecture where each concern (parsing, routing, exporting, inference) is independently scalable.

```
ParseAnything/
│
├── parseanything/          # Main application package
│   ├── api/                # FastAPI server, routing, endpoints
│   ├── cli/                # Command Line Interface tools
│   ├── core/               # Orchestrator, parsing pipeline, file type routing
│   ├── formats/            # Individual parsers (PDF, DOCX, XLSX, CSV, PPTX, Email, etc.)
│   ├── exporters/          # Data exporters (e.g., XLSX export of tables)
│   ├── anomalies/          # Rules engine for detecting math/logic anomalies
│   ├── retrieval/          # Local vector store and RAG Q&A implementation
│   ├── sensitive/          # PII detection and redaction module
│   ├── llm/                # Local LLM integration (Ollama backend)
│   ├── domains/            # Domain classification and intelligent extraction profiles
│   ├── imageparse/         # Image pre-processing and metadata extraction
│   ├── ocr/                # Optical Character Recognition logic
│   ├── math/               # Math/equation extraction engine
│   ├── pdf/                # PDF specific structure extraction 
│   ├── tables/             # Table structure inference
│   └── tts/                # Local Text-to-Speech service integration
│
├── ui/                     # Frontend UI assets (HTML, CSS, JS)
│
├── docs/                   # Documentation and project plans
├── scripts/                # Helper scripts
├── tests/                  # Unit and integration tests
├── test_outputs/           # Output directory for test runs and exports
└── test_scripts/           # Sandbox and QA testing scripts
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Srivastava23/ParseAnything.git
cd ParseAnything

# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install .
pip install pyttsx3 # Required for local TTS
```

### 2. Running the API

Start the backend API server. The UI is automatically served by the API.

```bash
python parseanything/cli/main.py serve --port 8000
```
Open `http://127.0.0.1:8000/` in your browser to access the interface!

### 3. Running Local LLM (Ollama)

To use the intelligent chat, domain classification, and summarization features, you need to run Ollama locally:

```bash
# Ensure Ollama is installed on your machine
ollama serve
ollama pull llama3
```

## 🧠 Design Philosophy

ParseAnything avoids a monolithic parser design. Instead, the `core/orchestrator.py` intelligently inspects incoming files and routes them to dedicated specialized parsers in `formats/`. The parsed output is then sent through a sequence of post-processors (PII Redaction, Anomaly Detection, Domain Extraction) before being finalized into a universal `Document` schema (`schema.py`).
