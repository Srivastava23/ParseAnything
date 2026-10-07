# Changelog

## [Unreleased]
### Added
- **Tables**
  - TableRegionExtractor with fallback grid/cell extraction and table structure models.
  - Cross-page table merging logic based on column structures and page boundaries.
  - Financial numbers validator for OCR hygiene.
- **Charts**
  - ChartRegionExtractor that queries local VLMs (`Qwen2.5-VL`) or Gemini to extract chart data.
  - Fallback OCR data extraction if VLMs are unavailable.
- **Math**
  - EquationRegionExtractor using `pix2tex` to convert image equations into LaTeX.
  - Fallback OCR strategy for math equations.
