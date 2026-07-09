# 电子书上传工作流

本文档记录当前 PDF 上传、临时 Release、自动导入、正式发布和网页部署流程。

## 核心原则

- PDF 不进入 Git 历史，只托管在 GitHub Releases。
- PDF XMP 是书目元数据来源；不根据文件名、Release 标题或正文内容猜测书目信息。
- 不手写 `downloadUrl`、`releaseTag`、`pdfFilename`、`classification`、`volume` 等派生字段。
- 正式发布键为 `{bookId}_v{edition}`，例如 `F0-1-1_v1`。
- `prism:bookEdition` 必须由 PDF 声明；脚本只校验，不替 PDF 决定版次。

## 本地上传入口

推荐使用本地命令创建临时 ingest Release：

```bash
npm run ebook:upload path/to/book.pdf
```

常用检查：

```bash
npm run ebook:upload path/to/book.pdf -- --dry-run
npm run ebook:upload path/to/book.pdf -- --draft
npm run ebook:upload path/to/book.pdf -- --allow-edition-skip
```

`--dry-run` 只做 preflight，不创建 Release。输出会包含：

- 书名、索书号、PDF 声明版次；
- 内容提要摘要；
- `xmp:CreateDate`、`editionDate`；
- 正式 tag、正式 PDF 文件名、临时 ingest tag；
- 版次校验结果；
- 本地和远程重复检查结果。

`--allow-edition-skip` 默认不要使用。确需跳版时，本地脚本会把 `Allow-Edition-Skip: true` 写入临时 Release notes，ingest workflow 再据此放行；没有该标记时 CI 仍按不跳版规则失败。

## 必填 PDF XMP 字段

| 含义 | XMP 字段 | 规则 |
|---|---|---|
| 索书号 | `dc:identifier` | 必须符合索书号正则，且分类号存在 |
| 主标题 | `dc:title` | 非空 |
| 版次 | `prism:bookEdition` | 正整数，且必须符合仓库预期版次 |
| 内容提要 | `dc:description` | 非空，不得为明显占位文本 |
| PDF 创建日期 | `xmp:CreateDate` | 用于生成 `editionDate = YYYY-MM` |

`dc:creator` 不再必填；缺失时前端隐藏作者栏。
`dc:language` 不再必填；缺失时系统默认 `zh-CN`，前端默认不展示语言。

## 可选 PDF XMP 字段

| 含义 | XMP 字段或 PDF Info 键 |
|---|---|
| 作者、编者、整理者 | `dc:creator` |
| 语言 | `dc:language` |
| 副标题 | `prism:subtitle` |
| 标签 | `dc:subject` |
| 丛书 | `prism:publicationName` |
| PDF 内部卷号 | `prism:volume` |
| 出版者 | `dc:publisher` |
| 来源 | `dc:source` |
| 权利说明 | `dc:rights` |
| 权利说明 URL | `xmpRights:WebStatement` |
| Z-Library 页面 URL | `prism:url`（LaTeX helper 中为 `zlibrary-url`，最终写入 `pdfurl`） |
| 总册数 | `/EbookTotalVolumes` |

LaTeX 源码可以使用项目自己的宏名，但最终写入 PDF XMP 时必须映射到标准字段，例如 `dc:identifier`、`dc:title`、`prism:bookEdition`、`dc:description`。

项目提供了一个可直接放入 LaTeX 工程的元数据模块：

```txt
docs/latex/culturalsimmer-ebook-metadata.sty
```

使用时把该文件复制到 LaTeX 工程目录，正文前调用：

```tex
\usepackage{culturalsimmer-ebook-metadata}

\EbookMetadata{
  id = F0-1-1,
  title = 政治经济学基础知识,
  subtitle = 资本主义部分,
  author = 《政治经济学基础知识》编写组,
  edition = 1,
  volume = 1,
  total-volumes = 1,
  description = 系统介绍资本主义政治经济学的基础知识。,
  keywords = {政治经济学,资本主义},
  language = zh-CN,
  series = 青年自学丛书,
  zlibrary-url = https://z-library.sk/book/...
}
```

## 版次校验规则

导入前会读取 `src/content/books/{bookId}.md` 中的 `editions[]`。

- 新书没有历史记录时，预期版次为 `1`。
- 已有历史记录时，预期版次为已有最大 `edition + 1`。
- PDF 声明的 `prism:bookEdition` 等于预期版次才通过。
- 重复版次永远失败。
- 默认不允许跳版。
- 本地上传可传 `--allow-edition-skip` 允许跳版，但仍会显示警告。

示例输出：

```txt
PDF 声明版次：2
仓库已有最高版次：1
脚本预期版次：2
版次校验：通过
```

失败示例：

```txt
PDF 声明版次：2
仓库已有最高版次：2
脚本预期版次：3
版次校验：失败，该版次已存在，应为第 3 版
```

## 自动导入流程

```text
本地脚本创建 ingest-* Release
  -> GitHub Actions 下载 Release 中唯一 PDF
  -> 读取并校验 PDF XMP 元数据
  -> 校验 PDF 版次是否等于仓库预期版次
  -> 生成 Markdown、manifest、封面、书脊、目录和阅读数据
  -> 运行检查、测试和生产构建
  -> 创建正式 Release 并上传规范化 PDF
  -> 读取 GitHub Release asset digest 写入 manifest
  -> 提交生成文件到 main
  -> 删除临时 Release 和临时 tag
  -> main push 触发 GitHub Pages 部署
```

`Ingest PDF` workflow 使用全局并发锁 `ebook-ingest`，避免多个 ingest Release 同时处理。

## Markdown 书目记录

Markdown 是书目级索引。版次统一记录在 `editions[]` 中：

```yaml
---
id: F0-1-1
title: 政治经济学基础知识
subtitle: 资本主义部分
description: 系统介绍……
author: 《政治经济学基础知识》编写组
language: zh-CN
zlibraryUrl: https://z-library.sk/book/...
editions:
  - edition: 1
    editionDate: "2026-06"
    releaseTag: F0-1-1_v1
    manifest: src/data/manifests/F0-1-1_v1.json
  - edition: 2
    editionDate: "2026-07"
    releaseTag: F0-1-1_v2
    manifest: src/data/manifests/F0-1-1_v2.json
---
```

当前版不单独存冗余字段；系统自动取 `editions[].edition` 最大值作为默认展示和下载版本。

## manifest

每个版本都有独立 manifest：

```txt
src/data/manifests/F0-1-1_v1.json
src/data/manifests/F0-1-1_v2.json
```

manifest 是版本文件事实记录，包含 `bookId`、`title`、`edition`、`editionDate`、`pdfCreateDate`、`description`、`creator`、`language`、`releaseTag`、`pdfFilename`、`downloadUrl`、`githubAssetDigest`、`bytes`、`pageCount`、`wordCount` 等字段。

GitHub Release asset digest 由 GitHub 提供，系统读取并记录；不要求人工计算 SHA，也不在前台展示。

## 前端展示

详情页只展示读者关心的信息：

- 卷册：`上册`、`中册`、`下册` 或 `第 n 册`；
- 页数、字数、文件大小；
- `YYYY 年 M 月第 n 版`；
- 内部书号，如 `F0-1-1`；
- 内容提要。

详情页不展示 digest、releaseTag、downloadUrl、pdfFilename、manifest path、Git tag、GitHub asset id 等系统字段。
