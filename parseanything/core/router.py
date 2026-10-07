from typing import Any
import os
import tempfile
from parseanything.schema import Document
from parseanything.registry import get_format_parser
from parseanything.errors import ErrorCode, ParseError, ParseException
from parseanything.core.orchestrator import process_paged_document

def route(format_name: str, path_or_bytes: Any, options: Any) -> Document:
    path = path_or_bytes
    is_temp = False
    if isinstance(path_or_bytes, bytes):
        fd, path = tempfile.mkstemp(suffix=f".{format_name}")
        with os.fdopen(fd, "wb") as f:
            f.write(path_or_bytes)
        is_temp = True
        
    try:
        if format_name in ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp", "image"]:
            return process_paged_document(path, format_name, options)
        
        parser = get_format_parser(format_name)
        if not parser:
            raise ParseException(ParseError(code=ErrorCode.UNSUPPORTED_FORMAT, message=f"No parser available for format: {format_name}"))
        
        return parser.parse(path, options)
    finally:
        if is_temp:
            os.remove(path)
