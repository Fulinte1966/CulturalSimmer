"""Generate a structured PDF edition changelog and GitHub Release Markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from compare_content_snapshots import compare_content_snapshots
from extract_content_snapshot import extract_content_snapshot, write_snapshot
from render_release_changelog import render_release_changelog


def _write_text(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _validate_pdf_identity(
    pdf_path: Path,
    *,
    book_id: str,
    edition: int,
    edition_date: str,
) -> None:
    from extract_metadata import MetadataError, extract

    try:
        metadata = extract(pdf_path)
    except (ValueError, MetadataError) as exc:
        raise ValueError(f"PDF metadata validation failed for {pdf_path}: {exc}") from exc
    if metadata.id != book_id:
        raise ValueError(f"PDF book ID mismatch: {metadata.id} != {book_id}")
    if metadata.edition != edition:
        raise ValueError(f"PDF edition mismatch: {metadata.edition} != {edition}")
    if metadata.edition_date != edition_date:
        raise ValueError(
            f"PDF edition date mismatch: {metadata.edition_date} != {edition_date}"
        )


def generate_release_changelog(
    *,
    new_pdf: Path,
    book_id: str,
    new_edition: int,
    new_edition_date: str,
    output_json: Path,
    output_markdown: Path,
    old_pdf: Path | None = None,
    old_edition: int | None = None,
    old_edition_date: str | None = None,
    force: bool = False,
    debug: bool = False,
    max_changes: int = 200,
    max_tokens: int = 400_000,
    timeout_seconds: int = 30,
    exclude_cover: bool = True,
) -> dict[str, Any]:
    if old_pdf is not None and (old_edition is None or old_edition_date is None):
        raise ValueError("Old edition and edition date are required with --old-pdf")
    if old_pdf is None and (old_edition is not None or old_edition_date is not None):
        raise ValueError("--old-edition and --old-edition-date require --old-pdf")
    if max_changes < 0:
        raise ValueError("--max-changes must be zero or greater")
    if max_tokens < 1 or timeout_seconds < 1:
        raise ValueError("Comparison limits must be positive")
    for output in (output_json, output_markdown):
        if output.exists() and not force:
            raise FileExistsError(f"Output already exists: {output}")

    _validate_pdf_identity(
        new_pdf,
        book_id=book_id,
        edition=new_edition,
        edition_date=new_edition_date,
    )
    if old_pdf is not None:
        _validate_pdf_identity(
            old_pdf,
            book_id=book_id,
            edition=int(old_edition),
            edition_date=str(old_edition_date),
        )

    new_snapshot = extract_content_snapshot(
        new_pdf,
        book_id=book_id,
        edition=new_edition,
        edition_date=new_edition_date,
        exclude_cover=exclude_cover,
    )
    old_snapshot = None
    if old_pdf is not None:
        old_snapshot = extract_content_snapshot(
            old_pdf,
            book_id=book_id,
            edition=int(old_edition),
            edition_date=str(old_edition_date),
            exclude_cover=exclude_cover,
        )

    changelog = compare_content_snapshots(
        old_snapshot,
        new_snapshot,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )
    _write_text(
        output_json,
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
        force=force,
    )
    _write_text(
        output_markdown,
        render_release_changelog(changelog, max_changes=max_changes),
        force=force,
    )

    if debug:
        base = output_json.with_suffix("")
        write_snapshot(
            base.with_name(f"{base.name}.new.content.json.gz"),
            new_snapshot,
            force=force,
        )
        if old_snapshot is not None:
            write_snapshot(
                base.with_name(f"{base.name}.old.content.json.gz"),
                old_snapshot,
                force=force,
            )
    return changelog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-pdf")
    parser.add_argument("--new-pdf", required=True)
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--old-edition", type=int)
    parser.add_argument("--new-edition", required=True, type=int)
    parser.add_argument("--old-edition-date")
    parser.add_argument("--new-edition-date", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--max-changes", type=int, default=200)
    parser.add_argument("--max-tokens", type=int, default=400_000)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--include-cover", action="store_true")
    args = parser.parse_args(argv)

    try:
        generate_release_changelog(
            new_pdf=Path(args.new_pdf),
            book_id=args.book_id,
            new_edition=args.new_edition,
            new_edition_date=args.new_edition_date,
            output_json=Path(args.output_json),
            output_markdown=Path(args.output_markdown),
            old_pdf=Path(args.old_pdf) if args.old_pdf else None,
            old_edition=args.old_edition,
            old_edition_date=args.old_edition_date,
            force=args.force,
            debug=args.debug,
            max_changes=args.max_changes,
            max_tokens=args.max_tokens,
            timeout_seconds=args.timeout_seconds,
            exclude_cover=not args.include_cover,
        )
    except (FileExistsError, OSError, RuntimeError, ValueError) as exc:
        print(f"Changelog generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
