# CulturalSimmer（文火）

面向读者的静态 PDF 电子书馆。GitHub Pages 是永久主站，Cloudflare Pages 提供同一构建产物的备用镜像，GitHub Releases 保存正式 PDF。

- 主站：<https://fulinte1966.github.io/CulturalSimmer/>
- Cloudflare 镜像：<https://culturalsimmer-mirror.pages.dev/CulturalSimmer/>
- 文档索引：[docs/README.md](docs/README.md)
- 本站更新归档：[docs/site-updates-archive.md](docs/site-updates-archive.md)
- ntfy 备用信号源：[docs/ntfy-subscription-guide.md](docs/ntfy-subscription-guide.md)

## 架构

```text
带 XMP 元数据的 PDF
  -> 临时 ingest Release
  -> GitHub Actions 校验、生成资产和更新日志
  -> 正式 GitHub Release
  -> 生成书目、封面、目录、阅读数据和更新事件
  -> GitHub Pages 主站
  -> Cloudflare Pages 镜像
```

主要技术：Astro、TypeScript、Pagefind、PyMuPDF、GitHub Actions、GitHub Pages、GitHub Releases 和 Cloudflare Pages。

## 本地开发

项目通过 `.node-version`、`.python-version` 和 `mise.toml` 固定运行环境。

```bash
mise trust
mise install
mise run setup
mise exec -- npm run dev
```

提交前运行完整验证。该命令包含测试、数据校验、Astro 检查、两遍生产构建和字体子集刷新：

```bash
mise run check
```

只需单独重建生产字体时运行：

```bash
mise run fonts
```

## 发布电子书

PDF XMP 是人工书目数据的唯一来源。不要手写 Release tag、下载地址、PDF 文件名、分类号、册次或版本 manifest。

```bash
# 仅预检
mise exec -- npm run ebook:upload path/to/book.pdf -- --dry-run

# 创建临时 Release 并触发正式入库
mise exec -- npm run ebook:upload path/to/book.pdf
```

完整步骤见 [电子书上传工作流](docs/ebook-upload-workflow.md)，元数据要求见 [PDF 元数据契约](docs/pdf/metadata-contract.md)，版本差异规则见 [电子书版本更新日志规范](docs/release-changelog-conventions.md)。

## 数据原则

- `src/content/books/`、`src/data/` 和 `public/covers/` 中的书目派生文件由入库流程生成。
- `src/content/announcements/` 保存人工公告；`src/data/site-update-pins.json` 保存置顶顺序。
- PDF 只进入 GitHub Releases，不进入 Git 历史。
- `docs/site-updates-archive.md` 是自动生成的可读镜像，不是人工编辑源。
- 检查更新链接使用 `/check/?bookId={id}&edition={n}`。
- 书籍勘误链接使用 `/errata/?bookId={id}&edition={n}`。

## 贡献

问题报告和代码贡献约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。公开仓库只保存运行、复现和贡献所需资料；本地凭据、备份、运维记录、测试 PDF 与智能体配置不得提交。

## 权利说明

本项目为个人公益项目。电子书内容的权利归原作者及相关权利人所有。
