"""Build the repository's human-readable site update archive."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from site_updates_data import load_generated_updates

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "site-updates-archive.md"
PUBLIC_SITE_URL = "https://fulinte1966.github.io/CulturalSimmer/"
GITHUB_REPOSITORY = "Fulinte1966/CulturalSimmer"
TYPE_LABELS = {
    "new_book": "新书上架",
    "book_version": "版本更新",
    "important_erratum": "重要勘误",
    "site_announcement": "本站公告",
}


def _load_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Markdown frontmatter is missing: {path}")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"Markdown frontmatter is invalid: {path}")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Markdown frontmatter must be an object: {path}")
    return data, parts[2].strip()


def _parse_datetime(value: object, context: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid publishedAt for {context}: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"publishedAt must include a timezone for {context}")
    return parsed


def _load_books(root: Path) -> dict[str, dict]:
    books: dict[str, dict] = {}
    for path in sorted((root / "src/content/books").glob("*.md")):
        data, _ = _load_frontmatter(path)
        book_id = str(data.get("id") or "").strip()
        title = str(data.get("title") or "").strip()
        editions = data.get("editions")
        if not book_id or not title or not isinstance(editions, list) or not editions:
            raise ValueError(f"Book metadata is incomplete: {path}")
        if book_id in books:
            raise ValueError(f"Duplicate book ID: {book_id}")
        books[book_id] = data
    return books


def _find_edition(book: dict, edition: int) -> dict:
    for record in book["editions"]:
        if int(record["edition"]) == edition:
            return record
    raise ValueError(f"Edition v{edition} does not exist for {book['id']}")


def _book_title(book: dict) -> str:
    return f"{book['title']}{book.get('subtitle') or ''}"


def _edition_summary(record: dict) -> str:
    year, month = str(record["editionDate"]).split("-", 1)
    return f"{int(year)} 年 {int(month)} 月第 {int(record['edition'])} 版"


def _book_url(book_id: str) -> str:
    return f"{PUBLIC_SITE_URL}books/{book_id}/"


def _automatic_entries(root: Path, books: dict[str, dict]) -> list[dict]:
    entries: list[dict] = []
    for update in load_generated_updates(root / "src/data/generated-updates.json"):
        book = books.get(update["bookId"])
        if book is None:
            raise ValueError(f"Update {update['id']} references missing book {update['bookId']}")
        is_new = update["type"] == "book-added"
        edition = (
            min(int(item["edition"]) for item in book["editions"])
            if is_new
            else int(update["edition"])
        )
        record = _find_edition(book, edition)
        entries.append(
            {
                "id": f"{'new-book' if is_new else 'book-version'}-{book['id']}-v{edition}",
                "type": "new_book" if is_new else "book_version",
                "publishedAt": _parse_datetime(update["publishedAt"], update["id"]),
                "bookId": book["id"],
                "title": _book_title(book),
                "version": f"v{edition}",
                "summary": [_edition_summary(record)],
                "url": _book_url(book["id"]),
            }
        )
    return entries


def _announcement_entries(root: Path, books: dict[str, dict]) -> list[dict]:
    entries: list[dict] = []
    for path in sorted((root / "src/content/announcements").glob("*.md")):
        data, _ = _load_frontmatter(path)
        kind = str(data.get("kind") or "site-announcement")
        summary = data.get("summary") or []
        if not isinstance(summary, list) or not all(isinstance(item, str) for item in summary):
            raise ValueError(f"Announcement summary must be a string array: {path}")
        normalized_id = re.sub(r"[^a-zA-Z0-9.-]+", "-", path.stem).lower()
        if kind == "important-erratum":
            book_id = str(data.get("bookId") or "")
            edition = int(data.get("edition") or 0)
            book = books.get(book_id)
            if book is None or edition < 1:
                raise ValueError(f"Important erratum requires a valid book and edition: {path}")
            _find_edition(book, edition)
            entry_type = "important_erratum"
            url = _book_url(book_id)
            version = f"v{edition}"
        elif kind == "site-announcement":
            book_id = None
            entry_type = "site_announcement"
            url = None
            version = None
        else:
            raise ValueError(f"Unknown announcement kind in {path}: {kind}")
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValueError(f"Announcement title must not be empty: {path}")
        entries.append(
            {
                "id": f"{'erratum' if entry_type == 'important_erratum' else 'announcement'}-{normalized_id}",
                "type": entry_type,
                "publishedAt": _parse_datetime(data.get("publishedAt"), path.name),
                "bookId": book_id,
                "title": title,
                "version": version,
                "summary": summary,
                "url": url,
            }
        )
    return entries


def build_archive_entries(root: Path = ROOT) -> list[dict]:
    books = _load_books(root)
    entries = [
        *_automatic_entries(root, books),
        *_announcement_entries(root, books),
    ]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Site update archive contains duplicate IDs")
    return sorted(
        entries,
        key=lambda entry: (entry["publishedAt"], entry["id"]),
        reverse=True,
    )


def _escape_markdown(value: object) -> str:
    text = (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\\", "\\\\")
    )
    for character in ("[", "]", "*", "_", "`", "~"):
        text = text.replace(character, f"\\{character}")
    return text


def _format_date(value: datetime) -> str:
    local = value.astimezone(ZoneInfo("Asia/Shanghai"))
    return f"{local.year} 年 {local.month} 月 {local.day} 日"


def render_site_updates_archive(entries: list[dict]) -> str:
    lines = [
        "# 本站更新归档",
        "",
        "> 本文件由仓库中的自动更新记录和人工公告生成，请勿手动编辑。",
        "> 网站首页仅展示置顶消息和最近动态；正式电子书版本记录以书目详情页和 GitHub Releases 为准。",
    ]
    if not entries:
        lines.extend(["", "暂无更新记录。"])
        return "\n".join(lines) + "\n"
    for entry in entries:
        lines.extend(
            [
                "",
                "---",
                "",
                f"## {_format_date(entry['publishedAt'])}　［{TYPE_LABELS[entry['type']]}］",
                "",
            ]
        )
        subject = _escape_markdown(entry["title"])
        if entry.get("bookId"):
            subject = f"{_escape_markdown(entry['bookId'])}　《{subject}》"
        if entry.get("url"):
            lines.append(f"### [{subject}]({entry['url']})")
        else:
            lines.append(f"### {subject}")
        if entry.get("version"):
            lines.extend(["", f"**版本：** `{entry['version']}`"])
        if entry["summary"]:
            lines.append("")
            lines.extend(f"- {_escape_markdown(item)}" for item in entry["summary"])
        lines.extend(["", f"<!-- update-id: {entry['id']} -->"])
    return "\n".join(lines) + "\n"


def build_site_updates_archive(
    root: Path = ROOT, *, output_path: Path | None = None, check: bool = False
) -> Path:
    target = output_path or root / DEFAULT_OUTPUT.relative_to(ROOT)
    markdown = render_site_updates_archive(build_archive_entries(root))
    if check:
        if not target.is_file() or target.read_text(encoding="utf-8") != markdown:
            raise ValueError(f"Site update archive is out of date: {target}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(markdown)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        target = build_site_updates_archive(check=args.check)
    except (OSError, ValueError) as error:
        print(f"Site update archive build failed: {error}")
        return 1
    print(f"{'Checked' if args.check else 'Generated'} {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
