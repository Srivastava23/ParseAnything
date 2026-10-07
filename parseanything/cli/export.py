import json
from parseanything.schema import Document, BlockType

def document_to_json(doc: Document) -> str:
    return doc.model_dump_json(indent=2)

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
                if block.table.markdown:
                    md_lines.append(f"{prefix}{block.table.markdown}")
                else:
                    md_lines.append(f"{prefix}[Table: {block.table.n_rows} rows x {block.table.n_cols} cols]")
            elif block.type == BlockType.EQUATION and block.latex:
                md_lines.append(f"{prefix}$$\n{block.latex}\n$$")
            elif block.type == BlockType.CHART and block.chart:
                md_lines.append(f"{prefix}[Chart: {block.chart.chart_type}] {block.chart.title or ''}")
            else:
                if content:
                    md_lines.append(f"{prefix}{content}")
            md_lines.append("")
            
    return "\n".join(md_lines)
