import threading
from parseanything.errors import ErrorCode, ParseError
from parseanything.schema import Document

def watchdog_wrapper(func, args, kwargs, timeout_seconds=55):
    result = []
    exc = []
    
    def target():
        try:
            result.append(func(*args, **kwargs))
        except Exception as e:
            exc.append(e)
            
    t = threading.Thread(target=target)
    t.start()
    t.join(timeout_seconds)
    
    if t.is_alive():
        doc = Document(source="unknown", format="unknown")
        doc.errors.append(ParseError(code=ErrorCode.TIMEOUT, message=f"Timeout after {timeout_seconds}s", recoverable=True))
        return doc
        
    if exc:
        source_name = "unknown"
        if args and len(args) > 0 and isinstance(args[0], (str, bytes)):
            source_name = args[0] if isinstance(args[0], str) else "bytes"
        doc = Document(source=source_name, format="unknown")
        err_msg = str(exc[0])
        code = ErrorCode.CORRUPT_FILE if ("format error" in err_msg.lower() or "pdfium" in err_msg.lower()) else ErrorCode.INTERNAL_ERROR
        doc.errors.append(ParseError(code=code, message=err_msg, stage="watchdog", recoverable=False))
        return doc
    return result[0]
