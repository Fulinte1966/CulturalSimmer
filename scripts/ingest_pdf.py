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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


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
    opts = ap.parse_args(args)

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
        if existing.get("edition") == meta.edition:
            raise SystemExit(f"Book entry {md_path} already has edition {meta.edition}")

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
        "description": meta.description,
        "tags": meta.tags,
        "language": meta.language,
        "date": published_at[:10],
        "series": meta.series,
        "volume": meta.volume,
        "total_volumes": meta.total_volumes,
        "readtime": meta.readtime,
        "publisher": meta.publisher,
        "source": meta.source,
        "rights": meta.rights,
        "license_url": meta.license_url,
        "canonical_tag": tag,
        "canonical_filename": filename,
        "source_release_id": int(opts.release_id),
        "source_asset_id": int(matching_assets[0]["id"]),
        "source_release_tag": opts.release_tag,
        "source_sha256": sha,
        "source_pdf_path": str(pdf_path),
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
    pdf_path = Path(meta["source_pdf_path"])

    # Markdown entry
    date_str = meta.get("date", "")
    tags = meta.get("tags") or []

    frontmatter = {
        "id": id_,
        "title": meta["title"],
        "edition": edition,
        "date": date_str,
        "tags": tags,
    }
    for opt in (
        "subtitle",
        "author",
        "total_volumes",
        "readtime",
        "series",
        "publisher",
        "source",
        "rights",
        "license_url",
        "language",
    ):
        if meta.get(opt) is not None:
            frontmatter[opt] = meta[opt]

    yaml_text = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    md_content = f"---\n{yaml_text}---\n\n{meta.get('description', '')}\n"
    md_path = ROOT / "src" / "content" / "books" / f"{id_}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written {md_path}")

    # Manifest
    manifest_dir = ROOT / "src" / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "id": id_,
        "edition": edition,
        "source_release_id": meta["source_release_id"],
        "source_asset_id": meta["source_asset_id"],
        "source_sha256": meta["source_sha256"],
        "canonical_tag": meta["canonical_tag"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
                "license_url",
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

    # Cover / spine / outline / reading via book_assets.py
    from book_assets import extract_book_assets
    extract_book_assets(pdf_path, id_, edition, ROOT)
    print("Assets generated via book_assets")

    # Summary stub
    summary_lines = [
        f"## Ingest {id_} edition {edition}",
        f"- SHA-256: `{meta['source_sha256']}`",
        f"- Canonical tag: `{meta['canonical_tag']}`",
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
    pdf_path = Path(meta["source_pdf_path"])
    normalized_pdf = Path(opts.workspace) / meta["canonical_filename"]
    if pdf_path.resolve() != normalized_pdf.resolve():
        shutil.copyfile(pdf_path, normalized_pdf)

    # Create canonical Release
    _gh(
        "release", "create", meta["canonical_tag"],
        normalized_pdf.resolve().as_posix(),
        "--title", f"{meta['title']} (v{meta['edition']})",
        "--notes", f"Automated intake of {meta['canonical_filename']}",
    )
    print(f"Canonical Release {meta['canonical_tag']} created")


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
                    meta["canonical_tag"],
                    "--yes",
                    "--cleanup-tag",
                )
                print(f"Rolled back canonical Release {meta['canonical_tag']}")
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
