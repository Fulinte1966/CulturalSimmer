from __future__ import annotations

"""Extract and validate PDF book metadata from XMP.

Implements the contract defined in docs/pdf/metadata-contract.md.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from defusedxml import ElementTree as ET

# ---------------------------------------------------------------------------
# XMP namespaces
# ---------------------------------------------------------------------------

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "prism": "http://prismstandard.org/namespaces/basic/2.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "xmpRights": "http://ns.adobe.com/xap/1.0/rights/",
}

NS_ALIASES = {
    "prism": (
        "http://prismstandard.org/namespaces/basic/2.1/",
        "http://prismstandard.org/namespaces/basic/3.0/",
    ),
}

# Regex matching the existing call-number parser in src/lib/bookId.ts
_ID_REGEX = re.compile(r"^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$")

# A5: 148 x 210 mm  → aspect ratio ≈ 0.70476
_A5_ASPECT = 148.0 / 210.0
_ASPECT_TOLERANCE = 0.01


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class PdfBookMetadata:
    id: str
    title: str
    edition: int
    edition_date: str
    edition_date_source: str
    pdf_create_date: str
    description: str
    tags: list[str]
    language: str
    author: Optional[str] = None
    subtitle: Optional[str] = None
    series: Optional[str] = None
    volume: Optional[int] = None
    total_volumes: Optional[int] = None
    publisher: Optional[str] = None
    source: Optional[str] = None
    rights: Optional[str] = None
    license_url: Optional[str] = None


# ---------------------------------------------------------------------------
# XMP helpers
# ---------------------------------------------------------------------------


def _expanded_names(tag: str) -> list[str]:
    if ":" not in tag:
        return [tag]
    prefix, local = tag.split(":", 1)
    namespaces = NS_ALIASES.get(prefix, (NS[prefix],))
    return [f"{{{namespace}}}{local}" for namespace in namespaces]


def _xmp_text(desc: ET.Element, tag: str) -> Optional[str]:
    """Read a simple text element, rdf:Alt, or single-value rdf:Seq/Bag."""
    if ":" in tag:
        for expanded_name in _expanded_names(tag):
            attr_text = _normalize_text(desc.attrib.get(expanded_name))
            if attr_text:
                return attr_text

    elements = [desc.find(expanded_name) for expanded_name in _expanded_names(tag)]
    el = next((candidate for candidate in elements if candidate is not None), None)
    if el is None:
        return None

    # rdf:Alt — pick the first non-empty language-tagged value
    alt = el.find("rdf:Alt", NS)
    if alt is not None:
        for li in alt.findall("rdf:li", NS):
            text = _normalize_text(li.text)
            if text:
                return text
        return None

    # rdf:Seq / rdf:Bag — return first item (used by dc:creator etc.)
    for wrapper in ("rdf:Seq", "rdf:Bag"):
        container = el.find(wrapper, NS)
        if container is not None:
            for li in container.findall("rdf:li", NS):
                text = _normalize_text(li.text)
                if text:
                    return text
            return None

    text = _normalize_text(el.text)
    return text if text else None


def _normalize_text(value: Optional[str]) -> str:
    """Normalize extracted metadata to trimmed Unicode NFC."""
    return unicodedata.normalize("NFC", value or "").strip()


def _xmp_seq(desc: ET.Element, tag: str) -> list[str]:
    """Read an rdf:Seq or rdf:Bag list."""
    elements = [desc.find(expanded_name) for expanded_name in _expanded_names(tag)]
    el = next((candidate for candidate in elements if candidate is not None), None)
    if el is None:
        return []

    container = el.find("rdf:Seq", NS) or el.find("rdf:Bag", NS)
    if container is None:
        return []

    values: list[str] = []
    for li in container.findall("rdf:li", NS):
        text = _normalize_text(li.text)
        if text:
            values.append(text)
    return values


def _xmp_int(desc: ET.Element, tag: str) -> Optional[int]:
    text = _xmp_text(desc, tag)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _edition_date_from_create_date(raw_create_date: str) -> str:
    """Return YYYY-MM from an XMP date string."""
    normalized = raw_create_date.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise MetadataError(f"xmp:CreateDate is not a valid ISO date: {raw_create_date}") from exc

    return f"{parsed.year:04d}-{parsed.month:02d}"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def extract(  # noqa: C901
    pdf_path: Path,
    classification_labels: dict[str, str] | None = None,
) -> PdfBookMetadata:
    """Extract and strictly validate PdfBookMetadata from a PDF.

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.
    classification_labels : dict[str, str] | None
        Known classification map (code → label). When omitted, the
        classification check is skipped so the function can be called
        from environments that haven't loaded the full YAML.

    Raises
    ------
    FileNotFoundError
        If *pdf_path* does not exist.
    ValueError
        If the PDF is encrypted or has zero pages.
    MetadataError
        If XMP is absent or a required field is missing / invalid.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF (fitz) is required to extract PDF metadata")

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    document = fitz.open(pdf_path)
    try:
        return _extract_from_document(document, classification_labels)
    finally:
        document.close()


