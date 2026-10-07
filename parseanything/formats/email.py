import os
import email
from email import policy
from typing import Any
from parseanything.interfaces import FormatParser
from parseanything.schema import Document, Page, Block, BlockType, ParseError, ErrorCode
from parseanything.registry import register_format_parser
from parseanything import parse
import tempfile
from bs4 import BeautifulSoup

class EmailParser(FormatParser):
    name = "email"
    extensions = {"eml", "msg"}
    mime = {"message/rfc822", "application/vnd.ms-outlook"}

    def parse(self, path: str, opts: Any) -> Document:
        doc = Document(source=os.path.basename(path), format=os.path.splitext(path)[1].lower().strip('.'))
        
        ext = os.path.splitext(path)[1].lower()
        if ext == '.msg':
            try:
                import extract_msg
                msg = extract_msg.Message(path)
                subject = msg.subject or "No Subject"
                sender = msg.sender or "Unknown Sender"
                date = msg.date or "Unknown Date"
                body = msg.body or ""
                attachments = msg.attachments
                
                blocks = self._create_blocks(subject, sender, date, body)
                self._process_msg_attachments(attachments, blocks, opts)
                msg.close()
            except ImportError:
                doc.errors.append(ParseError(code=ErrorCode.INTERNAL_ERROR, message="extract-msg package is required for .msg files"))
                return doc
        else: # .eml
            with open(path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
            
            subject = msg.get('subject', 'No Subject')
            sender = msg.get('from', 'Unknown Sender')
            date = msg.get('date', 'Unknown Date')
            
            body = ""
            attachments = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition"))
                    content_type = part.get_content_type()
                    
                    if "attachment" in content_disposition or part.get_filename():
                        attachments.append(part)
                    elif content_type == "text/plain":
                        body += part.get_content() + "\n"
                    elif content_type == "text/html" and not body:
                        html = part.get_content()
                        soup = BeautifulSoup(html, "html.parser")
                        body += soup.get_text() + "\n"
            else:
                body = msg.get_content()
                
            blocks = self._create_blocks(subject, sender, date, body)
            self._process_eml_attachments(attachments, blocks, opts)
            
        page = Page(number=1, width=800, height=1100, blocks=blocks, kind="virtual")
        doc.pages.append(page)
        doc.stats.pages = 1
        doc.stats.blocks = len(blocks)
        return doc
        
    def _create_blocks(self, subject, sender, date, body):
        blocks = []
        blocks.append(Block(id="p1_b1", type=BlockType.HEADING, page=1, content=f"Subject: {subject}", reading_order=1))
        blocks.append(Block(id="p1_b2", type=BlockType.PARAGRAPH, page=1, content=f"From: {sender}\nDate: {date}", reading_order=2))
        blocks.append(Block(id="p1_b3", type=BlockType.PARAGRAPH, page=1, content=body, reading_order=3))
        return blocks
        
    def _process_msg_attachments(self, attachments, blocks, opts):
        block_idx = len(blocks) + 1
        with tempfile.TemporaryDirectory() as temp_dir:
            for att in attachments:
                if att.longFilename:
                    filename = att.longFilename
                elif att.shortFilename:
                    filename = att.shortFilename
                else:
                    filename = "attachment"
                    
                path = os.path.join(temp_dir, filename)
                with open(path, 'wb') as f:
                    f.write(att.data)
                
                blocks.append(Block(id=f"p1_b{block_idx}", type=BlockType.HEADING, page=1, content=f"Attachment: {filename}", reading_order=block_idx))
                block_idx += 1
                
                try:
                    att_doc = parse(path, options=opts)
                    for p in att_doc.pages:
                        for b in p.blocks:
                            b.id = f"att_{b.id}"
                            b.reading_order = block_idx
                            blocks.append(b)
                            block_idx += 1
                except Exception:
                    pass

    def _process_eml_attachments(self, attachments, blocks, opts):
        block_idx = len(blocks) + 1
        with tempfile.TemporaryDirectory() as temp_dir:
            for part in attachments:
                filename = part.get_filename() or "attachment"
                path = os.path.join(temp_dir, filename)
                payload = part.get_payload(decode=True)
                if payload:
                    with open(path, 'wb') as f:
                        f.write(payload)
                        
                    blocks.append(Block(id=f"p1_b{block_idx}", type=BlockType.HEADING, page=1, content=f"Attachment: {filename}", reading_order=block_idx))
                    block_idx += 1
                    
                    try:
                        att_doc = parse(path, options=opts)
                        for p in att_doc.pages:
                            for b in p.blocks:
                                b.id = f"att_{b.id}"
                                b.reading_order = block_idx
                                blocks.append(b)
                                block_idx += 1
                    except Exception:
                        pass

register_format_parser(EmailParser())
