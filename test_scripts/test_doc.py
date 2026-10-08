from parseanything.schema import Document
import json

doc_dict = {
  "source": "test",
  "format": "csv",
  "pages": [
    {
      "number": 1,
      "width": 100,
      "height": 100,
      "kind": "virtual",
      "blocks": [
        {
          "id": "b1",
          "type": "table",
          "page": 1,
          "table": {
            "n_rows": 2,
            "n_cols": 2,
            "cells": [
              {"row": 0, "col": 0, "text": "A"},
              {"row": 1, "col": 1, "text": "B"}
            ]
          }
        }
      ]
    }
  ],
  "stats": {"pages": 1, "blocks": 1}
}

doc = Document(**doc_dict)
print("Block table:", doc.pages[0].blocks[0].table)
print("Export test...")
from parseanything.exporters.xlsx import XlsxExporter
exp = XlsxExporter()
exp.export(doc, "test_out.xlsx", {})
print("Done")
