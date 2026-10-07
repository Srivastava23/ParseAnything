import os
import zipfile

def sniff_format(path_or_bytes: str | bytes, extension_hint: str = "") -> str:
    """Detects file format by magic bytes or content heuristics."""
    if isinstance(path_or_bytes, str):
        if not os.path.exists(path_or_bytes):
            from parseanything.errors import ErrorCode, ParseError, ParseException
            raise ParseException(ParseError(code=ErrorCode.FILE_NOT_FOUND, message=f"File not found: {path_or_bytes}"))
        with open(path_or_bytes, "rb") as f:
            header = f.read(8192)
    else:
        header = path_or_bytes[:8192]

    # Handle empty files
    if not header:
        from parseanything.errors import ErrorCode, ParseError, ParseException
        raise ParseException(ParseError(code=ErrorCode.EMPTY_FILE, message="File is empty"))

    # Magic byte signatures
    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
        return "tiff"
    if header.startswith(b"BM"):
        return "bmp"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"

    if header.startswith(b"PK\x03\x04"):
        try:
            import io
            file_obj = path_or_bytes if isinstance(path_or_bytes, str) else io.BytesIO(path_or_bytes)
            with zipfile.ZipFile(file_obj, "r") as zf:
                namelist = zf.namelist()
                if "word/document.xml" in namelist:
                    return "docx"
                if "xl/workbook.xml" in namelist:
                    return "xlsx"
                if "ppt/presentation.xml" in namelist:
                    return "pptx"
        except zipfile.BadZipFile:
            pass
        return "zip"

    # OLE2 (legacy doc/xls/ppt or msg)
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        # We'd need something like olefile to inspect inside, but for now we fallback to extension
        ext = extension_hint.lower()
        if ext in [".doc", ".xls", ".ppt", ".msg"]:
            return ext.strip(".")
        return "ole2"

    # EML (RFC 822) heuristic
    if b"Return-Path:" in header or b"Received:" in header or b"From:" in header:
        return "eml"

    # HTML heuristic
    if b"<html" in header.lower() or b"<!doctype html" in header.lower():
        return "html"

    # CSV/TXT heuristic
    try:
        text = header.decode("utf-8")
        if text.isprintable() or any(c in text for c in "\n\r\t"):
            if "," in text and "\n" in text:
                return "csv"
            return "txt"
    except UnicodeDecodeError:
        pass

    # Fallback to extension if provided
    if extension_hint:
        ext = extension_hint.lower().strip(".")
        if ext in ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp", "docx", "xlsx", "pptx", "doc", "xls", "ppt", "msg", "eml", "html", "txt", "csv"]:
            return "jpg" if ext == "jpeg" else ext

    from parseanything.errors import ErrorCode, ParseError, ParseException
    raise ParseException(ParseError(code=ErrorCode.UNSUPPORTED_FORMAT, message="Unsupported file format"))
