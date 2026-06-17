"""Extract PDF bookmark outline to JSON using PyMuPDF."""

import json
import sys
from pathlib import Path


def extract_outline(pdf_path: str, out_path: str) -> None:
    import fitz

    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    outline = [
        {
            "level": int(level),
            "title": str(title),
            "page": int(page),
        }
        for level, title, page in toc
    ]

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(outline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/extract-outline.py input.pdf output.json"
        )
        sys.exit(1)

    extract_outline(sys.argv[1], sys.argv[2])
