# 电子书版本更新日志规范

**适用对象：** 电子书制作者、内容校对者与仓库维护者。

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

没有上一版时按初版发行处理。

## 内容快照

Release 中的 `{releaseTag}.content.json.gz` 使用以下字段：

```json
{
  "schemaVersion": 1,
  "normalizationProfile": "culturalsimmer-content-v3",
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
    {"start": 0, "end": 1024, "page": 11, "label": "1"}
  ]
}
```

`pageRuns` 的 `start` 包含、`end` 不包含。`page` 是从 1 开始的 PDF 物理页序号，仅供程序定位；`label` 是 PDF `/PageLabels` 定义的排版页码，例如前置部分的 `i`、`ii` 和正文重新开始的 `1`、`2`。Release 日志必须优先显示 `label`，不能用物理页序号代替。没有定义页面标签时，`label` 为 `null`，Markdown 明确回退为 `PDF 第 n 页`，避免与排版页码混淆。

页码只用于把差异定位回原 PDF，不参与内容对齐；因此相同正文重新分页不会产生差异。

完整正文快照不提交到 Git，只保存在 workflow 临时目录和正式 Release 资产中。

## 提取与规范化

`scripts/extract_content_snapshot.py` 使用 PyMuPDF 的 `page.get_text("dict", sort=True)`，按页面坐标和阅读顺序提取带字体信息的文本块，并使用 `Page.get_label()` 读取 PDF 原生页面标签。规则集中在 `culturalsimmer-content-v3` 中：

1. 使用 Unicode NFC，不使用 NFKC；
2. 删除软连字符、PDF 字体层产生的空字符，合并重复抽取的分号，并修复明确的拉丁字母行末断词；
3. token 化时忽略空格、软换行和连续空白差异；
4. CJK 正文按字符分词，拉丁字母和数字连续串作为一个 token，标点单独作为 token；
5. 默认排除作为封面的 PDF 第 1 页；
6. 排除含 `CULTURALSIMMER_UPDATE_PAGE` 的整页；
7. 排除页边缘的独立阿拉伯数字或罗马数字页码；
8. 仅在同一页边区域跨足够多页面重复时排除页眉或页脚；
9. 仅在可识别的目录页移除行尾目录页码；
10. 整页排除可识别的版权信息页和相邻二维码信息页。页面必须同时出现至少两个明确字段，例如“内部书号”“排版”“排印”“书籍勘误”或“检查更新”，不能只凭日期判断；
11. 排除旋转 90 度或 270 度的页面。这类页面在本项目中用于横向复杂表格，PDF 文本抽取的阅读顺序不稳定；
12. 排除数学字体字符占主导的独立公式块；
13. 排除大型矢量绘图区域内及紧邻的文本块，包括图示标签和复杂表格单元格。

复杂公式、表格和图形不进入自动文字差异，也不自动生成“待复核”项目。确有内容变化时，由维护者在生成的 changelog 中人工补录。自动排除规则必须保守：普通正文即使与公式或图表位于同一页，只要不属于复杂区域就应保留；不能可靠判定为结构噪声的内容也应保留。
若排除结构页后没有可比较文本，脚本会中止；纯扫描 PDF 必须先提供 OCR 文本或改由人工核查。

## 差异算法与限制

`scripts/compare_content_snapshots.py` 先使用带常见 token 抑制的 `SequenceMatcher` 对全书建立稳定匹配，再对不超过 12,000 token 的变化区段关闭自动抑制进行细化。完全相同的 token 序列直接返回零差异。

默认保护限制：

- 单版最多 400,000 token；
- 比较最多 30 秒；
- 相距不超过 4 个相同 token 的小差异合并；
- 相同文本因重新分页或脚注换位而在相邻 PDF 页之间移动时，成对删除对应的 `delete` 和 `insert`；这属于排版重定位，不是文字内容变化；
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
  "normalizationProfile": "culturalsimmer-content-v3",
  "fromEdition": {"edition": 1, "editionDate": "2026-06"},
  "toEdition": {"edition": 2, "editionDate": "2026-07"},
  "summary": {"total": 1, "added": 0, "removed": 0, "changed": 1},
  "changes": [
    {
      "index": 1,
      "type": "replace",
      "needsReview": true,
      "old": {
        "pages": [22],
        "pageLabels": ["12"],
        "prefix": "认真",
        "changedText": "做",
        "suffix": "好出版工作。"
      },
      "new": {
        "pages": [23],
        "pageLabels": ["13"],
        "prefix": "认真",
        "changedText": "作",
        "suffix": "好出版工作。"
      }
    }
  ]
}
```

导入完成后，同一份 JSON 同时保存在 `src/data/changelogs/{releaseTag}.changelog.json` 和正式 Release 资产中。仓库文件是后续人工修订的来源；Release 资产和正文是它的发布副本。初版的 `fromEdition` 为 `null`，统计均为 `0`，`changes` 为空数组。不得从 Markdown 反向解析 JSON。

`changes` 是唯一需要维护的差异列表。`index` 和 `summary` 均为派生字段：Release 渲染器和未来网页调用 `changes` 时必须重新计算统计，不得信任或人工维护旧的 `summary`。同步程序会按数组顺序重写连续的 `index`，并把派生统计写回 changelog 和 manifest。

`needsReview` 是人工差异项上的可选布尔字段。维护者暂时不能确认变化性质或定位时设为 `true`；省略或为 `false` 均表示不显示待复核标记。待复核数量必须从完整 `changes` 数组计算，是总差异的子集，不写入独立的手工统计字段。一个 `replace` 项虽然显示旧、新两行，仍只计一处待复核。

## Markdown 格式

初版固定为：

```markdown
### 2026 年 6 月第 1 版