def _extract_from_document(
    document,
    classification_labels: dict[str, str] | None,
) -> PdfBookMetadata:
    """Core extraction logic. *document* is managed by the caller."""
    if document.is_encrypted:
        raise ValueError("PDF is encrypted")

    if document.page_count == 0:
        raise ValueError("PDF has zero pages")

    # Aspect-ratio check ---------------------------------------------------
    for page_number, page in enumerate(document, start=1):
        w, h = page.rect.width, page.rect.height
        if w <= 0 or h <= 0:
            raise ValueError(f"PDF page {page_number} has zero dimension")
        aspect = min(w, h) / max(w, h)
        if abs(aspect - _A5_ASPECT) > _ASPECT_TOLERANCE:
            raise ValueError(
                f"Page {page_number} aspect ratio {aspect:.4f} differs from A5 "
                f"({_A5_ASPECT}) by more than 1%"
            )

    # XMP extraction -------------------------------------------------------
    xmp_bytes = document.get_xml_metadata()

    if not xmp_bytes:
        raise MetadataError("XMP metadata is absent")

    try:
        root = ET.fromstring(xmp_bytes)
    except ET.ParseError as exc:
        raise MetadataError(f"XMP is not well-formed XML: {exc}")

    rdf = root.find("rdf:RDF", NS)
    if rdf is None:
        raise MetadataError("XMP missing rdf:RDF element")

    descs = rdf.findall("rdf:Description", NS)
    if not descs:
        raise MetadataError("XMP missing rdf:Description element")

    desc = descs[0]

    # --- Required fields ---------------------------------------------------
    raw_id = _xmp_text(desc, "dc:identifier")
    if not raw_id:
        raise MetadataError("dc:identifier is missing or empty")
    if not _ID_REGEX.match(raw_id):
        raise MetadataError(f"Invalid call number: {raw_id}")

    title = _xmp_text(desc, "dc:title")
    if not title:
        raise MetadataError("dc:title is missing or empty")

    raw_edition = _xmp_text(desc, "prism:bookEdition")
    if not raw_edition:
        raise MetadataError("prism:bookEdition is missing or empty")
    try:
        edition = int(raw_edition)
    except ValueError:
        raise MetadataError(f"prism:bookEdition is not an integer: {raw_edition}")
    if edition < 1:
        raise MetadataError(f"prism:bookEdition must be positive: {edition}")

    description = _xmp_text(desc, "dc:description")
    if not description:
        raise MetadataError("dc:description is missing or empty")
    if description in {"暂无简介", "待补充"} or "TODO" in description.upper():
        raise MetadataError("dc:description appears to be placeholder text")

    pdf_create_date = _xmp_text(desc, "xmp:CreateDate")
    if not pdf_create_date:
        raise MetadataError("xmp:CreateDate is missing or empty")
    edition_date = _edition_date_from_create_date(pdf_create_date)

    # --- Optional fields ----------------------------------------------------
    raw_author = _xmp_text(desc, "dc:creator")
    language = _xmp_text(desc, "dc:language") or "zh-CN"
    subtitle = _xmp_text(desc, "prism:subtitle")

    raw_tags = _xmp_seq(desc, "dc:subject")
    seen: set[str] = set()
    tags: list[str] = []
    for t in raw_tags:
        if t and t not in seen:
            seen.add(t)
            tags.append(t)

    series = _xmp_text(desc, "prism:publicationName")
    raw_volume = _xmp_text(desc, "prism:volume")
    volume: Optional[int] = None
    if raw_volume is not None:
        try:
            volume = int(raw_volume)
        except ValueError:
            raise MetadataError(f"prism:volume is not an integer: {raw_volume}")

    publisher = _xmp_text(desc, "dc:publisher")
    source = _xmp_text(desc, "dc:source")
    rights = _xmp_text(desc, "dc:rights")
    license_url = _xmp_text(desc, "xmpRights:WebStatement")

    # --- Custom PDF Info fields --------------------------------------------
    info = _read_custom_pdf_info(document)
    total_volumes = parse_custom_pdf_info(info)

    # --- Classification check ---------------------------------------------
    classification = parse_classification_simple(raw_id)
    if classification_labels and classification not in classification_labels:
        raise MetadataError(
            f"Classification {classification} not found in classifications.yml"
        )

    # --- Volume consistency -----------------------------------------------
    vol_from_id = _extract_volume_from_id(raw_id)
    if volume is not None and vol_from_id is not None:
        if volume != vol_from_id:
            raise MetadataError(
                f"prism:volume ({volume}) conflicts with volume parsed "
                f"from ID ({vol_from_id})"
            )
    elif vol_from_id is not None:
        volume = vol_from_id

    if total_volumes is not None and volume is not None:
        if total_volumes < volume:
            raise MetadataError(
                f"total_volumes ({total_volumes}) < current volume ({volume})"
            )

    return PdfBookMetadata(
        id=raw_id,
        title=title,
        subtitle=subtitle,
        author=raw_author,
        edition=edition,
        edition_date=edition_date,
        edition_date_source="xmp:CreateDate",
        pdf_create_date=pdf_create_date,
        description=description,
        tags=tags,
        language=language,
        series=series,
        volume=volume,
        total_volumes=total_volumes,
        publisher=publisher,
        source=source,
        rights=rights,
        license_url=license_url,
    )


