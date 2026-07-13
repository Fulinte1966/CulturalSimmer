# 电子书馆

静态 PDF 电子书分享网站。个人公益项目。

## 架构

- **网页**：GitHub Pages 托管，使用 [Astro](https://astro.build) 生成静态网站。
- **PDF**：GitHub Releases 托管，由 LaTeX 编译生成。
- **搜索**：使用 [Pagefind](https://pagefind.app) 提供静态站内搜索。
- **书目数据**：Markdown frontmatter，位于 `src/content/books/`。
- **静态书籍资产**：从 PDF 自动生成封面、目录和阅读数据。

## 本地开发

```bash
# 首次克隆后信任项目配置
mise trust

# 安装并启用与 GitHub Actions 一致的 Node 和 Python
mise install

# 安装项目依赖
mise run setup

# 启动开发服务器
mise exec -- npm run dev

# 运行全部测试、数据校验、类型检查和生产构建
mise run check
```

进入项目目录后，`mise` 会读取 `.node-version` 和 `.python-version`，让 `node`、`npm`、`python` 和 `python3` 使用与 GitHub Actions 相同的版本。不要直接依赖 macOS 的 `/usr/bin/python3`。

常用的单项命令仍可在项目环境中运行：

```bash
mise exec -- npm run check
mise exec -- npm run validate
mise exec -- npm run build
mise exec -- npm run preview
```

## 新增书籍

当前使用本地上传脚本创建临时 GitHub Release，再由 GitHub Actions 自动导入。不要手写 Markdown、下载链接、Release tag、PDF 文件名、分类号或册次；这些都由 PDF 元数据和索书号规则自动推导。

完整流程见 [电子书上传工作流](docs/ebook-upload-workflow.md)。

### 上传步骤

1. 准备带完整 XMP 元数据的 PDF。
2. 先运行本地预检：

   ```bash
   npm run ebook:upload path/to/book.pdf -- --dry-run
   ```

3. 通过本地脚本创建临时 Release：

   ```bash
   npm run ebook:upload path/to/book.pdf
   ```

4. GitHub Actions 自动校验元数据、比较相邻 PDF 版次、生成网页数据和静态资产、创建正式 Release、提交到 `main` 并触发 Pages 部署。

临时 Release tag 由脚本生成，格式类似：

   ```txt
   ingest-20260707-F0-1-1-v1
   ```

正式 Release tag 和 PDF 文件名由系统生成：

```txt
F0-1-1_v1
F0-1-1_v1.pdf
```

### 新版发布

同一本书发布新版时，保持同一个索书号，只递增 `edition`：

```txt
F0-1-1_v1
F0-1-1_v2
```

网页显示出版式版次，例如 `2026 年 6 月第 1 版`、`2026 年 7 月第 2 版`。下载入口始终指向当前 Markdown 记录的最新版。

正式 Release 会保存规范化正文快照和结构化 changelog，并使用自动生成的 Markdown 作为正文。复杂公式、表格和图形默认不参与文字差异；需要补录时编辑仓库中的 changelog，再手动运行 **Sync Release Changelog** 重新计算统计并更新 Release。详细规则见 [电子书版本更新日志规范](docs/release-changelog-conventions.md)。

主页“本站消息”会合并电子书入库生成的 `［新书］`、`［更新］` 消息和人工公告，并支持有序置顶及栏目内全文阅读。数据格式、创建命令和维护规则见 [本站消息维护规范](docs/site-updates-workflow.md)。

生产构建同时生成公开更新源 [`/updates/feed.json`](https://fulinte1966.github.io/CulturalSimmer/updates/feed.json)、最新摘要 `latest.json`、JSON Schema 和仓库内的 [`docs/site-updates-archive.md`](docs/site-updates-archive.md)。网站不提供完整更新正文页，首页“本站消息”只展示置顶和最近动态；`/updates/` 仅为旧链接保留静态跳转。更新 ID 只由书号、版次或公告文件名确定，重复构建不会产生新事件；外部通知器只按 ID 判断是否已发送。

书末“检查更新”二维码使用 `/check/?bookId={内部书号}&edition={版次}`。页面只以 URL 中的书号和版次进行匹配，书名、封面、最新版本和下载入口均以仓库数据为准。每次生产构建还会把同一书目的各版日志合并为 `src/data/changelogs/{内部书号}.md`，供检查更新页面跳转查看。

书末“书籍勘误”二维码使用 `/errata/?bookId={内部书号}&edition={版次}`。最新版会转入详情页并一次性打开嵌入的 Tally 表单；旧版会转到检查更新页面。详情页刷新后始终恢复默认二维码提示。

### 自动生成内容

以 `F0-1-1` 第 1 版为例，导入后会生成：

- `public/covers/F0-1-1_v1.png`
- `public/covers/F0-1-1_v1_spine.png`
- `src/data/outlines/F0-1-1_v1.json`
- `src/data/reading/F0-1-1_v1.json`
- `src/data/changelogs/F0-1-1_v1.changelog.json`
- `src/content/books/F0-1-1.md`
- `src/data/manifests/F0-1-1_v1.json`

中文、日文、韩文按字符计数，拉丁字母与数字按连续 token 计数。

## 索书号规则

### 单册书

```txt
分类号-入库序号
```

示例：`A8-3` = A8 类下第 3 种入库书。

### 多册书

```txt
分类号-入库序号-册次
```

示例：`A12-8-2` = A12 类下第 8 种入库书的第 2 册。

### 版次

版次在 frontmatter 中统一记录到 `editions[]`，每个条目包含 `edition` 和 `editionDate`。网页和下载默认使用 `editions[].edition` 最大的版本。

PDF 文件名和 Release tag 格式为：

```txt
A12-8-2_v1.pdf    A12-8-2_v1
```

下载链接自动生成为：

```txt
https://github.com/Fulinte1966/CulturalSimmer/releases/download/A12-8-2_v1/A12-8-2_v1.pdf
```

## 分类表

分类表位于 `src/data/classifications.yml`，采用自定义分类法。第一版仅用于显示分类入口和分类页标题，不做层级树浏览。

## 技术栈

- [Astro](https://astro.build) + TypeScript
- [Pagefind](https://pagefind.app) - 静态搜索
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 封面、书签与阅读数据提取
- GitHub Pages + GitHub Releases

## 许可

本项目为个人公益项目。PDF 文件的版权归原作者所有。
