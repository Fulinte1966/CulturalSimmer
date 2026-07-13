"""Build one aggregate GitHub Markdown changelog for every book."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from changelog_model import normalize_changelog
from render_release_changelog import render_release_changelog


ROOT = Path(__file__).resolve().parents[1]
GITHUB_REPOSITORY = "Fulinte1966/CulturalSimmer"


def _load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid book frontmatter: {path}")
    _, frontmatter, _ = text.split("---", 2)
    value = yaml.safe_load(frontmatter)
    if not isinstance(value, dict):
        raise ValueError(f"Book frontmatter must be an object: {path}")
    return value


def _release_tag(book_id: str, edition: dict[str, Any]) -> str:
    return str(edition.get("releaseTag") or f"{book_id}_v{edition['edition']}")


def _load_edition_changelog(
    root: Path,
    book_id: str,
    edition: dict[str, Any],
) -> dict[str, Any]:
    tag = _release_tag(book_id, edition)
    path = root / "src" / "data" / "changelogs" / f"{tag}.changelog.json"
    if path.is_file():
        changelog = normalize_changelog(
            json.loads(path.read_text(encoding="utf-8"))
        )
        if changelog["bookId"] != book_id:
            raise ValueError(f"Changelog bookId does not match {tag}")
        if int(changelog["toEdition"]["edition"]) != int(edition["edition"]):
            raise ValueError(f"Changelog edition does not match {tag}")
        return changelog

    if int(edition["edition"]) != 1:
        raise ValueError(f"Missing repository changelog: {path}")
    return {
        "schemaVersion": 1,
        "bookId": book_id,
        "fromEdition": None,
        "toEdition": {
            "edition": 1,
            "editionDate": str(edition["editionDate"]),
        },
        "changes": [],
    }


def render_book_changelog(root: Path, book_path: Path) -> tuple[str, str]:
    book = _load_frontmatter(book_path)
    book_id = str(book.get("id") or "")
    title = str(book.get("title") or "")
    editions = book.get("editions")
    if not book_id or not title:
        raise ValueError(f"Book must define id and title: {book_path}")
    if not isinstance(editions, list) or not editions:
        raise ValueError(f"Book must define editions: {book_path}")

    ordered = sorted(editions, key=lambda item: int(item["edition"]), reverse=True)
    blocks: list[str] = []
    for edition in ordered:
        tag = _release_tag(book_id, edition)
        release_url = f"https://github.com/{GITHUB_REPOSITORY}/releases/tag/{tag}"
        changelog = _load_edition_changelog(root, book_id, edition)
        blocks.append(
            "\n".join(
                [
                    f"## [{tag}]({release_url})",
                    "",
                    render_release_changelog(changelog).rstrip(),
                ]
            )
        )
    return book_id, "\n\n".join(blocks) + "\n"


def build_repository_changelogs(root: Path = ROOT, *, check: bool = False) -> list[Path]:
    books_dir = root / "src" / "content" / "books"
    output_dir = root / "src" / "data" / "changelogs"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for book_path in sorted(books_dir.glob("*.md")):
        book_id, markdown = render_book_changelog(root, book_path)
        output_path = output_dir / f"{book_id}.md"
        if check:
            if not output_path.is_file() or output_path.read_text(
                encoding="utf-8"
            ) != markdown:
                raise ValueError(f"Aggregate changelog is out of date: {output_path}")
        else:
            output_path.write_text(markdown, encoding="utf-8")
        generated.append(output_path)
    return generated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        generated = build_repository_changelogs(check=args.check)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Book changelog build failed: {error}", file=sys.stderr)
        return 1
    action = "Checked" if args.check else "Generated"
    print(f"{action} {len(generated)} aggregate book changelog(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