初版发行
```

后续版次固定显示当前版次标题、总数和三类统计；标题与统计之间不放分割线，单版日志末尾保留一条 `---`。存在差异明细时，统计和明细之间另用一条 `---` 分隔；零差异时只保留末尾分割线。修改使用旧、新两行和 `***变化文字***`；删减使用 `~~**删除文字**~~`；新增使用 `**新增文字**`。变化标记与前后原文上下文之间各保留一个 ASCII 空格，避免标点邻接使 GFM 强调分隔符失效。页码取自 `pageLabels`：单页写作 `第 i 页` 或 `第 1 页`，跨页写作 `第 ii—iii 页` 或 `第 12—13 页`；没有页面标签时写作 `PDF 第 n 页` 或 `PDF 第 n—m 页`。

存在 `needsReview: true` 的差异项时，在三类统计下方另行显示 `<sub>?</sub> 待复核 **n** 处`，并在该项每个差异行的操作标记前显示 `<sub>?</sub>`；不存在时整行和所有问号标记均省略。

正文中的 `*`、`_`、`~`、反引号、尖括号和反斜杠必须先转义，再添加程序生成的 Markdown 标记。

## Release 与失败处理

当前项目先创建 Draft intake，并在受保护候选站完成验收。正式 Release 创建前必须重新验证候选锁，并完成快照、差异和 Markdown 生成。Release 资产包括：

```text
F0-1-1_v2.pdf
F0-1-1_v2.manifest.json
F0-1-1_v2.content.json.gz
F0-1-1_v2.changelog.json
```

Release 创建时先上传 PDF、快照和 changelog，并将生成的 Markdown 作为正文。取得 GitHub 提供的 PDF asset digest 后更新 manifest，再上传最终 manifest。后续提交失败时，现有 cleanup 步骤删除本次正式 Release 和 tag；历史 Release 不受影响。

## 人工补录与重新发布

自动导入和 Pages 部署保持原流程不变。需要补录被跳过的公式、表格或图形变化，或者修订自动结果时：

1. 编辑 `src/data/changelogs/{releaseTag}.changelog.json` 的 `changes` 数组，只填写 `type`、`old`、`new` 和可选的 `needsReview`；
2. 将修改合并到默认分支，等待常规 Deploy 完成；未来网页读取日志时从 `changes` 即时计算统计，因此不会显示手写或过期的 `summary`；
3. 在 GitHub Actions 中手动运行 **Sync Release Changelog**，输入正式 `releaseTag`；
4. workflow 校验 JSON 和仓库数据，重新计算 `index`、`summary` 与 manifest 统计，运行完整构建，再更新正式 Release 正文和同名 changelog 资产。

该 workflow 使用 GitHub 官方的 `workflow_dispatch` 手动触发机制；只有默认分支上的 workflow 可以从 Actions 页面运行。Release 正文通过 `gh release edit --notes-file` 更新，JSON 资产在本地校验完成后通过 `gh release upload --clobber` 替换。同步失败不会改写 PDF，也不会触发电子书导入流程。

## 单书总更新日志

`npm run build` 会先执行 `scripts/build_book_changelogs.py`，按最新版至最早版把同一书目的 Release Markdown 合并为：

```text
src/data/changelogs/{bookId}.md
```

聚合文件是构建产物，不是新的事实来源。文件不增加总标题、说明或额外分割线，只按最新版至最早版依次拼接 `## [releaseTag](releaseUrl)` 和对应单版日志；相邻版次由前一个非初版日志末尾自带的 `---` 分隔。脚本逐版读取 `{releaseTag}.changelog.json`，渲染时重新计算统计；第 1 版历史日志缺失时可根据书目版次生成“初版发行”，第 2 版及以后缺失结构化日志则构建失败。电子书检查更新页面链接到 GitHub 默认分支中的该文件。

检查更新 URL 契约为：

```text
https://fulinte.pages.dev/CulturalSimmer/check/?bookId=F0-1-1&edition=1
```

`bookId` 必须与书目内部书号完全一致，`edition` 必须为正整数。页面只把参数作为查询键，不接受 URL 覆盖书名、封面、下载地址或最新版信息。

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
npm run verify
```

## 参考文档

- [PyMuPDF 文本提取说明](https://pymupdf.readthedocs.io/en/latest/app1.html)
- [PyMuPDF `Page.get_text()` 文档](https://pymupdf.readthedocs.io/en/latest/page.html)
- [GitHub Actions：手动运行 workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [GitHub Actions workflow 语法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub CLI `gh release` 命令参考](https://cli.github.com/manual/gh_release)
- [GitHub CLI `gh release edit`](https://cli.github.com/manual/gh_release_edit)
- [GitHub CLI `gh release upload`](https://cli.github.com/manual/gh_release_upload)
- [GitHub REST API：Release assets](https://docs.github.com/en/rest/releases/assets)
