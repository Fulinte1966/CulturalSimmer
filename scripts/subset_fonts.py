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
# UAPI documents `weather` as free-form text, not a fixed enum. The weather
# words below are only the common Chinese values listed in their API reference;
# unexpected API text should still fall through to the CSS fallback font stack.
SAFE_TEXT = """
的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可
主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家
电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞
政治经济学基础知识资本主义部分青年自学丛书文火文化模拟器书籍勘误读者勘误表
主页分类索引搜索内容提要目录大纲内部书号传阅基核技术站择览资料站返回勘误
零一二三四五六七八九十百千万亿年月日星期周上下左右第版页字兆字节
北京地区天气预报白天夜间风向风力最高温度最低暂无晴多云阴小雨中雨大雨雷阵雨
小雪中雪大雪雨夹雪雾霾沙尘东南西北东北西南微持续级度
农历甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥正冬腊初廿
《》“”‘’（）()：；，。！？、·・＊-—–/\\[]{}<>….,:;!?*
"""


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
    text = [SAFE_TEXT]
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
