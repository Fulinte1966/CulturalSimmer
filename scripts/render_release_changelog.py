"""Render a structured electronic-book changelog as GitHub Markdown."""

from __future__ import annotations

from typing import Any

from changelog_model import calculate_changelog_summary


def escape_markdown_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for character in ("*", "_", "~", "`"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped.replace("<", "&lt;").replace(">", "&gt;")


def _edition_label(edition: dict[str, Any]) -> str:
    year, month = str(edition["editionDate"]).split("-", 1)
    return f"{int(year)} 年 {int(month)} 月第 {int(edition['edition'])} 版"


def _page_label(page_labels: list[str], pages: list[int]) -> str:
    labels = [label for label in page_labels if label]
    if labels:
        first, last = labels[0], labels[-1]
        return f"第 {first} 页" if first == last else f"第 {first}—{last} 页"
    if not pages:
        return "页码未知"
    first, last = min(pages), max(pages)
    return f"PDF 第 {first} 页" if first == last else f"PDF 第 {first}—{last} 页"


def _render_side(side: dict[str, Any], marker: str) -> str:
    prefix = escape_markdown_text(str(side.get("prefix", "")))
    changed = escape_markdown_text(str(side.get("changedText", "")))
    suffix = escape_markdown_text(str(side.get("suffix", "")))
    if marker == "replace":
        changed = f"***{changed}***"
    elif marker == "delete":
        changed = f"~~**{changed}**~~"
    else:
        changed = f"**{changed}**"

    fragments: list[str] = []
    if side.get("prefixTruncated"):
        fragments.append("…")
    if prefix:
        fragments.append(prefix)
    fragments.append(changed)
    if suffix:
        fragments.append(suffix)
    if side.get("suffixTruncated"):
        fragments.append("…")
    page_reference = _page_label(
        [str(label) for label in side.get("pageLabels", [])],
        [int(page) for page in side.get("pages", [])],
    )
    return f"`{page_reference}` " + " ".join(fragments)


def _review_marker(change: dict[str, Any]) -> str:
    return "<sub>?</sub> " if change.get("needsReview") is True else ""


def render_release_changelog(
    changelog: dict[str, Any], *, max_changes: int | None = None
) -> str:
    current = changelog["toEdition"]
    lines = [f"### {_edition_label(current)}", ""]
    previous = changelog.get("fromEdition")
    if previous is None:
        lines.append("初版发行")
        return "\n".join(lines) + "\n"

    summary = calculate_changelog_summary(changelog)
    changes = changelog.get("changes", [])
    review_count = sum(change.get("needsReview") is True for change in changes)
    lines.extend(
        [
            f"较 `{_edition_label(previous)}` 共有 **{summary['total']}** 处不同<br>",
            "",
            f"> <kbd>+ 新增</kbd> **{summary['added']}** 处<br>",
            ">",
            f"> <kbd>− 删减</kbd> **{summary['removed']}** 处<br>",
            ">",
            f"> <kbd>± 修改</kbd> **{summary['changed']}** 处",
        ]
    )
    if review_count:
        lines.extend(
            [
                "",
                f"> <sub>?</sub> 待复核 **{review_count}** 处",
            ]
        )
    displayed = changes if max_changes is None else changes[:max_changes]
    if displayed:
        lines.extend(["", "---"])
    for display_index, change in enumerate(displayed, start=1):
        lines.append("")
        review_marker = _review_marker(change)
        if change["type"] == "replace":
            lines.append(
                f"{display_index}. {review_marker}<kbd>−</kbd> "
                f"{_render_side(change['old'], 'replace')}<br>"
            )
            lines.append(
                f"   {review_marker}<kbd>+</kbd> "
                f"{_render_side(change['new'], 'replace')}"
            )
        elif change["type"] == "delete":
            lines.append(
                f"{display_index}. {review_marker}<kbd>−</kbd> "
                f"{_render_side(change['old'], 'delete')}"
            )
        else:
            lines.append(
                f"{display_index}. {review_marker}<kbd>+</kbd> "
                f"{_render_side(change['new'], 'insert')}"
            )

    if max_changes is not None and len(changes) > max_changes:
        lines.extend(
            [
                "",
                "> Release 正文仅列出前 "
                f"**{max_changes}** 处差异；完整结果见 changelog JSON。",
            ]
        )
    lines.extend(["", "---"])
    return "\n".join(lines) + "\n"
