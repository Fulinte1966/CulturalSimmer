"""Generate static cover, outline, and reading metadata from a PDF."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CJK_PATTERN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    r"\u3040-\u309f\u30a0-\u30ff\uac00-\ud7a3]"
)
LATIN_TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+(?:[._+#/-][A-Za-z0-9]+)*"
)
LEGACY_BYTE_RUN_PATTERN = re.compile(r"[\x00-\xff]+")
SPARSE_TEXT_UNITS_PER_PAGE = 80


def normalize_pdf_text(text: str) -> str:
    """Recover legacy GBK text exposed by a PDF as Latin-1 bytes."""

    def decode_run(match: re.Match[str]) -> str:
        raw = match.group(0)
        high_byte_count = sum(ord(character) >= 0x80 for character in raw)
        if high_byte_count < 2 or high_byte_count / len(raw) < 0.3:
            return raw

        try:
            decoded = raw.encode("latin-1").decode("gb18030")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return raw

        if len(CJK_PATTERN.findall(decoded)) <= len(CJK_PATTERN.findall(raw)):
            return raw
        return decoded

    return LEGACY_BYTE_RUN_PATTERN.sub(decode_run, text)


def count_text_units(text: str) -> tuple[int, int]:
    """Count CJK characters and Latin/number tokens independently."""

    return (
        len(CJK_PATTERN.findall(text)),
        len(LATIN_TOKEN_PATTERN.findall(text)),
    )


def extract_book_assets(
    pdf_path: Path,
    book_id: str,
    edition: int,
    root: Path,
) -> dict[str, Path]:
    """Generate all committed static assets for one PDF edition."""

    import fitz

    tag = f"{book_id}_v{edition}"
    outline_path = root / "src" / "data" / "outlines" / f"{tag}.json"
    reading_path = root / "src" / "data" / "reading" / f"{tag}.json"
    cover_path = root / "public" / "covers" / f"{tag}.png"
    spine_path = root / "public" / "covers" / f"{tag}_spine.png"

    document = fitz.open(pdf_path)
    if document.page_count < 1:
        raise ValueError("PDF must contain at least one page")

    outline = [
        {
            "level": int(level),
            "title": normalize_pdf_text(str(title)),
            "page": int(page),
        }
        for level, title, page in document.get_toc()
    ]

    text = "\n".join(
        normalize_pdf_text(page.get_text("text")) for page in document
    )
    cjk_count, latin_count = count_text_units(text)
    total_units = cjk_count + latin_count
    units_per_page = total_units / document.page_count

    reading: dict[str, Any] = {
        "pageCount": document.page_count,
        "fileSizeBytes": pdf_path.stat().st_size,
    }
    if units_per_page >= SPARSE_TEXT_UNITS_PER_PAGE:
        reading["cjkCharacterCount"] = cjk_count
        reading["latinTokenCount"] = latin_count

    first_page = document.load_page(0)
    scale = min(3.0, 640 / max(first_page.rect.width, 1))
    pixmap = first_page.get_pixmap(
        matrix=fitz.Matrix(scale, scale),
        alpha=False,
    )
    # Stretch the cover's first rendered pixel column across the spine so the
    # spine's inner edge always matches the front cover without a color seam.
    spine_sample_width = 1 / scale
    spine_pixmap = first_page.get_pixmap(
        matrix=fitz.Matrix(scale, scale),
        clip=fitz.Rect(
            first_page.rect.x0,
            first_page.rect.y0,
            first_page.rect.x0 + spine_sample_width,
            first_page.rect.y1,
        ),
        alpha=False,
    )

    outline_path.parent.mkdir(parents=True, exist_ok=True)
    reading_path.parent.mkdir(parents=True, exist_ok=True)
    cover_path.parent.mkdir(parents=True, exist_ok=True)

    outline_path.write_text(
        json.dumps(outline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    reading_path.write_text(
        json.dumps(reading, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    pixmap.save(cover_path)
    spine_pixmap.save(spine_path)
    document.close()

    return {
        "outline": outline_path,
        "reading": reading_path,
        "cover": cover_path,
        "spine": spine_path,
    }
