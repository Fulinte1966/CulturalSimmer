"""Validated, atomic storage helpers for generated homepage updates."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

GENERATED_TYPES = {"book-added", "book-updated"}


def validate_generated_update(item: object) -> dict:
    if not isinstance(item, dict):
        raise ValueError("Generated site update must be an object")
    required = {"id", "type", "publishedAt", "bookId"}
    missing = sorted(required - item.keys())
    if missing:
        raise ValueError(f"Generated site update is missing: {', '.join(missing)}")
    if not all(isinstance(item[key], str) and item[key] for key in required):
        raise ValueError("Generated site update string fields must not be empty")
    if item["type"] not in GENERATED_TYPES:
        raise ValueError(f"Unknown generated site update type: {item['type']}")
    try:
        datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid generated site update date: {item['publishedAt']}") from exc
    if item["type"] == "book-updated":
        edition = item.get("edition")
        if not isinstance(edition, int) or isinstance(edition, bool) or edition < 1:
            raise ValueError("book-updated requires a positive integer edition")
    elif "edition" in item:
        raise ValueError("book-added must not store an edition")
    return item


def load_generated_updates(path: Path) -> list[dict]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("generated-updates.json must contain an array")
    updates = [validate_generated_update(item) for item in value]
    ids = [item["id"] for item in updates]
    if len(ids) != len(set(ids)):
        raise ValueError("generated-updates.json contains duplicate IDs")
    return updates


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def append_generated_update(path: Path, incoming: dict) -> bool:
    incoming = validate_generated_update(incoming)
    updates = load_generated_updates(path)
    existing = next((item for item in updates if item["id"] == incoming["id"]), None)
    if existing is not None:
        if existing != incoming:
            raise ValueError(f"Conflicting generated site update ID: {incoming['id']}")
        return False
    updates.append(incoming)
    updates.sort(key=lambda item: (item["publishedAt"], item["id"]))
    atomic_write_json(path, updates)
    return True
