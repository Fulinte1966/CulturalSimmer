"""Compare normalized PDF content snapshots and map changes back to pages."""

from __future__ import annotations

import difflib
import signal
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

from extract_content_snapshot import NORMALIZATION_PROFILE


SCHEMA_VERSION = 1
MAX_EQUAL_GAP_TO_MERGE = 4
CONTEXT_TOKENS_BEFORE = 20
CONTEXT_TOKENS_AFTER = 20
MAX_CHANGE_DISPLAY_CHARS = 160
DEFAULT_MAX_TOKENS = 400_000
DEFAULT_TIMEOUT_SECONDS = 30
REFINE_SEGMENT_TOKENS = 12_000
SENTENCE_BOUNDARIES = {"。", "！", "？", "；", "!", "?", ";"}


class DiffLimitError(RuntimeError):
    """Raised when a comparison exceeds its configured size or time limit."""


@contextmanager
def _time_limit(seconds: int) -> Iterator[None]:
    if (
        seconds <= 0
        or threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "SIGALRM")
    ):
        yield
        return

    def raise_timeout(signum, frame):  # noqa: ARG001
        raise DiffLimitError(f"Content comparison exceeded {seconds} seconds")

    previous_handler = signal.signal(signal.SIGALRM, raise_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schemaVersion") != 1:
        raise ValueError("Unsupported content snapshot schema version")
    if snapshot.get("normalizationProfile") != NORMALIZATION_PROFILE:
        raise ValueError(
            "Snapshot normalization profile mismatch; re-extract both PDFs "
            f"with {NORMALIZATION_PROFILE}"
        )
    if not isinstance(snapshot.get("tokens"), list):
        raise ValueError("Snapshot tokens must be a list")
    if not isinstance(snapshot.get("pageRuns"), list):
        raise ValueError("Snapshot pageRuns must be a list")
    token_count = len(snapshot["tokens"])
    for run in snapshot["pageRuns"]:
        if (
            not isinstance(run, dict)
            or not all(isinstance(run.get(key), int) for key in ("start", "end", "page"))
            or run["start"] < 0
            or run["start"] >= run["end"]
            or run["end"] > token_count
            or run["page"] < 1
        ):
            raise ValueError("Snapshot contains an invalid page run")


def _refined_opcodes(
    old_tokens: list[str], new_tokens: list[str]
) -> list[tuple[str, int, int, int, int]]:
    coarse = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=True)
    result: list[tuple[str, int, int, int, int]] = []
    for tag, old_start, old_end, new_start, new_end in coarse.get_opcodes():
        old_size = old_end - old_start
        new_size = new_end - new_start
        if tag == "equal" or max(old_size, new_size) > REFINE_SEGMENT_TOKENS:
            result.append((tag, old_start, old_end, new_start, new_end))
            continue
        detail = difflib.SequenceMatcher(
            None,
            old_tokens[old_start:old_end],
            new_tokens[new_start:new_end],
            autojunk=False,
        )
        result.extend(
            (
                detail_tag,
                old_start + detail_old_start,
                old_start + detail_old_end,
                new_start + detail_new_start,
                new_start + detail_new_end,
            )
            for (
                detail_tag,
                detail_old_start,
                detail_old_end,
                detail_new_start,
                detail_new_end,
            ) in detail.get_opcodes()
        )
    return result


def _merge_changes(
    opcodes: list[tuple[str, int, int, int, int]],
) -> list[tuple[str, int, int, int, int]]:
    merged: list[tuple[str, int, int, int, int]] = []
    index = 0
    while index < len(opcodes):
        tag, old_start, old_end, new_start, new_end = opcodes[index]
        if tag == "equal":
            index += 1
            continue
        constituent_tags = {tag}
        cursor = index + 1
        while cursor + 1 < len(opcodes):
            equal = opcodes[cursor]
            following = opcodes[cursor + 1]
            if equal[0] != "equal" or following[0] == "equal":
                break
            equal_size = max(equal[2] - equal[1], equal[4] - equal[3])
            if equal_size > MAX_EQUAL_GAP_TO_MERGE:
                break
            old_end = following[2]
            new_end = following[4]
            constituent_tags.add(following[0])
            cursor += 2
        if constituent_tags == {"insert"}:
            merged_tag = "insert"
        elif constituent_tags == {"delete"}:
            merged_tag = "delete"
        else:
            merged_tag = "replace"
        merged.append((merged_tag, old_start, old_end, new_start, new_end))
        index = cursor
    return merged


def _pages_for_range(
    snapshot: dict[str, Any], start: int, end: int
) -> list[int]:
    pages = {
        int(run["page"])
        for run in snapshot["pageRuns"]
        if int(run["start"]) < end and int(run["end"]) > start
    }
    return sorted(pages)


def _is_word_token(token: str) -> bool:
    return bool(token) and all(
        character.isascii() and character.isalnum()
        for character in token.replace("-", "")
    )


def join_tokens(tokens: list[str]) -> str:
    output: list[str] = []
    previous: str | None = None
    for token in tokens:
        if previous is not None and _is_word_token(previous) and _is_word_token(token):
            output.append(" ")
        output.append(token)
        previous = token
    return "".join(output)


