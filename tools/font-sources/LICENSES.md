# 字体来源与许可

本目录中的完整字体只用于确定性生成 `public/fonts/subset/` 的 WOFF2。生成的子集继续受对应源字体许可约束；复制、更新或替换字体时必须同时核对上游许可与字体内部 `name` 表。

| 源字体 | 字体内部版本 | 许可 |
| --- | --- | --- |
| `ChillDuanHeiSong_WideLight.otf` | 1.200 | SIL Open Font License 1.1 |
| `ChillJinshuSong*.otf` | 2.000 | SIL Open Font License 1.1 |
| `GlowSansSC-Compressed-ExtraBold.otf` | 0.93 | SIL Open Font License 1.1 |
| `SourceHanSansSC-Medium.otf` | 2.004 | SIL Open Font License 1.1 |
| `ZhuqueFangsong-Regular.ttf` | 0.212 | SIL Open Font License 1.1 |
| `LXGWNeoZhiSongScreen.ttf` | 1.010 | IPA Font License Agreement 1.0 |
| `texgyretermes-regular.otf`、`texgyretermes-bold.otf` | 2.004 | GUST Font License |

许可证全文：

- [`licenses/OFL-1.1.txt`](licenses/OFL-1.1.txt)
- [`licenses/IPA-FONT-LICENSE-1.0.txt`](licenses/IPA-FONT-LICENSE-1.0.txt)
- [`licenses/GUST-FONT-LICENSE.txt`](licenses/GUST-FONT-LICENSE.txt)

许可来源以当前仓库字体文件内嵌的 license description/URL 为准。TeX Gyre 另见 [CTAN tex-gyre](https://ctan.org/pkg/tex-gyre)，IPA Font License 全文另见 [Open Source Initiative](https://opensource.org/license/ipa)。

## 更新规则

1. 不用系统字体覆盖本目录文件；只从可追溯上游版本更新。
2. 更新时记录字体版本、许可和上游地址，并重新运行 `npm run verify`。
3. 若源字体许可、保留字体名或衍生字体要求变化，先处理许可义务，再发布新的 WOFF2。
4. 不删除完整源字体：CI 需要它们在无本机字体依赖的环境中重建子集。
