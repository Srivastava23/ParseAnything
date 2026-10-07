# Handoff: Agent 1 (Phase 0 Complete)

## 1. DONE
- **Bug Fix**: Fixed `ImportError` for `Region` by correctly importing it from `parseanything.interfaces` instead of `schema` inside `parseanything/pdf/layout.py`, `text_blocks.py`, and `classify.py`.
- **Smoke Test**: Added `tests/test_imports.py` to recursively import all modules. Proven by `python -m pytest tests/test_imports.py` which passes cleanly.
- **Additive Schema**: 
  - Added `SCHEMA_VERSION = "1.0.0"`.
  - Added `Block.id` (stable deterministic hash).
  - Added `Provenance` class and attached `Block.provenance`.
  - Added `Document.analysis` dictionary.
  - Assigned IDs deterministically inside `parseanything/core/assemble.py` based on `doc.source + page + bbox + type`.
- **Protocols & Registry**: Published `LLMBackend`, `Embedder`, `Retriever`, `TTSBackend`, `Exporter`, `SensitiveDetector`, `Redactor`, and `AnomalyRule` in `parseanything/interfaces.py`. Created corresponding registries in `parseanything/registry.py`.
- **Initialization**: Wrapped module imports in `try/except ImportError: pass` in `parseanything/__init__.py`.
- **Configuration**: Set up `config.yaml` skeleton and refactored `parseanything/config.py` to use `pydantic-settings`.
- **Dependencies**: Added optional extras (`[project.optional-dependencies]`) in `pyproject.toml` for layout, llm, retrieval, tts, and sensitive.

## 2. NOT DONE / KNOWN ISSUES
- Phase 1 (Layout Upgrade) and Phase 10 (FastAPI/CLI) are untouched. They will be completed during my next shift.
- The `try/except` in `__init__.py` dynamically catches imports, but if `parseanything.formats.pptx` depends on `python-pptx`, the missing dependency will fail gracefully without crashing the whole application, as per the contract.

## 3. HOW TO USE
- To test the current build, run:
  ```bash
  pip install -e .
  python -m pytest tests/test_imports.py
  ```
- To configure, edit `config.yaml` at the root directory. Options are loaded automatically using `pydantic-settings`.
- Agents can install their specific dependencies via extras: `pip install -e .[llm,retrieval,tts,sensitive]`.

## 4. FOR THE NEXT AGENT (AGENTS 2, 3, 4)
The Phase 0 contract is now live and pushed to `main`.
- **Agent 2**: You can begin Phase 2 (LLM, Retrieval, Citations, Domain). Use the `LLMBackend`, `Embedder`, and `Retriever` protocols defined in `interfaces.py`. Add your settings to the `[llm]` and `[retrieval]` blocks in `config.yaml`.
- **Agent 3**: You can begin Phase 4 and 9 (Privacy, Export, TTS). Implement `SensitiveDetector`, `Redactor`, `Exporter`, and `TTSBackend`. Add settings under the `[tts]` and `[redaction]` blocks.
- **Agent 4**: You can begin Phase 5 and 7 (Anomaly detection, Charts). Implement `AnomalyRule` protocols. Wait for Agent 2 to finish retrieval before doing Phase 8.2 (Predictive questions).
**Note**: Build against the interfaces in `interfaces.py` and register your classes in `registry.py` (e.g., `register_llm`).

## 5. Message to Human
Agent 1 here! I have successfully completed Phase 0. The import bug has been resolved, all new protocol interfaces have been established, and the `pydantic-settings` schema is live alongside `config.yaml`. The core schema has been additively updated with deterministic `Block.id`s, `Provenance`, and an `analysis` dict. The code has been tested and pushed to the `main` branch. 

**Unresolved REQUESTS.md**: None so far.

The Phase 0 contract is live. Let me know when you'd like me to start Phase 1.
