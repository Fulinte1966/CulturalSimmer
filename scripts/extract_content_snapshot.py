"""Extract a normalized, page-addressable content snapshot from a PDF."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from book_assets import normalize_pdf_text


SCHEMA_VERSION = 1
NORMALIZATION_PROFILE = "culturalsimmer-content-v1"
UPDATE_PAGE_MARKER = "CULTURALSIMMER_UPDATE_PAGE"
MARGIN_RATIO = 0.10
REPEATED_MARGIN_MIN_PAGES = 3
REPEATED_MARGIN_MIN_RATIO = 0.25

TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+(?:[._+#:/-][A-Za-z0-9]+)*"
    r"|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"
    r"|[^\s]"
)
PAGE_NUMBER_PATTERN = re.compile(
    r"^[\s\-–—·•]*(?:\d+|[ivxlcdmIVXLCDM]+)[\s\-–—·•]*$"
)
TOC_TRAILING_PAGE_PATTERN = re.compile(
    r"(?:\s|[.．·…]|-{2,})+(?:\d+|[ivxlcdmIVXLCDM]+)\s*$"
)
EDITION_LINE_PATTERN = re.compile(
    r"^\s*\d{4}\s*年\s*\d{1,2}\s*月(?:\s*第\s*\d+\s*版)?\s*$"
)


@dataclass(frozen=True)
class PageBlock:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    page_height: float
    text: str

    @property
    def margin(self) -> str | None:
        if self.y1 <= self.page_height * MARGIN_RATIO:
            return "header"
        if self.y0 >= self.page_height * (1 - MARGIN_RATIO):
            return "footer"
        return None


def normalize_extracted_text(text: str) -> str:
    """Normalize layout-only PDF text differences without compatibility folding."""

    normalized = normalize_pdf_text(text)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("\u00ad", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?<=[A-Za-z])-[ \t]*\n[ \t]*(?=[A-Za-z])", "", normalized)
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    return normalized.strip()


def tokenize_text(text: str) -> list[str]:
    """Tokenize CJK by character, Latin/number runs by word, and punctuation alone."""

    return TOKEN_PATTERN.findall(normalize_extracted_text(text))


def _canonical_margin_text(text: str) -> str:
    return re.sub(r"\s+", "", normalize_extracted_text(text))


def _is_margin_page_number(block: PageBlock) -> bool:
    return bool(block.margin and PAGE_NUMBER_PATTERN.fullmatch(block.text.strip()))


def _looks_like_toc(blocks: list[PageBlock]) -> bool:
    lines = [
        line.strip()
        for block in blocks
        for line in normalize_extracted_text(block.text).splitlines()
        if line.strip()
    ]
    if any(line in {"目录", "目錄", "Contents", "CONTENTS"} for line in lines):
        return True
    return sum(bool(TOC_TRAILING_PAGE_PATTERN.search(line)) for line in lines) >= 3


def _looks_like_colophon(blocks: list[PageBlock]) -> bool:
    text = "\n".join(block.text for block in blocks)
    indicators = (
        "版次",
        "出版日期",
        "制作日期",
        "责任编辑",
        "电子书制作",
        "检查更新",
    )
    return sum(indicator in text for indicator in indicators) >= 2


def _filter_structural_lines(text: str, *, toc: bool, colophon: bool) -> str:
    kept: list[str] = []
    for raw_line in normalize_extracted_text(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if toc:
            line = TOC_TRAILING_PAGE_PATTERN.sub("", line).rstrip()
        if colophon and (
            EDITION_LINE_PATTERN.fullmatch(line)
            or re.search(
                r"(?:检查更新|生成日期|制作日期|版本|版次).*(?:https?://|\d{4})",
                line,
            )
            or re.search(r"https?://\S*(?:releases|check|update)\S*", line, re.I)
        ):
            continue
        if line:
            kept.append(line)
    return "\n".join(kept)


def _collect_blocks(document: Any) -> tuple[dict[int, list[PageBlock]], set[int]]:
    pages: dict[int, list[PageBlock]] = {}
    marker_pages: set[int] = set()
    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        page_number = page_index + 1
        page_blocks: list[PageBlock] = []
        for raw in page.get_text("blocks", sort=True):
            if len(raw) < 7 or int(raw[6]) != 0:
                continue
            text = normalize_extracted_text(str(raw[4]))
            if not text:
                continue
            page_blocks.append(
                PageBlock(
                    page=page_number,
                    x0=float(raw[0]),
                    y0=float(raw[1]),
                    x1=float(raw[2]),
                    y1=float(raw[3]),
                    page_height=float(page.rect.height),
                    text=text,
                )
            )
        pages[page_number] = page_blocks
        if UPDATE_PAGE_MARKER in "\n".join(block.text for block in page_blocks):
            marker_pages.add(page_number)
    return pages, marker_pages


def _repeated_margin_keys(
    pages: dict[int, list[PageBlock]], excluded_pages: set[int]
) -> set[tuple[str, str]]:
    page_sets: dict[tuple[str, str], set[int]] = {}
    eligible_count = max(len(pages) - len(excluded_pages), 1)
    threshold = max(
        REPEATED_MARGIN_MIN_PAGES,
        math.ceil(eligible_count * REPEATED_MARGIN_MIN_RATIO),
    )
    for page_number, blocks in pages.items():
        if page_number in excluded_pages:
            continue
        for block in blocks:
            if not block.margin or _is_margin_page_number(block):
                continue
            key = (block.margin, _canonical_margin_text(block.text))
            if key[1]:
                page_sets.setdefault(key, set()).add(page_number)
    return {key for key, page_numbers in page_sets.items() if len(page_numbers) >= threshold}


def extract_content_snapshot(
    pdf_path: Path,
    *,
    book_id: str,
    edition: int,
    edition_date: str,
    exclude_cover: bool = True,
    excluded_pages: Iterable[int] = (),
) -> dict[str, Any]:
    """Return a normalized snapshot whose token offsets map back to PDF pages."""

    import fitz

    document = fitz.open(pdf_path)
    try:
        if document.page_count < 1:
            raise ValueError("PDF must contain at least one page")
        pages, marker_pages = _collect_blocks(document)
        excluded = {int(page) for page in excluded_pages}
        if exclude_cover:
            excluded.add(1)
        excluded.update(marker_pages)
        invalid = sorted(page for page in excluded if page < 1 or page > document.page_count)
        if invalid:
            raise ValueError(f"Excluded page is outside the PDF: {invalid[0]}")

        repeated_margin = _repeated_margin_keys(pages, excluded)
        tokens: list[str] = []
        page_runs: list[dict[str, int]] = []
        removed_counts: Counter[str] = Counter()

        for page_number, blocks in pages.items():
            if page_number in excluded:
                continue
            toc = _looks_like_toc(blocks)
            colophon = _looks_like_colophon(blocks)
            page_tokens: list[str] = []
            for block in blocks:
                if _is_margin_page_number(block):
                    removed_counts["pageNumbers"] += 1
                    continue
                margin_key = (
                    block.margin,
                    _canonical_margin_text(block.text),
                )
                if block.margin and margin_key in repeated_margin:
                    removed_counts["repeatedMargins"] += 1
                    continue
                filtered = _filter_structural_lines(
                    block.text,
                    toc=toc,
                    colophon=colophon,
                )
                page_tokens.extend(tokenize_text(filtered))
            if page_tokens:
                start = len(tokens)
                tokens.extend(page_tokens)
                page_runs.append({"start": start, "end": len(tokens), "page": page_number})

        version = getattr(fitz, "VersionBind", None)
        if not version and getattr(fitz, "version", None):
            version = fitz.version[0]
        return {
            "schemaVersion": SCHEMA_VERSION,
            "normalizationProfile": NORMALIZATION_PROFILE,
            "extractor": {"name": "PyMuPDF", "version": str(version or "unknown")},
            "bookId": book_id,
            "edition": int(edition),
            "editionDate": edition_date,
            "pageCount": document.page_count,
            "tokens": tokens,
            "pageRuns": page_runs,
            "exclusions": {
                "coverExcluded": exclude_cover,
                "pages": sorted(excluded),
                "markerPages": sorted(marker_pages),
                "removedBlocks": dict(sorted(removed_counts.items())),
            },
        }
    finally:
        document.close()


def _json_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def write_snapshot(path: Path, snapshot: dict[str, Any], *, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_bytes(snapshot)
    if path.suffix == ".gz":
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                stream.write(payload)
    else:
        path.write_bytes(payload)


def read_snapshot(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            data = json.load(stream)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Snapshot must be a JSON object: {path}")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--edition", required=True, type=int)
    parser.add_argument("--edition-date", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-cover", action="store_true")
    parser.add_argument("--exclude-page", action="append", type=int, default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    snapshot = extract_content_snapshot(
        Path(args.pdf),
        book_id=args.book_id,
        edition=args.edition,
        edition_date=args.edition_date,
        exclude_cover=not args.include_cover,
        excluded_pages=args.exclude_page,
    )
    write_snapshot(Path(args.output), snapshot, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
