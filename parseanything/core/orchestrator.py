import concurrent.futures
import time
from parseanything.schema import Document, Page, Block, ParseError, ErrorCode, DocStats
from parseanything.registry import get_layout_backend, get_region_extractors
from parseanything.config import Options

def process_page(page_idx: int, path: str, format_name: str, options: Options) -> Page:
    try:
        from parseanything.pdf.render import render_page
        from parseanything.pdf.classify import classify_page
    except ImportError:
        from parseanything.interfaces import PageContext
        def render_page(p, idx, dpi): return PageContext(idx, 800, 600, None, 1.0, None, "digital")
        def classify_page(ctx): return "digital", []

    ctx = render_page(path, page_idx, options.dpi)
    kind, regions_needing_ocr = classify_page(ctx)
    ctx.kind = kind
    
    layout_backend = get_layout_backend(options.layout_backend)
    regions = []
    if layout_backend:
        regions = layout_backend.detect(ctx)
        
    blocks = []
    try:
        for region in regions:
            extractors = get_region_extractors(region.label)
            for extractor in extractors:
                try:
                    extracted = extractor.extract(ctx, region)
                    blocks.extend(extracted)
                    break
                except Exception as e:
                    pass
    finally:
        if hasattr(ctx, '_pdf') and ctx._pdf:
            try:
                ctx._pdf.close()
            except Exception:
                pass
                
    return Page(number=page_idx, width=ctx.width, height=ctx.height, kind=kind, blocks=blocks)

def process_paged_document(path: str, format_name: str, options: Options) -> Document:
    doc = Document(source=path, format=format_name)
    start_time = time.time()
    
    try:
        from parseanything.pdf.render import get_page_count
        page_count = get_page_count(path)
    except ImportError:
        page_count = 1
        
    futures = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=options.workers) as executor:
        for i in range(1, page_count + 1):
            futures[executor.submit(process_page, i, path, format_name, options)] = i
            
    pages = []
    for future in concurrent.futures.as_completed(futures):
        page_idx = futures[future]
        try:
            page = future.result()
            pages.append(page)
        except Exception as e:
            doc.errors.append(ParseError(code=ErrorCode.EXTRACTOR_FAILED, message=str(e), stage="orchestrator", page=page_idx, recoverable=True))
            pages.append(Page(number=page_idx, width=0, height=0, kind="digital", blocks=[]))
            
    pages.sort(key=lambda p: p.number)
    doc.pages = pages
    
    from parseanything.core.assemble import assemble_document
    assemble_document(doc)
    
    doc.stats.elapsed_s = time.time() - start_time
    doc.stats.pages = len(pages)
    if doc.stats.elapsed_s > 0:
        doc.stats.pages_per_sec = doc.stats.pages / doc.stats.elapsed_s
        
    return doc
