# Handoff: Agent 1

## Status
- **Phase 0** is live. `schema.py`, `interfaces.py`, `registry.py`, `errors.py`, `config.py`, and `__init__.py` (with stub backends) have been committed to main.
- Contract finalized per instructions.

## What works
- `parseanything.parse(path)` returns a valid empty Document.
- Base types are available for import.
- Stub backends (`StubOCR`, `StubLayout`, `StubVLM`) are registered.

## Known Gaps
- Actual API, Orchestrator, Router, etc. are not yet implemented (scheduled for Phase 1).
