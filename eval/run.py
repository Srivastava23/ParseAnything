import os
import argparse
import time
import pdfplumber
from pathlib import Path
from parseanything import parse

def get_baseline_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass
    return text

def run_eval(data_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    results = []
    
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if not os.path.isfile(filepath):
            continue
            
        print(f"Evaluating {filename}...")
        
        # Baseline
        start_base = time.time()
        base_text = ""
        if filename.endswith(".pdf"):
            base_text = get_baseline_text(filepath)
        time_base = time.time() - start_base
        
        # ParseAnything
        start_pa = time.time()
        try:
            doc = parse(filepath)
            pa_text = "\n".join([b.content for p in doc.pages for b in p.blocks])
            pa_blocks = sum([len(p.blocks) for p in doc.pages])
            pa_pages = len(doc.pages)
            pa_status = "OK"
            if doc.errors:
                pa_status = f"ERRORS: {len(doc.errors)}"
        except Exception as e:
            pa_text = ""
            pa_blocks = 0
            pa_pages = 0
            pa_status = f"CRASH: {e}"
        time_pa = time.time() - start_pa
        
        results.append({
            "file": filename,
            "pa_pages": pa_pages,
            "pa_blocks": pa_blocks,
            "pa_time": time_pa,
            "pa_status": pa_status,
            "base_time": time_base,
            "base_text_len": len(base_text),
            "pa_text_len": len(pa_text)
        })
        
    md_path = os.path.join(out_dir, "results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# ParseAnything Evaluation Results\n\n")
        f.write("| File | PA Pages | PA Blocks | PA Time (s) | Baseline Time (s) | PA Status |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in results:
            f.write(f"| {r['file']} | {r['pa_pages']} | {r['pa_blocks']} | {r['pa_time']:.2f} | {r['base_time']:.2f} | {r['pa_status']} |\n")
            
    print(f"Results written to {md_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run_eval(args.data, args.out)
