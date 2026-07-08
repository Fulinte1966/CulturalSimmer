"""PDF ingestion orchestration for GitHub Actions.

Called by ``.github/workflows/ingest-pdf.yml``.  Subcommands:

    validate   — download + extract + validate → JSON metadata
    generate   — produce Markdown / covers / spine / outline / reading
    publish    — create canonical GitHub Release
    cleanup    — remove temporary Release and tag
    commit-message  — print formatted commit message
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from edition_policy import check_expected_edition, format_edition_check_lines

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _dump_frontmatter(data: dict) -> str:
    return yaml.dump(
        data,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def _run(cmd: list[str], **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def _gh(*args: str):
    return _run(["gh", *args], capture_output=True).stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_classifications() -> dict[str, str]:
    path = ROOT / "src" / "data" / "classifications.yml"
    data = yaml.safe_load(path.read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("classifications.yml must contain a mapping")
    return {str(key): str(value) for key, value in data.items()}


def _load_frontmatter(path: Path) -> dict:
    text = path.read_text("utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid frontmatter in {path}")
    _, frontmatter, _ = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid frontmatter in {path}")
    return data


def _load_markdown_parts(path: Path) -> tuple[dict, str]:
    text = path.read_text("utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Invalid frontmatter in {path}")
    _, frontmatter, body = text.split("---", 2)
    data = yaml.safe_load(frontmatter)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid frontmatter in {path}")
    return data, body.strip()


def _month_to_date(month: str) -> str:
    return f"{month}-01"


def _merge_edition_record(frontmatter: dict, meta: dict) -> list[dict]:
    existing: list[dict] = []

    raw_editions = frontmatter.get("editions")
    if isinstance(raw_editions, list):
        for item in raw_editions:
            if isinstance(item, dict) and isinstance(item.get("edition"), int):
                existing.append(dict(item))

    edition = int(meta["edition"])
    if any(item["edition"] == edition for item in existing):
        raise SystemExit(f"Book entry already contains edition {edition}")

    existing.append(
        {
            "edition": edition,
            "editionDate": meta["editionDate"],
            "releaseTag": meta["canonicalTag"],
            "manifest": f"src/data/manifests/{meta['canonicalTag']}.json",
        }
    )
    return sorted(existing, key=lambda item: item["edition"])


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def cmd_validate(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--release-id", required=True)
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--allow-edition-skip", action="store_true")
    opts = ap.parse_args(args)

    if not opts.release_tag.startswith("ingest-"):
        raise SystemExit("Intake Release tag must start with ingest-")

    ws = Path(opts.workspace)
    pdfs = sorted(ws.glob("*.pdf"))
    if len(pdfs) != 1:
        raise SystemExit(f"Expected exactly 1 PDF, found {len(pdfs)}")

    pdf_path = pdfs[0]
    sha = _sha256(pdf_path)

    release = json.loads(
        _gh("api", f"repos/:owner/:repo/releases/{int(opts.release_id)}")
    )
    matching_assets = [
        asset for asset in release.get("assets", [])
        if asset.get("name") == pdf_path.name
    ]
    if len(matching_assets) != 1:
        raise SystemExit("Unable to identify the source PDF asset")
    published_at = release.get("published_at")
    if not published_at:
        raise SystemExit("Intake Release has no publication timestamp")

    # Extract metadata via shared extract_metadata module
    from extract_metadata import extract, MetadataError
    try:
        meta = extract(pdf_path, _load_classifications())
    except (ValueError, MetadataError) as exc:
        raise SystemExit(f"Metadata validation failed: {exc}")

    tag = f"{meta.id}_v{meta.edition}"
    filename = f"{tag}.pdf"

    allow_edition_skip = opts.allow_edition_skip or os.environ.get(
        "ALLOW_EDITION_SKIP", ""
    ).lower() in {"1", "true", "yes"}
    edition_check = check_expected_edition(
        ROOT,
        meta.id,
        meta.edition,
        allow_edition_skip=allow_edition_skip,
    )
    for line in format_edition_check_lines(edition_check):
        print(line)
    if not edition_check.ok:
        raise SystemExit(f"Edition validation failed: {edition_check.message}")

    # Dedup checks
    try:
        _gh("release", "view", tag)
        raise SystemExit(f"Canonical Release {tag} already exists")
    except subprocess.CalledProcessError:
        pass  # expected — Release does not exist yet

    remote_tag = _run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        capture_output=True,
    ).stdout.strip()
    if remote_tag:
        raise SystemExit(f"Canonical Git tag {tag} already exists")

    def _exists(path: Path) -> bool:
        return path.exists()

    md_path = ROOT / "src" / "content" / "books" / f"{meta.id}.md"
    if _exists(md_path):
        existing = _load_frontmatter(md_path)
        if existing.get("title") and existing.get("title") != meta.title:
            raise SystemExit(
                f"Book title mismatch: existing {existing.get('title')} != PDF {meta.title}"
            )

    duplicate_paths = (
        ROOT / "src" / "data" / "manifests" / f"{tag}.json",
        ROOT / "public" / "covers" / f"{tag}.png",
        ROOT / "public" / "covers" / f"{tag}_spine.png",
        ROOT / "src" / "data" / "outlines" / f"{tag}.json",
        ROOT / "src" / "data" / "reading" / f"{tag}.json",
    )
    existing_paths = [
        str(path.relative_to(ROOT)) for path in duplicate_paths if path.exists()
    ]
    if existing_paths:
        raise SystemExit(
            f"Canonical generated assets already exist: {', '.join(existing_paths)}"
        )

    result = {
        "id": meta.id,
        "title": meta.title,
        "subtitle": meta.subtitle,
        "author": meta.author,
        "edition": meta.edition,
        "editionDate": meta.edition_date,
        "editionDateSource": meta.edition_date_source,
        "pdfCreateDate": meta.pdf_create_date,
        "description": meta.description,
        "tags": meta.tags,
        "language": meta.language,
        "date": _month_to_date(meta.edition_date),
        "sourcePublishedAt": published_at,
        "series": meta.series,
        "volume": meta.volume,
        "totalVolumes": meta.total_volumes,
        "publisher": meta.publisher,
        "source": meta.source,
        "rights": meta.rights,
        "licenseUrl": meta.license_url,
        "canonicalTag": tag,
        "canonicalFilename": filename,
        "sourceReleaseId": int(opts.release_id),
        "sourceAssetId": int(matching_assets[0]["id"]),
        "sourceReleaseTag": opts.release_tag,
        "sourceSha256": sha,
        "sourcePdfPath": str(pdf_path),
    }
    Path(opts.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Validation OK: {tag}")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def cmd_generate(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--workspace", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    id_ = meta["id"]
    edition = meta["edition"]
    pdf_path = Path(meta["sourcePdfPath"])
    tag = meta["canonicalTag"]

    # Cover / spine / outline / reading via book_assets.py
    from book_assets import extract_book_assets
    asset_paths = extract_book_assets(pdf_path, id_, edition, ROOT)
    print("Assets generated via book_assets")

    reading = json.loads(asset_paths["reading"].read_text(encoding="utf-8"))
    page_count = reading.get("pageCount")
    word_count = (reading.get("cjkCharacterCount") or 0) + (
        reading.get("latinTokenCount") or 0
    )

    # Markdown entry
    tags = meta.get("tags") or []

    md_path = ROOT / "src" / "content" / "books" / f"{id_}.md"
    existing_frontmatter: dict = {}
    if md_path.exists():
        existing_frontmatter, _ = _load_markdown_parts(md_path)

    frontmatter: dict = {
        "id": id_,
        "title": meta["title"],
        "description": meta["description"],
        "tags": tags,
    }
    for opt in (
        "subtitle",
        "author",
        "totalVolumes",
        "series",
        "publisher",
        "source",
        "rights",
        "licenseUrl",
        "language",
    ):
        if meta.get(opt) is not None:
            frontmatter[opt] = meta[opt]
    frontmatter["editions"] = _merge_edition_record(existing_frontmatter, meta)

    yaml_text = _dump_frontmatter(frontmatter)
    md_content = f"---\n{yaml_text}---\n\n{meta.get('description', '')}\n"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written {md_path}")

    # Manifest
    manifest_dir = ROOT / "src" / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schemaVersion": 2,
        "bookId": id_,
        "title": meta["title"],
        "edition": edition,
        "editionDate": meta["editionDate"],
        "editionDateSource": meta["editionDateSource"],
        "pdfCreateDate": meta["pdfCreateDate"],
        "description": meta["description"],
        "creator": meta.get("author"),
        "language": meta.get("language") or "zh-CN",
        "releaseTag": meta["canonicalTag"],
        "pdfFilename": meta["canonicalFilename"],
        "downloadUrl": (
            "https://github.com/"
            f"{os.environ.get('GITHUB_REPOSITORY', 'Fulinte1966/CulturalSimmer')}"
            f"/releases/download/{meta['canonicalTag']}/{meta['canonicalFilename']}"
        ),
        "githubAssetDigest": None,
        "bytes": pdf_path.stat().st_size,
        "pageCount": page_count,
        "wordCount": word_count,
        "sourceReleaseId": meta["sourceReleaseId"],
        "sourceAssetId": meta["sourceAssetId"],
        "sourceSha256": meta["sourceSha256"],
        "canonicalTag": meta["canonicalTag"],
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            key: meta.get(key)
            for key in (
                "title",
                "subtitle",
                "author",
                "language",
                "series",
                "publisher",
                "source",
                "rights",
                "licenseUrl",
            )
            if meta.get(key) is not None
        },
    }
    manifest_path = manifest_dir / f"{id_}_v{edition}.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Written {manifest_path}")

    # Summary stub
    summary_lines = [
        f"## Ingest {id_} edition {edition}",
        f"- SHA-256: `{meta['sourceSha256']}`",
        f"- Canonical tag: `{meta['canonicalTag']}`",
        f"- Entry: `{md_path.relative_to(ROOT)}`",
    ]
    (ROOT / "_ingest_summary.md").write_text("\n".join(summary_lines))


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------

def cmd_publish(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--workspace", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    pdf_path = Path(meta["sourcePdfPath"])
    normalized_pdf = Path(opts.workspace) / meta["canonicalFilename"]
    if pdf_path.resolve() != normalized_pdf.resolve():
        shutil.copyfile(pdf_path, normalized_pdf)

    # Create canonical Release
    _gh(
        "release", "create", meta["canonicalTag"],
        normalized_pdf.resolve().as_posix(),
        "--title", f"{meta['title']} (v{meta['edition']})",
        "--notes", f"Automated intake of {meta['canonicalFilename']}",
    )
    digest = None
    release_json = _gh("api", f"repos/:owner/:repo/releases/tags/{meta['canonicalTag']}")
    if release_json:
        release = json.loads(release_json)
        for asset in release.get("assets", []):
            if asset.get("name") == meta["canonicalFilename"]:
                digest = asset.get("digest")
                break

    manifest_path = ROOT / "src" / "data" / "manifests" / f"{meta['canonicalTag']}.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["githubAssetDigest"] = digest
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Canonical Release {meta['canonicalTag']} created")


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

def cmd_cleanup(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata")
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--push-success", required=True)
    opts = ap.parse_args(args)

    push_succeeded = opts.push_success.lower() == "true"
    if push_succeeded:
        try:
            _gh("release", "delete", opts.release_tag, "--yes")
            _gh("api", f"repos/:owner/:repo/git/refs/tags/{opts.release_tag}",
                "-X", "DELETE")
            print(f"Temporary Release {opts.release_tag} deleted")
        except subprocess.CalledProcessError as exc:
            print(f"Warning: cleanup failed: {exc}")
    else:
        if opts.metadata and Path(opts.metadata).exists():
            meta = json.loads(Path(opts.metadata).read_text("utf-8"))
            try:
                _gh(
                    "release",
                    "delete",
                    meta["canonicalTag"],
                    "--yes",
                    "--cleanup-tag",
                )
                print(f"Rolled back canonical Release {meta['canonicalTag']}")
            except subprocess.CalledProcessError:
                pass
        print(f"Push did not succeed; keeping {opts.release_tag} for inspection")


# ---------------------------------------------------------------------------
# commit-message
# ---------------------------------------------------------------------------

def cmd_commit_message(args: list[str]):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True)
    opts = ap.parse_args(args)

    meta = json.loads(Path(opts.metadata).read_text("utf-8"))
    print(f"content: ingest {meta['id']} edition {meta['edition']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "validate": cmd_validate,
    "generate": cmd_generate,
    "publish": cmd_publish,
    "cleanup": cmd_cleanup,
    "commit-message": cmd_commit_message,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS)}> [...]", file=sys.stderr)
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
