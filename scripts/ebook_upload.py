"""Local preflight and temporary Release upload for ebook PDFs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from edition_policy import check_expected_edition, format_edition_check_lines
from extract_metadata import MetadataError, extract
from ingest_pdf import ROOT, _load_classifications


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def _gh(*args: str, check: bool = True) -> str:
    return _run(["gh", *args], check=check).stdout.strip()


def _ensure_gh_auth() -> None:
    result = _run(["gh", "auth", "status"], check=False)
    if result.returncode != 0:
        raise SystemExit("GitHub CLI is not logged in. Please run: gh auth login")


def _remote_release_exists(tag: str) -> bool:
    return _run(["gh", "release", "view", tag], check=False).returncode == 0


def _remote_tag_exists(tag: str) -> bool:
    result = _run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        check=False,
    )
    return bool(result.stdout.strip())


def _local_path_conflicts(tag: str) -> list[str]:
    candidates = (
        ROOT / "src" / "data" / "manifests" / f"{tag}.json",
        ROOT / "src" / "data" / "outlines" / f"{tag}.json",
        ROOT / "src" / "data" / "reading" / f"{tag}.json",
        ROOT / "src" / "data" / "changelogs" / f"{tag}.changelog.json",
        ROOT / "public" / "covers" / f"{tag}.png",
        ROOT / "public" / "covers" / f"{tag}_spine.png",
    )
    return [str(path.relative_to(ROOT)) for path in candidates if path.exists()]


def _print_summary(
    *,
    title: str,
    book_id: str,
    edition: int,
    description: str,
    pdf_create_date: str,
    edition_date: str,
    canonical_tag: str,
    canonical_filename: str,
    ingest_tag: str,
    pdf_path: Path,
    edition_lines: list[str],
    conflicts: list[str],
) -> None:
    print("=== Ebook Upload Preflight ===")
    print(f"书名：{title}")
    print(f"索书号：{book_id}")
    print(f"版次：{edition}")
    print(f"内容提要：{description[:80]}")
    print(f"PDF 创建日期：{pdf_create_date}")
    print(f"editionDate：{edition_date}")
    print(f"正式 tag：{canonical_tag}")
    print(f"正式 PDF 文件名：{canonical_filename}")
    print(f"临时 ingest tag：{ingest_tag}")
    print(f"将要上传的 PDF 路径：{pdf_path}")
    print("")
    for line in edition_lines:
        print(line)
    print("")
    if conflicts:
        print("重复检查：失败")
        for item in conflicts:
            print(f"- {item}")
    else:
        print("重复检查：通过")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--allow-edition-skip", action="store_true")
    args = parser.parse_args(argv)

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise SystemExit("Input file must be a .pdf")

    try:
        meta = extract(pdf_path, _load_classifications())
    except (ValueError, MetadataError) as exc:
        raise SystemExit(f"Metadata validation failed: {exc}") from exc

    _ensure_gh_auth()

    canonical_tag = f"{meta.id}_v{meta.edition}"
    canonical_filename = f"{canonical_tag}.pdf"
    ingest_tag = f"ingest-{datetime.now():%Y%m%d}-{meta.id}-v{meta.edition}"

    edition_check = check_expected_edition(
        ROOT,
        meta.id,
        meta.edition,
        allow_edition_skip=args.allow_edition_skip,
    )
    conflicts: list[str] = []
    if _remote_release_exists(canonical_tag):
        conflicts.append(f"Canonical Release already exists: {canonical_tag}")
    if _remote_tag_exists(canonical_tag):
        conflicts.append(f"Canonical Git tag already exists: {canonical_tag}")
    if _remote_release_exists(ingest_tag):
        conflicts.append(f"Temporary ingest Release already exists: {ingest_tag}")
    if _remote_tag_exists(ingest_tag):
        conflicts.append(f"Temporary ingest Git tag already exists: {ingest_tag}")
    conflicts.extend(_local_path_conflicts(canonical_tag))

    _print_summary(
        title=meta.title,
        book_id=meta.id,
        edition=meta.edition,
        description=meta.description,
        pdf_create_date=meta.pdf_create_date,
        edition_date=meta.edition_date,
        canonical_tag=canonical_tag,
        canonical_filename=canonical_filename,
        ingest_tag=ingest_tag,
        pdf_path=pdf_path,
        edition_lines=format_edition_check_lines(edition_check),
        conflicts=conflicts,
    )

    if not edition_check.ok:
        raise SystemExit(1)
    if conflicts:
        raise SystemExit(1)
    if args.dry_run:
        return 0

    release_args = [
        "release",
        "create",
        ingest_tag,
        str(pdf_path),
        "--title",
        ingest_tag,
        "--notes",
        (
            f"Temporary ingest release for {meta.id} v{meta.edition}\n"
            f"Allow-Edition-Skip: {str(args.allow_edition_skip).lower()}"
        ),
    ]
    if args.draft:
        release_args.append("--draft")

    _gh(*release_args)
    print(f"Temporary ingest Release created: {ingest_tag}")
    if args.draft:
        print("Draft mode enabled; publish the Release manually to trigger ingest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
