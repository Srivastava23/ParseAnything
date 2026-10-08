from parseanything import parse
from parseanything.config import Options
doc = parse("test2.csv", options=Options())
texts = []
for p in doc.pages:
    for b in p.blocks:
        if getattr(b, 'table', None) and getattr(b.table, 'cells', None):
            for cell in b.table.cells:
                if cell.text:
                    texts.append(cell.text)
full_text = "\n".join(texts)
print(len(full_text))
print(full_text)
