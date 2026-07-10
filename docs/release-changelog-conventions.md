# 电子书版本更新日志规范

本文档规定同一书目相邻 PDF 版次的内容比较、结构化记录和 GitHub Release 正文格式。

## 目的与边界

更新日志回答“读者在最终 PDF 中看到的内容发生了什么变化”。比较对象只能是同一索书号相邻版次的最终 PDF 经规范化后得到的正文 token 序列。

不得使用 Git tag、提交记录、LaTeX 源码或 PDF 二进制差异代替正文比较。这些来源会混入排版代码、网站修改、字体子集、对象编号和压缩方式等非内容变化。

程序只判定：

- `insert`：新增；
- `delete`：删减；
- `replace`：修改。

程序不得把差异描述为“纠错”“勘误”“优化”“改进”或“校订”。这些词涉及修改意图，必须由人工判断。

## 相邻版次

导入当前版次时，系统从 `src/content/books/{bookId}.md` 的 `editions[]` 中选取小于当前 `edition` 的最大值。不得直接假设上一版等于 `edition - 1`。

有上一版时，系统优先下载其 `{releaseTag}.content.json.gz`。快照缺失或 `normalizationProfile` 不一致时，改为下载 `{releaseTag}.pdf` 并使用当前规则重新提取。旧 PDF 或快照的 `bookId`、`edition` 必须与书目记录一致，否则中止发布。

没有上一版时按初次发布处理。

## 内容快照

Release 中的 `{releaseTag}.content.json.gz` 使用以下字段：

```json
{
  "schemaVersion": 1,
  "normalizationProfile": "culturalsimmer-content-v1",
  "extractor": {
    "name": "PyMuPDF",
    "version": "1.24.11"
  },
  "bookId": "F0-1-1",
  "edition": 2,
  "editionDate": "2026-07",
  "pageCount": 218,
  "tokens": ["认", "真", "GitHub", "2026", "。"],
  "pageRuns": [
    {"start": 0, "end": 1024, "page": 2}
  ]
}
```

`pageRuns` 的 `start` 包含、`end` 不包含。页码只用于把差异定位回原 PDF，不参与内容对齐；因此相同正文重新分页不会产生差异。

完整正文快照不提交到 Git，只保存在 workflow 临时目录和正式 Release 资产中。

## 提取与规范化

`scripts/extract_content_snapshot.py` 使用 PyMuPDF 的 `page.get_text("blocks", sort=True)`，按页面坐标和阅读顺序提取文本块。规则集中在 `culturalsimmer-content-v1` 中：

1. 使用 Unicode NFC，不使用 NFKC；
2. 删除软连字符并修复明确的拉丁字母行末断词；
3. token 化时忽略空格、软换行和连续空白差异；
4. CJK 正文按字符分词，拉丁字母和数字连续串作为一个 token，标点单独作为 token；
5. 默认排除作为封面的 PDF 第 1 页；
6. 排除含 `CULTURALSIMMER_UPDATE_PAGE` 的整页；
7. 排除页边缘的独立阿拉伯数字或罗马数字页码；
8. 仅在同一页边区域跨足够多页面重复时排除页眉或页脚；
9. 仅在可识别的目录页移除行尾目录页码；
10. 仅在可识别的版权信息页移除发行版次、生成日期和检查更新 URL。版权页必须同时出现至少两个明确字段，例如“内部书号”“排版”“排印”“书籍勘误”或“检查更新”，不能只凭日期判断。

自动排除规则必须保守。不能可靠判定为结构噪声的内容应保留。
若排除结构页后没有可比较文本，脚本会中止；纯扫描 PDF 必须先提供 OCR 文本或改由人工核查。

## 差异算法与限制

`scripts/compare_content_snapshots.py` 先使用带常见 token 抑制的 `SequenceMatcher` 对全书建立稳定匹配，再对不超过 12,000 token 的变化区段关闭自动抑制进行细化。完全相同的 token 序列直接返回零差异。