def parse_custom_pdf_info(
    info: dict | None,
) -> Optional[int]:
    """Parse /EbookTotalVolumes from a PDF info dict.

    Raises ``MetadataError`` when a value is present but not a positive integer.
    """
    total_volumes: Optional[int] = None

    if info is None:
        return None

    raw_tv = info.get("ebookTotalVolumes")
    if raw_tv:
        try:
            total_volumes = int(raw_tv)
        except (ValueError, TypeError):
            raise MetadataError(
                f"/EbookTotalVolumes is not a positive integer: {raw_tv}"
            )
        if total_volumes < 1:
            raise MetadataError(
                f"/EbookTotalVolumes must be positive: {total_volumes}"
            )

    return total_volumes


def _read_custom_pdf_info(document) -> dict[str, str]:
    """Read custom keys from the PDF Info dictionary via PyMuPDF xrefs."""
    try:
        info_type, info_ref = document.xref_get_key(-1, "Info")
    except (AttributeError, RuntimeError, ValueError):
        return {}
    if info_type != "xref":
        return {}

    match = re.match(r"(\d+)\s+\d+\s+R", info_ref)
    if not match:
        return {}
    info_xref = int(match.group(1))

    result: dict[str, str] = {}
    for pdf_key, output_key in (
        ("EbookTotalVolumes", "ebookTotalVolumes"),
    ):
        value_type, raw_value = document.xref_get_key(info_xref, pdf_key)
        if value_type == "null":
            continue
        value = raw_value.strip()
        if value_type == "string" and value.startswith("(") and value.endswith(")"):
            value = value[1:-1]
        result[output_key] = value
    return result


def _extract_volume_from_id(book_id: str) -> Optional[int]:
    """Return the volume number embedded in a call number, or None."""
    m = _ID_REGEX.match(book_id)
    if m is None:
        return None
    parts = book_id.split("-")
    if len(parts) == 3:
        return int(parts[2])
    return None


def parse_classification_simple(book_id: str) -> str:
    """Extract classification code from a call number.

    >>> parse_classification_simple("F0-1-1")
    'F0'
    >>> parse_classification_simple("I210.4-1")
    'I210.4'
    """
    m = _ID_REGEX.match(book_id)
    if m is None:
        raise ValueError(f"Invalid call number: {book_id}")
    # Split at first hyphen and return the prefix
    return book_id.split("-", 1)[0]


class MetadataError(Exception):
    """Raised when XMP metadata is absent, incomplete, or invalid."""
