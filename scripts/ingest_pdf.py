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
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

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
    result: dict[str, str] = {}
    for line in path.read_text("utf-8").splitlines():
        m = line.strip().match(r"^([A-Z](?:\d+(?:\.\d+)?)?):\s*(.+)$",
                               line.strip())
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


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

    def _exists(path: Path) -> bool:
        return path.exists()

    md_path = ROOT / "src" / "content" / "books" / f"{meta.id}.md"
    if _exists(md_path):
        raise SystemExit(f"Book entry {md_path} already exists")

    result = {
        "id": meta.id,
        "title": meta.title,
        "subtitle": meta.subtitle,
        "author": meta.author,
        "edition": meta.edition,
        "description": meta.description,
        "tags": meta.tags,
        "language": meta.language,
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
    for opt in ("subtitle", "author", "total_volumes", "readtime"):
        if meta.get(opt) is not None:
            frontmatter[opt] = meta[opt]

    md_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            md_lines.append(f"{k}:")
            for item in v:
                md_lines.append(f"  - {item}")
        elif isinstance(v, int):
            md_lines.append(f"{k}: {v}")
        else:
            md_lines.append(f"{k}: {v}")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(meta.get("description", ""))

    md_content = "\n".join(md_lines)
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
        "source_sha256": meta["source_sha256"],
        "canonical_tag": meta["canonical_tag"],
        "generated_at": "",
    }
    manifest_path = manifest_dir / f"{id_}_v{edition}.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Written {manifest_path}")

    # Cover / spine / outline / reading via book_assets.py
    try:
        from book_assets import extract_book_assets
        extract_book_assets(pdf_path, id_, edition, ROOT)
        print("Assets generated via book_assets")
    except Exception as exc:
        print(f"Warning: book_assets failed ({exc}); asset generation skipped")

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

    # Create canonical Release
    _gh(
        "release", "create", meta["canonical_tag"],
        pdf_path.resolve().as_posix(),
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
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--push-success", required=True)
    opts = ap.parse_args(args)

    if opts.push_success == "True" or opts.push_success == "true":
        try:
            _gh("release", "delete", opts.release_tag, "--yes")
            _gh("api", f"repos/:owner/:repo/git/refs/tags/{opts.release_tag}",
                "-X", "DELETE")
            print(f"Temporary Release {opts.release_tag} deleted")
        except subprocess.CalledProcessError as exc:
            print(f"Warning: cleanup failed: {exc}")
    else:
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
