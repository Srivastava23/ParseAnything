import os
import tempfile
import subprocess
from typing import Any
from parseanything.interfaces import FormatParser
from parseanything.schema import Document, ParseError, ErrorCode
from parseanything.registry import register_format_parser
from parseanything import parse

class LegacyParser(FormatParser):
    name = "legacy"
    extensions = {"doc", "xls", "ppt", "rtf", "odt"}
    mime = {
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/rtf",
        "application/vnd.oasis.opendocument.text"
    }

    def parse(self, path: str, opts: Any) -> Document:
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.doc', '.rtf', '.odt']:
            target_ext = '.docx'
            convert_type = 'docx'
        elif ext == '.xls':
            target_ext = '.xlsx'
            convert_type = 'xlsx'
        elif ext == '.ppt':
            target_ext = '.pptx'
            convert_type = 'pptx'
        else:
            target_ext = '.docx'
            convert_type = 'docx'
            
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = os.path.join(temp_dir, "soffice_profile")
            cmd = [
                "soffice", 
                "--headless", 
                f"-env:UserInstallation=file:///{profile_dir.replace('\\', '/')}",
                "--convert-to", 
                convert_type,
                "--outdir", 
                temp_dir, 
                path
            ]
            try:
                subprocess.run(cmd, check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                doc = Document(source=os.path.basename(path), format=ext.strip('.'))
                doc.errors.append(ParseError(code=ErrorCode.TIMEOUT, message="LibreOffice conversion timed out"))
                return doc
            except subprocess.CalledProcessError as e:
                doc = Document(source=os.path.basename(path), format=ext.strip('.'))
                doc.errors.append(ParseError(code=ErrorCode.CORRUPT_FILE, message=f"LibreOffice conversion failed: {e}"))
                return doc
            except Exception as e:
                doc = Document(source=os.path.basename(path), format=ext.strip('.'))
                doc.errors.append(ParseError(code=ErrorCode.INTERNAL_ERROR, message=f"Failed to run LibreOffice: {e}"))
                return doc
                
            base_name = os.path.splitext(os.path.basename(path))[0]
            output_file = os.path.join(temp_dir, base_name + target_ext)
            
            if not os.path.exists(output_file):
                doc = Document(source=os.path.basename(path), format=ext.strip('.'))
                doc.errors.append(ParseError(code=ErrorCode.CORRUPT_FILE, message="LibreOffice did not produce an output file"))
                return doc
                
            doc = parse(output_file, options=opts)
            doc.source = os.path.basename(path)
            doc.format = ext.strip('.')
            return doc

register_format_parser(LegacyParser())
