from typing import Any, Optional
from parseanything.schema import Document
from parseanything.config import Options

# Import backends and extractors to register them
import parseanything.ocr.rapidocr_backend
import parseanything.ocr.tesseract_backend
import parseanything.pdf.layout
import parseanything.pdf.text_blocks
import parseanything.tables.extract
import parseanything.charts.extract
import parseanything.math.extract
import parseanything.formats.docx
import parseanything.formats.xlsx
import parseanything.formats.misc
def _do_parse(path_or_bytes: Any, options: Options, extension_hint: str = "") -> Document:
    from parseanything.core.sniff import sniff_format
    from parseanything.core.router import route
    from parseanything.errors import ParseException
    
    try:
        format_name = sniff_format(path_or_bytes, extension_hint)
        doc = route(format_name, path_or_bytes, options)
        
        cost = 0.0
        if options.enable_cloud_fallbacks:
            if options.ocr_backend and options.ocr_backend != "stub_ocr" and doc.stats.pages > 0:
                cost += doc.stats.pages * options.ocr_cost_per_page
            if options.vlm_backend and options.vlm_backend != "stub_vlm" and doc.stats.pages > 0:
                cost += doc.stats.pages * options.vlm_cost_per_page
        doc.stats.est_cost_usd = cost
        return doc
    except ParseException as e:
        source_name = path_or_bytes if isinstance(path_or_bytes, str) else "bytes"
        from parseanything.schema import DocStats
        doc = Document(source=source_name, format="unknown", stats=DocStats())
        doc.errors.append(e.parse_error)
        return doc

def parse(path_or_bytes: Any, options: Optional[Options] = None, extension_hint: str = "") -> Document:
    from parseanything.core.watchdog import watchdog_wrapper
    if options is None:
        options = Options()
    
    return watchdog_wrapper(_do_parse, args=(path_or_bytes, options, extension_hint), kwargs={}, timeout_seconds=55)
