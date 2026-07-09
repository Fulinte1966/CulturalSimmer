#!/usr/bin/env python3
"""Generate WOFF2 web-font subsets from the repository's source fonts."""

from __future__ import annotations

import argparse
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "tools" / "font-sources"
OUTPUT_DIR = ROOT / "public" / "fonts" / "subset"
TEXT_SOURCES = ("src", "public/assets", "dist")
TEXT_SUFFIXES = {
    ".astro",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".svg",
    ".ts",
    ".txt",
    ".yml",
}
LATIN_UNICODES = (
    "U+0020-007E,"
    "U+00A0-00FF,"
    "U+20A0-20CF,"
    "U+2100-214F,"
    "U+2150-218F,"
    "U+FF10-FF19,"
    "U+FF21-FF3A,"
    "U+FF41-FF5A"
)
@dataclass(frozen=True)
class FontJob:
    source: str
    output: str
    mode: str


FONT_JOBS = [
    FontJob("texgyretermes-regular.otf", "texgyretermes-regular.latin.woff2", "latin"),
    FontJob("texgyretermes-bold.otf", "texgyretermes-bold.latin.woff2", "latin"),
    FontJob("ChillJinshuSongRegular.otf", "chill-jinshu-song-regular.zh.woff2", "cjk"),
    FontJob("ChillJinshuSongMedium.otf", "chill-jinshu-song-medium.zh.woff2", "cjk"),
    FontJob("ChillJinshuSongBold.otf", "chill-jinshu-song-bold.zh.woff2", "cjk"),
    FontJob("ChillJinshuSong_CompactRegular.otf", "chill-jinshu-song-compact-regular.zh.woff2", "cjk"),
    FontJob("ChillJinshuSong_CompactBold.otf", "chill-jinshu-song-compact-bold.zh.woff2", "cjk"),
    FontJob("ChillJinshuSong_WideRegular.otf", "chill-jinshu-song-wide-regular.zh.woff2", "cjk"),
    FontJob("ChillJinshuSong_WideBold.otf", "chill-jinshu-song-wide-bold.zh.woff2", "cjk"),
    FontJob("ZhuqueFangsong-Regular.ttf", "zhuque-fangsong-regular.zh.woff2", "cjk"),
    FontJob("LXGWNeoZhiSongScreen.ttf", "lxgw-neo-zhisong-screen.zh.woff2", "cjk"),
    FontJob("SourceHanSansSC-Medium.otf", "source-han-sans-sc-medium.zh.woff2", "cjk"),
    FontJob("GlowSansSC-Compressed-ExtraBold.otf", "glow-sans-sc-compressed-extra-bold.zh.woff2", "cjk"),
    FontJob("ChillDuanHeiSong_WideLight.otf", "chill-duanhei-song-wide-light.zh.woff2", "cjk"),
]


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for source in TEXT_SOURCES:
        root = ROOT / source
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
    return sorted(files)


def collect_subset_text() -> str:
    text = []
    for path in iter_text_files():
        text.append(path.read_text("utf-8", errors="ignore"))

    chars = {
        char
        for char in "".join(text)
        if not unicodedata.category(char).startswith("C")
    }
    return "".join(sorted(chars))


def run_subset(job: FontJob, text_file: Path, dry_run: bool) -> None:
    source = SOURCE_DIR / job.source
    output = OUTPUT_DIR / job.output
    if not source.exists():
        raise FileNotFoundError(f"Missing source font: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "fontTools.subset",
        str(source),
        f"--output-file={output}",
        "--flavor=woff2",
        "--layout-features=*",
        "--name-IDs=*",
        "--name-legacy",
        "--name-languages=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs",
        "--no-hinting",
    ]

    if job.mode == "latin":
        command.append(f"--unicodes={LATIN_UNICODES}")
    else:
        command.append(f"--text-file={text_file}")

    if dry_run:
        print(" ".join(command))
        return

    subprocess.run(command, cwd=ROOT, check=True)
    original = source.stat().st_size
    subset = output.stat().st_size
    savings = 100 - (subset / original * 100)
    print(f"{output.relative_to(ROOT)}  {subset / 1024:.1f} KB  ({savings:.1f}% smaller)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text_file = OUTPUT_DIR / "_subset-text.txt"
    subset_text = collect_subset_text()
    if not args.dry_run:
        text_file.write_text(subset_text, encoding="utf-8")
        print(f"Subset text: {len(subset_text)} unique characters")

    for job in FONT_JOBS:
        run_subset(job, text_file, args.dry_run)

    if not args.dry_run:
        text_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
