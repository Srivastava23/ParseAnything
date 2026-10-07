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
        raise exc[0]
    return result[0]
