from parseanything.schema import Block, BlockType, TableData
from typing import Union
import copy

def merge_cross_page_tables(blocks_input: Union[dict[int, list[Block]], list[Block]]) -> Union[dict[int, list[Block]], list[Block]]:
    """
    Merge tables that span across multiple pages.
    Supports either dict[int, list[Block]] or list[Block].
    When matching tables across page boundaries:
    - Checks column count
    - Drops duplicate header rows on continuation pages
    - Updates TableData.pages to list all pages
    - Records page_bboxes in meta["page_bboxes"]
    """
    if isinstance(blocks_input, list):
        return _merge_blocks(blocks_input)
        
    page_keys = sorted(blocks_input.keys())
    
    for i in range(len(page_keys) - 1):
        curr_page = page_keys[i]
        next_page = page_keys[i+1]
        
        curr_blocks = blocks_input[curr_page]
        next_blocks = blocks_input[next_page]
        
        if not curr_blocks or not next_blocks:
            continue
            
        last_block = curr_blocks[-1]
        first_block = next_blocks[0]
        
        if last_block.type == BlockType.TABLE and first_block.type == BlockType.TABLE:
            if last_block.table and first_block.table:
                # Merge logic
                if last_block.table.n_cols == first_block.table.n_cols:
                    # They match!
                    
                    # Track bboxes
                    if "page_bboxes" not in last_block.meta:
                        last_block.meta["page_bboxes"] = {curr_page: last_block.bbox.model_dump() if hasattr(last_block.bbox, "model_dump") else last_block.bbox.dict() if last_block.bbox else None}
                    
                    last_block.meta["page_bboxes"][next_page] = first_block.bbox.model_dump() if hasattr(first_block.bbox, "model_dump") else first_block.bbox.dict() if first_block.bbox else None
                    
                    # Merge cells
                    offset_rows = last_block.table.n_rows
                    
                    header_rows = first_block.table.header_rows
                    
                    # Add cells from first_block, dropping headers if they match
                    is_repeated_header = False
                    if header_rows > 0:
                        # Simple check: do the text of the first row match?
                        last_headers = [c.text for c in last_block.table.cells if c.row == 0]
                        first_headers = [c.text for c in first_block.table.cells if c.row == 0]
                        if last_headers == first_headers:
                            is_repeated_header = True
                            
                    skip_rows = header_rows if is_repeated_header else 0
                    
                    added_rows = 0
                    for cell in first_block.table.cells:
                        if cell.row < skip_rows:
                            continue
                        
                        new_row_idx = cell.row - skip_rows + offset_rows
                        
                        if hasattr(cell, "model_copy"):
                            new_cell = cell.model_copy(update={"row": new_row_idx})
                        else:
                            new_cell = cell.copy(update={"row": new_row_idx})
                        last_block.table.cells.append(new_cell)
                        added_rows = max(added_rows, new_row_idx - offset_rows + 1)
                        
                    last_block.table.n_rows += added_rows
                    
                    if next_page not in last_block.table.pages:
                        last_block.table.pages.append(next_page)
                        
                    # Remove the first block from next_blocks since it's merged
                    next_blocks.pop(0)
                    
                    # Update bounding box of last_block to encompass the full thing? No, leave bbox as is, we have page_bboxes
                    
    return blocks_input

def _merge_blocks(blocks: list[Block]) -> list[Block]:
    # Fallback for list of blocks without page boundaries clearly separated
    # Not fully used in assemble logic but here for compatibility
    return blocks
