import json
from parseanything.schema import Document, BlockType

def document_to_json(doc: Document) -> str:
    return doc.model_dump_json(indent=2)

def table_to_markdown(table) -> str:
    if table.markdown:
        return table.markdown
    if not table.cells:
        return f"[Table: {table.n_rows} rows x {table.n_cols} cols]"
    grid = [["" for _ in range(table.n_cols)] for _ in range(table.n_rows)]
    for cell in table.cells:
        if 0 <= cell.row < table.n_rows and 0 <= cell.col < table.n_cols:
            grid[cell.row][cell.col] = str(cell.text).replace("\n", " ").replace("|", "\\|")
    md = []
    if grid:
        md.append("| " + " | ".join(grid[0]) + " |")
        md.append("|" + "|".join(["---" for _ in range(table.n_cols)]) + "|")
        for r in range(1, table.n_rows):
            md.append("| " + " | ".join(grid[r]) + " |")
    return "\n".join(md)

def document_to_markdown(doc: Document, include_ids: bool = True) -> str:
    md_lines = []
    
    for page in doc.pages:
        for block in page.blocks:
            prefix = ""
            if include_ids:
                prefix = f"<!-- {block.id} conf={block.confidence:.2f} -->\n"
                
            if block.flagged:
                prefix += f"> ⚠️ low confidence: {block.flag_reason}\n"
                
            content = block.content
            if block.type == BlockType.HEADING:
                level = block.level or 1
                md_lines.append(f"{prefix}{'#' * level} {content}")
            elif block.type == BlockType.LIST:
                md_lines.append(f"{prefix}- {content}")
            elif block.type == BlockType.TABLE and block.table:
                md_lines.append(f"{prefix}{table_to_markdown(block.table)}")
            elif block.type == BlockType.EQUATION and block.latex:
                md_lines.append(f"{prefix}$$\n{block.latex}\n$$")
            elif block.type == BlockType.CHART and block.chart:
                md_lines.append(f"{prefix}[Chart: {block.chart.chart_type}] {block.chart.title or ''}")
            else:
                if content:
                    md_lines.append(f"{prefix}{content}")
            md_lines.append("")
            
    return "\n".join(md_lines)