def _context_side(
    snapshot: dict[str, Any], start: int, end: int
) -> dict[str, Any]:
    tokens = snapshot["tokens"]
    left_limit = max(0, start - CONTEXT_TOKENS_BEFORE)
    right_limit = min(len(tokens), end + CONTEXT_TOKENS_AFTER)

    left_start = left_limit
    for position in range(start - 1, left_limit - 1, -1):
        if tokens[position] in SENTENCE_BOUNDARIES:
            left_start = position + 1
            break

    right_end = right_limit
    for position in range(end, right_limit):
        if tokens[position] in SENTENCE_BOUNDARIES:
            right_end = position + 1
            break

    prefix = join_tokens(tokens[left_start:start])
    changed = join_tokens(tokens[start:end])
    suffix = join_tokens(tokens[end:right_end])
    prefix_truncated = (
        left_start > 0 and tokens[left_start - 1] not in SENTENCE_BOUNDARIES
    )
    suffix_truncated = (
        right_end < len(tokens)
        and tokens[right_end - 1] not in SENTENCE_BOUNDARIES
    )

    changed_truncated = len(changed) > MAX_CHANGE_DISPLAY_CHARS
    if changed_truncated:
        left_chars = (MAX_CHANGE_DISPLAY_CHARS - 1) // 2
        right_chars = MAX_CHANGE_DISPLAY_CHARS - 1 - left_chars
        changed = f"{changed[:left_chars]}…{changed[-right_chars:]}"
        prefix_truncated = prefix_truncated or bool(prefix)
        suffix_truncated = suffix_truncated or bool(suffix)
        prefix = ""
        suffix = ""
    else:
        context_budget = MAX_CHANGE_DISPLAY_CHARS - len(changed)
        prefix_budget = context_budget // 2
        suffix_budget = context_budget - prefix_budget
        if len(prefix) > prefix_budget:
            prefix = prefix[-prefix_budget:] if prefix_budget else ""
            prefix_truncated = True
        if len(suffix) > suffix_budget:
            suffix = suffix[:suffix_budget]
            suffix_truncated = True

    return {
        "pages": _pages_for_range(snapshot, start, end),
        "prefix": prefix,
        "changedText": changed,
        "suffix": suffix,
        "changedTokenCount": end - start,
        "changedTextTruncated": changed_truncated,
        "prefixTruncated": prefix_truncated,
        "suffixTruncated": suffix_truncated,
    }


def compare_content_snapshots(
    old_snapshot: dict[str, Any] | None,
    new_snapshot: dict[str, Any],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return the structured changelog for one adjacent edition pair."""

    _validate_snapshot(new_snapshot)
    if old_snapshot is None:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "bookId": new_snapshot["bookId"],
            "normalizationProfile": NORMALIZATION_PROFILE,
            "fromEdition": None,
            "toEdition": {
                "edition": new_snapshot["edition"],
                "editionDate": new_snapshot["editionDate"],
            },
            "summary": {"total": 0, "added": 0, "removed": 0, "changed": 0},
            "changes": [],
        }

    _validate_snapshot(old_snapshot)
    if old_snapshot.get("bookId") != new_snapshot.get("bookId"):
        raise ValueError("Cannot compare snapshots from different books")
    if int(old_snapshot["edition"]) >= int(new_snapshot["edition"]):
        raise ValueError("Previous edition must be lower than the current edition")

    old_tokens = old_snapshot["tokens"]
    new_tokens = new_snapshot["tokens"]
    if max(len(old_tokens), len(new_tokens)) > max_tokens:
        raise DiffLimitError(
            f"Snapshot exceeds the {max_tokens:,}-token comparison limit"
        )

    started = time.monotonic()
    if old_tokens == new_tokens:
        merged_opcodes: list[tuple[str, int, int, int, int]] = []
    else:
        with _time_limit(timeout_seconds):
            merged_opcodes = _merge_changes(_refined_opcodes(old_tokens, new_tokens))
    elapsed = time.monotonic() - started

    changes: list[dict[str, Any]] = []
    counts = {"insert": 0, "delete": 0, "replace": 0}
    for index, (tag, old_start, old_end, new_start, new_end) in enumerate(
        merged_opcodes, start=1
    ):
        change: dict[str, Any] = {"index": index, "type": tag}
        if tag in {"delete", "replace"}:
            change["old"] = _context_side(old_snapshot, old_start, old_end)
        if tag in {"insert", "replace"}:
            change["new"] = _context_side(new_snapshot, new_start, new_end)
        changes.append(change)
        counts[tag] += 1

    return {
        "schemaVersion": SCHEMA_VERSION,
        "bookId": new_snapshot["bookId"],
        "normalizationProfile": NORMALIZATION_PROFILE,
        "fromEdition": {
            "edition": old_snapshot["edition"],
            "editionDate": old_snapshot["editionDate"],
        },
        "toEdition": {
            "edition": new_snapshot["edition"],
            "editionDate": new_snapshot["editionDate"],
        },
        "summary": {
            "total": len(changes),
            "added": counts["insert"],
            "removed": counts["delete"],
            "changed": counts["replace"],
        },
        "comparison": {
            "algorithm": "SequenceMatcher coarse-refine bounded",
            "elapsedSeconds": round(elapsed, 3),
            "oldTokenCount": len(old_tokens),
            "newTokenCount": len(new_tokens),
        },
        "changes": changes,
    }
