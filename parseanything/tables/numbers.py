import re
from parseanything.schema import TableData, Block

def validate_financial_numbers(block: Block) -> Block:
    """
    Validates numeric cells in a table for OCR errors or suspicious characters.
    Flags the block and reduces confidence if suspicious numbers are found.
    Keeps cell text exactly as printed.
    """
    if not block.table:
        return block
        
    suspicious_pattern = re.compile(r'(?i)(\d+[Oo]\d+)|(^[Oo]\d+)|(\d+[Oo]$)|(\d+[lI]\d+)|(^[lI]\d+)|(\d+[lI]$)')
    
    suspicious_cells = []
    
    for cell in block.table.cells:
        text = cell.text.strip()
        if not text:
            continue
            
        if suspicious_pattern.search(text):
            suspicious_cells.append(cell)
            
    if suspicious_cells:
        block.flagged = True
        block.flag_reason = f"Suspicious OCR characters in numeric cells: {', '.join([c.text for c in suspicious_cells[:5]])}"
        block.confidence *= 0.8
        
    return block
