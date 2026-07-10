"""Render a structured electronic-book changelog as GitHub Markdown."""

from __future__ import annotations

from typing import Any


def escape_markdown_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for character in ("*", "_", "~", "`"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped.replace("<", "&lt;").replace(">", "&gt;")


def _edition_label(edition: dict[str, Any]) -> str:
    year, month = str(edition["editionDate"]).split("-", 1)
    return f"{int(year)} 年 {int(month)} 月第 {int(edition['edition'])} 版"


def _page_label(pages: list[int]) -> str:
    if not pages:
        return "页码未知"
    first, last = min(pages), max(pages)
    return f"第 {first} 页" if first == last else f"第 {first}—{last} 页"


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

    leading = "… " if side.get("prefixTruncated") else ""
    trailing = " …" if side.get("suffixTruncated") else ""
    return (
        f"`{_page_label([int(page) for page in side.get('pages', [])])}` "
        f"{leading}{prefix}{changed}{suffix}{trailing}"
    ).rstrip()


def render_release_changelog(
    changelog: dict[str, Any], *, max_changes: int | None = None
) -> str:
    current = changelog["toEdition"]
    lines = [f"### {_edition_label(current)}", "", "---", ""]
    previous = changelog.get("fromEdition")
    if previous is None:
        lines.append("初次发布。")
        return "\n".join(lines) + "\n"

    summary = changelog["summary"]
    lines.extend(
        [
            f"较 `{_edition_label(previous)}` 共有 **{summary['total']}** 处不同<br>",
            "",
            f"> <kbd>+ 新增</kbd> **{summary['added']}** 处<br>",
            ">",
            f"> <kbd>− 删减</kbd> **{summary['removed']}** 处<br>",
            ">",
            f"> <kbd>± 修改</kbd> **{summary['changed']}** 处",
            "",
            "---",
        ]
    )

    changes = changelog.get("changes", [])
    displayed = changes if max_changes is None else changes[:max_changes]
    for display_index, change in enumerate(displayed, start=1):
        lines.append("")
        if change["type"] == "replace":
            lines.append(
                f"{display_index}. <kbd>−</kbd> "
                f"{_render_side(change['old'], 'replace')}<br>"
            )
            lines.append(
                f"   <kbd>+</kbd> {_render_side(change['new'], 'replace')}"
            )
        elif change["type"] == "delete":
            lines.append(
                f"{display_index}. <kbd>−</kbd> "
                f"{_render_side(change['old'], 'delete')}"
            )
        else:
            lines.append(
                f"{display_index}. <kbd>+</kbd> "
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
    return "\n".join(lines) + "\n"