默认保护限制：

- 单版最多 400,000 token；
- 比较最多 30 秒；
- 相距不超过 4 个相同 token 的小差异合并；
- 差异两侧优先截取到句末，否则各保留约 20 个 token；
- 单项最终显示区间最多 160 个字符；长变化保留首尾并以 `…` 标记；
- Release 正文默认最多列出 200 项，JSON 保留全部差异。

超限或比较失败会返回非零退出状态。导入 workflow 不会发布空白或伪造的更新日志。

## Changelog JSON

`{releaseTag}.changelog.json` 是 Markdown 和后续网站功能的单一事实来源：

```json
{
  "schemaVersion": 1,
  "bookId": "F0-1-1",
  "normalizationProfile": "culturalsimmer-content-v1",
  "fromEdition": {"edition": 1, "editionDate": "2026-06"},
  "toEdition": {"edition": 2, "editionDate": "2026-07"},
  "summary": {"total": 1, "added": 0, "removed": 0, "changed": 1},
  "changes": [
    {
      "index": 1,
      "type": "replace",
      "old": {
        "pages": [12],
        "prefix": "认真",
        "changedText": "做",
        "suffix": "好出版工作。"
      },
      "new": {
        "pages": [13],
        "prefix": "认真",
        "changedText": "作",
        "suffix": "好出版工作。"
      }
    }
  ]
}
```

初版的 `fromEdition` 为 `null`，统计均为 `0`，`changes` 为空数组。不得从 Markdown 反向解析 JSON。

## Markdown 格式

初版固定为：

```markdown
### 2026 年 6 月第 1 版

---

初次发布。
```

后续版次固定显示总数和三类统计。修改使用旧、新两行和 `***变化文字***`；删减使用 `~~**删除文字**~~`；新增使用 `**新增文字**`。单页写作 `第 1 页`，跨页写作 `第 12—13 页`。

正文中的 `*`、`_`、`~`、反引号、尖括号和反斜杠必须先转义，再添加程序生成的 Markdown 标记。

## Release 与失败处理

当前项目沿用自动正式发布，不改为 Draft Release。正式 Release 创建前必须完成快照、差异和 Markdown 生成。Release 资产包括：

```text
F0-1-1_v2.pdf
F0-1-1_v2.manifest.json
F0-1-1_v2.content.json.gz
F0-1-1_v2.changelog.json
```

Release 创建时先上传 PDF、快照和 changelog，并将生成的 Markdown 作为正文。取得 GitHub 提供的 PDF asset digest 后更新 manifest，再上传最终 manifest。后续提交失败时，现有 cleanup 步骤删除本次正式 Release 和 tag；历史 Release 不受影响。

## 本地生成

比较两个版次：

```bash
python scripts/generate_release_changelog.py \
  --old-pdf previous/F0-1-1_v1.pdf \
  --new-pdf current/F0-1-1_v2.pdf \
  --book-id F0-1-1 \
  --old-edition 1 \
  --new-edition 2 \
  --old-edition-date 2026-06 \
  --new-edition-date 2026-07 \
  --output-json output/F0-1-1_v2.changelog.json \
  --output-markdown output/F0-1-1_v2.release-notes.md
```

初版省略全部 `--old-*` 参数。命令默认不覆盖已有输出；需要覆盖时传 `--force`，需要保留中间快照时传 `--debug`。可使用 `--max-changes`、`--max-tokens` 和 `--timeout-seconds` 调整保护限制。

运行相关测试：

```bash
npm run test:changelog
npm run test:ingest
```

## 参考文档

- [PyMuPDF 文本提取说明](https://pymupdf.readthedocs.io/en/latest/app1.html)
- [PyMuPDF `Page.get_text()` 文档](https://pymupdf.readthedocs.io/en/latest/page.html)
- [GitHub CLI `gh release` 命令参考](https://cli.github.com/manual/gh_release)
- [GitHub REST API：Release assets](https://docs.github.com/en/rest/releases/assets)
