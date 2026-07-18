"""Edition sequencing checks shared by local upload and CI ingest."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EditionCheck:
    pdf_edition: int
    existing_editions: list[int]
    reserved_editions: list[int]
    highest_existing_edition: int | None
    expected_edition: int
    ok: bool
    message: str
    skipped: bool = False


def load_book_frontmatter(root: Path, book_id: str) -> dict[str, Any] | None:
    path = root / "src" / "content" / "books" / f"{book_id}.md"
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid frontmatter in {path}")

    _, frontmatter, _ = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid frontmatter in {path}")
    return data


def get_existing_editions(root: Path, book_id: str) -> list[int]:
    data = load_book_frontmatter(root, book_id)
    if data is None:
        return []

    editions: set[int] = set()
    raw_editions = data.get("editions")
    if isinstance(raw_editions, list):
        for item in raw_editions:
            if isinstance(item, dict) and isinstance(item.get("edition"), int):
                editions.add(item["edition"])

    return sorted(editions)


def get_reserved_editions(book_id: str, ledger_path: Path | None = None) -> list[int]:
    """Return publicly used edition numbers recorded in the private ledger."""

    configured = ledger_path or (
        Path(value)
        if (value := os.environ.get("CULTURALSIMMER_PUBLICATION_LEDGER"))
        else None
    )
    if configured is None or not configured.is_file():
        return []
    value = json.loads(configured.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ValueError("Publication ledger must use schemaVersion 1")
    reserved: set[int] = set()
    for record in value.get("removals", []):
        if not isinstance(record, dict) or record.get("bookId") != book_id:
            continue
        editions = record.get("editions")
        if not isinstance(editions, list):
            raise ValueError("Publication ledger removal editions must be an array")
        for edition in editions:
            if not isinstance(edition, int) or isinstance(edition, bool) or edition < 1:
                raise ValueError("Publication ledger editions must be positive integers")
            reserved.add(edition)
    return sorted(reserved)


def find_previous_edition_record(
    root: Path, book_id: str, current_edition: int
) -> dict[str, Any] | None:
    """Return the highest recorded edition below *current_edition*."""

    data = load_book_frontmatter(root, book_id)
    if data is None:
        return None
    raw_editions = data.get("editions")
    if not isinstance(raw_editions, list):
        return None
    candidates = [
        dict(item)
        for item in raw_editions
        if isinstance(item, dict)
        and isinstance(item.get("edition"), int)
        and item["edition"] < current_edition
    ]
    return max(candidates, key=lambda item: item["edition"], default=None)


def check_expected_edition(
    root: Path,
    book_id: str,
    pdf_edition: int,
    *,
    allow_edition_skip: bool = False,
    ledger_path: Path | None = None,
) -> EditionCheck:
    existing = get_existing_editions(root, book_id)
    reserved = get_reserved_editions(book_id, ledger_path)
    used = sorted(set(existing) | set(reserved))
    highest = max(used) if used else None
    expected = 1 if highest is None else highest + 1

    if pdf_edition in used:
        return EditionCheck(
            pdf_edition=pdf_edition,
            existing_editions=existing,
            reserved_editions=reserved,
            highest_existing_edition=highest,
            expected_edition=expected,
            ok=False,
            message=f"该版次已存在，应为第 {expected} 版",
        )

    if pdf_edition == expected:
        return EditionCheck(
            pdf_edition=pdf_edition,
            existing_editions=existing,
            reserved_editions=reserved,
            highest_existing_edition=highest,
            expected_edition=expected,
            ok=True,
            message="通过",
        )

    if pdf_edition > expected and allow_edition_skip:
        return EditionCheck(
            pdf_edition=pdf_edition,
            existing_editions=existing,
            reserved_editions=reserved,
            highest_existing_edition=highest,
            expected_edition=expected,
            ok=True,
            message=f"通过，已允许跳版；通常应为第 {expected} 版",
            skipped=True,
        )

    if pdf_edition > expected:
        return EditionCheck(
            pdf_edition=pdf_edition,
            existing_editions=existing,
            reserved_editions=reserved,
            highest_existing_edition=highest,
            expected_edition=expected,
            ok=False,
            message=f"检测到跳版，预期为第 {expected} 版",
        )

    return EditionCheck(
        pdf_edition=pdf_edition,
        existing_editions=existing,
        reserved_editions=reserved,
        highest_existing_edition=highest,
        expected_edition=expected,
        ok=False,
        message=f"低于预期版次，应为第 {expected} 版",
    )


def format_edition_check_lines(check: EditionCheck) -> list[str]:
    highest = (
        str(check.highest_existing_edition)
        if check.highest_existing_edition is not None
        else "无"
    )
    status = "通过" if check.ok else f"失败，{check.message}"
    return [
        f"PDF 声明版次：{check.pdf_edition}",
        f"公开记录及私有台账中的历史最高版次：{highest}",
        f"私有台账占用版次：{', '.join(map(str, check.reserved_editions)) or '无'}",
        f"脚本预期版次：{check.expected_edition}",
        f"版次校验：{status}",
    ]
