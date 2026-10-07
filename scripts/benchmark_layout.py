import time
import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from parseanything.pdf.render import render_page, get_page_count
from parseanything.registry import get_layout_backend

def benchmark(pdf_path: str):
    print(f"Benchmarking Layout Backends on {pdf_path}")
    try:
        pages = get_page_count(pdf_path)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # To keep it quick, test first 3 pages
    test_pages = min(3, pages)
    backends = ["rule_based", "docling"]

    for b_name in backends:
        backend = get_layout_backend(b_name)
        if not backend or getattr(backend, "name", "") == "stub_layout":
            print(f"[{b_name}] Not available or only stub loaded.")
            continue

        print(f"\n--- Testing Backend: {b_name} ---")
        total_time = 0.0
        total_regions = 0

        for i in range(1, test_pages + 1):
            ctx = render_page(pdf_path, i)
            t0 = time.time()
            regions = backend.detect(ctx)
            t1 = time.time()
            
            elapsed = t1 - t0
            total_time += elapsed
            total_regions += len(regions)
            print(f" Page {i}: {len(regions)} regions detected in {elapsed:.3f}s")
            
        avg_time = total_time / test_pages
        print(f"[{b_name}] Summary: Avg Time/Page = {avg_time:.3f}s, Total Regions = {total_regions}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        benchmark(sys.argv[1])
    else:
        benchmark("sample_test.pdf")
