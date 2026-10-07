from parseanything.schema import Block, BlockType, TableData

from typing import Union
from parseanything.schema import Block, BlockType, TableData

def _merge_blocks(blocks: list[Block]) -> list[Block]:
    merged_blocks = []
    current_table_block = None
    
    for block in blocks:
        if block.type == BlockType.TABLE and block.table is not None:
            if current_table_block is None:
                current_table_block = block
            else:
                # Merge logic: append rows
                offset_rows = current_table_block.table.n_rows
                
                for cell in block.table.cells:
                    # Adjust row index for the merged table
                    if hasattr(cell, "model_copy"):
                        new_cell = cell.model_copy(update={"row": cell.row + offset_rows})
                    else:
                        new_cell = cell.copy(update={"row": cell.row + offset_rows})
                    current_table_block.table.cells.append(new_cell)
                    
                current_table_block.table.n_rows += block.table.n_rows
                
                if block.page not in current_table_block.table.pages:
                    current_table_block.table.pages.append(block.page)
                    
                # Merge html/markdown logic if present
                if current_table_block.table.html and block.table.html:
                    current_table_block.table.html += "\n" + block.table.html
                if current_table_block.table.markdown and block.table.markdown:
                    current_table_block.table.markdown += "\n" + block.table.markdown
                    
        else:
            if current_table_block is not None:
                merged_blocks.append(current_table_block)
                current_table_block = None
            merged_blocks.append(block)
            
    if current_table_block is not None:
        merged_blocks.append(current_table_block)
        
    return merged_blocks

def merge_cross_page_tables(blocks_input: Union[dict[int, list[Block]], list[Block]]):
    """
    Merge tables that span across multiple pages.
    Supports either dict[int, list[Block]] or list[Block].
    """
    if isinstance(blocks_input, dict):
        page_keys = sorted(blocks_input.keys())
        all_blocks = []
        for p in page_keys:
            all_blocks.extend(blocks_input[p])
        merged = _merge_blocks(all_blocks)
        res = {p: [] for p in page_keys}
        for b in merged:
            p = b.page
            if p not in res:
                res[p] = []
            res[p].append(b)
        return res
    return _merge_blocks(blocks_input)

