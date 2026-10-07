# ParseAnything: Remaining Features Implementation Plan

This document outlines the detailed, step-by-step implementation plan for the remaining incomplete phases (4, 5, 6, 8, 9, 10).

## Phase 4: Sensitive Data Detection and Redaction
**Goal:** Detect PII/secrets in extracted text/tables and redact them safely in JSON, Markdown, and exported files.

### Steps:
1. **Interfaces & Registry Update (`parseanything/interfaces.py`, `registry.py`)**:
   - Ensure `SensitiveDetector` and `Redactor` protocols are defined.
   - Add `register_sensitive_detector` and `register_redactor` to `registry.py`.
2. **Detection Plugin (`parseanything/sensitive/detect.py`)**:
   - Implement `PresidioDetector` wrapping `presidio-analyzer` and `spaCy` (`en_core_web_sm`).
   - Add custom regex recognizers for Indian contexts (Aadhaar, PAN, IFSC) and secrets.
   - Output a list of `Finding` objects (type, block_id, span, bbox, confidence).
3. **Redaction Plugin (`parseanything/sensitive/redact.py`)**:
   - Implement `TextRedactor` which takes `Findings` and applies modes (`mask`, `pseudonym`, `remove`) to `Block.content`.
   - Update `Document.analysis["sensitive"]` with metadata of what was redacted.
4. **API Integration (`parseanything/api/server.py`)**:
   - Implement `POST /redact` which accepts a parsed `Document` JSON and redaction options, applies the `Redactor`, and returns the redacted `Document`.
5. **UI Update (`ui/index.html`)**:
   - Add a toggle for "Redact PII". When enabled, chain the `/parse` response through `/redact` before rendering.

## Phase 5: Anomaly Detection
**Goal:** Run deterministic rules over extracted tables/text to find inconsistencies (e.g., math errors in tables).

### Steps:
1. **Interfaces (`parseanything/interfaces.py`, `registry.py`)**:
   - Define `AnomalyRule` protocol with a `check(doc: Document) -> list[Anomaly]` method.
2. **Rule Implementations (`parseanything/anomalies/rules.py`)**:
   - `TableMathRule`: Checks rows/cols for summations. If `TableData` has a row "Total" but the sum doesn't match, flag it.
   - `MissingPageRule`: Checks if `Page.number` sequence is broken.
   - `ConfidenceRule`: Flags blocks with `score < 0.6`.
3. **Engine (`parseanything/anomalies/engine.py`)**:
   - Implement `run_all_rules(doc: Document)` that iterates all registered rules and aggregates results into `doc.analysis["anomalies"]`.
4. **API Integration (`parseanything/api/server.py`)**:
   - Implement `POST /anomalies` which accepts a `Document` and runs the engine.

## Phase 6: Domain Modes
**Goal:** Apply specific schemas and extraction prompts based on the document's domain (e.g., Legal, Financial).

### Steps:
1. **Profiles Directory (`parseanything/domains/profiles/`)**:
   - Create `financial.yaml`, `legal.yaml`, `general.yaml`.
   - Define keyword signals (e.g., "EBITDA", "Plaintiff") and expected extraction JSON schemas.
2. **Classifier (`parseanything/domains/classifier.py`)**:
   - Implement `DomainClassifier` that scans the first 5 pages of blocks against profile keywords to auto-detect the domain.
3. **Extractor (`parseanything/domains/extractor.py`)**:
   - Use `LLMBackend` with `generate_json` constrained to the detected profile's schema.
   - Append results to `Document.analysis["domain"]`.
4. **API Integration**:
   - Add `domain` override parameter to `/parse` `Options`. If set, automatically run the domain extractor during assembly.

## Phase 8: Productivity (Excel, Simplify, Next Questions)
**Goal:** Add QoL features for end-users interacting with the parsed document.

### Steps:
1. **Excel Exporter (`parseanything/exporters/xlsx.py`)**:
   - Implement `register_exporter("xlsx")`.
   - Use `openpyxl`. Create a sheet for each `TableData` in the document.
   - Preserve headers and create a "Sources" sheet linking table names to `page` and `bbox`.
2. **Next Questions (`parseanything/retrieval/questions.py`)**:
   - Implement `generate_next_questions(doc)`.
   - Use `LLMBackend` to read `doc.analysis["domain"]` and `doc.analysis["chart_insights"]` to propose 5 relevant follow-up questions.
3. **Simplify Mode (`parseanything/llm/simplify.py`)**:
   - Implement a function that takes a specific `block_id`, sends its text to the LLM with a "Plain English" prompt, and returns the simplified text.
4. **API Integration (`parseanything/api/server.py`)**:
   - Implement `POST /export/xlsx` returning a streaming file response.
   - Implement `POST /simplify` and `POST /next-questions`.

## Phase 9: Text-to-Speech (TTS)
**Goal:** Convert parsed document content (skipping noise/tables) into audio.

### Steps:
1. **Interfaces (`parseanything/interfaces.py`, `registry.py`)**:
   - Define `TTSBackend` with `synthesize(text) -> bytes`.
2. **TTS Backend (`parseanything/tts/kokoro.py`)**:
   - Implement `KokoroTTS` using the `kokoro` package or `pyttsx3` as a local offline fallback.
   - Add logic to chunk `Document` text (filtering out tables/charts) into sentences.
3. **API Integration (`parseanything/api/server.py`)**:
   - Implement `POST /tts` returning a streaming `.wav` or `.mp3` audio response.

## Phase 10: Final UI Polish
**Goal:** Wire the new API endpoints into the Streamlit/HTML UI.

### Steps:
1. **UI (`ui/index.html` or `ui/app.py`)**:
   - Add a "Download as Excel" button mapping to `/export/xlsx`.
   - Add an "Anomalies" tab that fetches and displays the anomalies array.
   - Add an audio player `<audio>` tag that fetches from `/tts`.
   - Under the Q&A section, display the suggestions from `/next-questions` as clickable chips.
