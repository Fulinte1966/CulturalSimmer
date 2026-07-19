"""读取并执行网站入库策略。"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


POLICY_PATH = Path("config/publication-policy.yml")
BOOK_ID_RE = re.compile(r"^[A-Z](?:\d+)?-\d+(?:-\d+)?$")


def load_blocked_books(root: Path) -> dict[str, str]:
    """返回不得公开发行的书目及原因，并严格校验策略文件。"""

    path = root / POLICY_PATH
    data = yaml.safe_load(path.read_text("utf-8"))
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("publication-policy.yml must use schemaVersion: 1")

    records = data.get("blockedBooks")
    if not isinstance(records, list):
        raise ValueError("publication-policy.yml blockedBooks must be a sequence")

    blocked: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Every blocked book must be a mapping")
        book_id = record.get("id")
        reason = record.get("reason")
        if not isinstance(book_id, str) or BOOK_ID_RE.fullmatch(book_id) is None:
            raise ValueError(f"Invalid blocked book ID: {book_id}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Blocked book {book_id} requires a reason")
        if book_id in blocked:
            raise ValueError(f"Duplicate blocked book ID: {book_id}")
        blocked[book_id] = reason.strip()
    return blocked


def assert_publishable(root: Path, book_id: str) -> None:
    """阻止本地专用书目进入候选、Release 和网站。"""

    reason = load_blocked_books(root).get(book_id)
    if reason:
        raise SystemExit(f"Publication policy blocks {book_id}: {reason}")
