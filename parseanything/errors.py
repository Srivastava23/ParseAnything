from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ErrorCode(str, Enum):
    CORRUPT_FILE = "CORRUPT_FILE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    PASSWORD_PROTECTED = "PASSWORD_PROTECTED"
    EMPTY_FILE = "EMPTY_FILE"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    EXTRACTOR_FAILED = "EXTRACTOR_FAILED"  # partial failure, recoverable
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ParseError(BaseModel):
    code: ErrorCode
    message: str
    stage: Optional[str] = None
    page: Optional[int] = None
    recoverable: bool = False

class ParseException(Exception):
    def __init__(self, parse_error: ParseError):
        self.parse_error = parse_error
        super().__init__(parse_error.message)
