from typing import Any, Optional
from parseanything.schema import Document
from parseanything.config import Options

def _do_parse(path_or_bytes: Any, options: Options, extension_hint: str = "") -> Document:
    from parseanything.core.sniff import sniff_format
    from parseanything.core.router import route
    
    format_name = sniff_format(path_or_bytes, extension_hint)
    return route(format_name, path_or_bytes, options)

def parse(path_or_bytes: Any, options: Optional[Options] = None, extension_hint: str = "") -> Document:
    from parseanything.core.watchdog import watchdog_wrapper
    if options is None:
        options = Options()
    
    return watchdog_wrapper(_do_parse, args=(path_or_bytes, options, extension_hint), kwargs={}, timeout_seconds=55)
