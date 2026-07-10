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
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 类型检查
npm run check

# 校验书目数据
npm run validate

# 构建生产版本（含 Pagefind 索引）
npm run build

# 预览构建结果
npm run preview
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

正式 Release 会保存规范化正文快照和结构化 changelog，并使用自动生成的 Markdown 作为正文。详细规则见 [电子书版本更新日志规范](docs/release-changelog-conventions.md)。

### 自动生成内容

以 `F0-1-1` 第 1 版为例，导入后会生成：

- `public/covers/F0-1-1_v1.png`
- `public/covers/F0-1-1_v1_spine.png`
- `src/data/outlines/F0-1-1_v1.json`
- `src/data/reading/F0-1-1_v1.json`
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
