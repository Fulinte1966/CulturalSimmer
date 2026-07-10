"""Validate changelog entries and derive statistics from their content."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CHANGE_TYPES = ("insert", "delete", "replace")


def _validate_edition(value: Any, field: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    if not isinstance(value.get("edition"), int) or value["edition"] < 1:
        raise ValueError(f"{field}.edition must be a positive integer")
    if not isinstance(value.get("editionDate"), str) or not value["editionDate"]:
        raise ValueError(f"{field}.editionDate must be a non-empty string")


def validate_changelog_metadata(changelog: dict[str, Any]) -> None:
    if not isinstance(changelog.get("bookId"), str) or not changelog["bookId"]:
        raise ValueError("changelog bookId must be a non-empty string")
    _validate_edition(changelog.get("fromEdition"), "fromEdition", optional=True)
    _validate_edition(changelog.get("toEdition"), "toEdition")


def _validate_side(side: Any, field: str) -> None:
    if not isinstance(side, dict):
        raise ValueError(f"{field} must be an object")
    if not isinstance(side.get("changedText"), str) or not side["changedText"]:
        raise ValueError(f"{field}.changedText must be a non-empty string")
    for text_field in ("prefix", "suffix"):
        if text_field in side and not isinstance(side[text_field], str):
            raise ValueError(f"{field}.{text_field} must be a string")
    if "pages" in side and (
        not isinstance(side["pages"], list)
        or not all(isinstance(page, int) and page > 0 for page in side["pages"])
    ):
        raise ValueError(f"{field}.pages must contain positive integers")
    if "pageLabels" in side and (
        not isinstance(side["pageLabels"], list)
        or not all(
            isinstance(label, str) and label for label in side["pageLabels"]
        )
    ):
        raise ValueError(f"{field}.pageLabels must contain non-empty strings")


def validate_changelog_changes(changelog: dict[str, Any]) -> list[dict[str, Any]]:
    changes = changelog.get("changes")
    if not isinstance(changes, list):
        raise ValueError("changelog changes must be an array")
    for position, change in enumerate(changes, start=1):
        if not isinstance(change, dict):
            raise ValueError(f"change {position} must be an object")
        change_type = change.get("type")
        if change_type not in CHANGE_TYPES:
            raise ValueError(f"change {position} has an invalid type")
        if "needsReview" in change and not isinstance(change["needsReview"], bool):
            raise ValueError(f"change {position}.needsReview must be a boolean")
        if change_type in {"delete", "replace"}:
            _validate_side(change.get("old"), f"change {position}.old")
        if change_type in {"insert", "replace"}:
            _validate_side(change.get("new"), f"change {position}.new")
    return changes


def calculate_changelog_summary(changelog: dict[str, Any]) -> dict[str, int]:
    changes = validate_changelog_changes(changelog)
    counts = {change_type: 0 for change_type in CHANGE_TYPES}
    for change in changes:
        counts[change["type"]] += 1
    return {
        "total": len(changes),
        "added": counts["insert"],
        "removed": counts["delete"],
        "changed": counts["replace"],
    }


def normalize_changelog(changelog: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(changelog)
    validate_changelog_metadata(normalized)
    changes = validate_changelog_changes(normalized)
    for index, change in enumerate(changes, start=1):
        change["index"] = index
    normalized["summary"] = calculate_changelog_summary(normalized)
    return normalized
