# 电子书馆

静态 PDF 电子书分享网站。个人公益项目。

## 架构

- **网页**：GitHub Pages 托管，使用 [Astro](https://astro.build) 生成静态网站。
- **PDF**：GitHub Releases 托管，由 LaTeX 编译生成。
- **搜索**：使用 [Pagefind](https://pagefind.app) 提供静态站内搜索。
- **书目数据**：Markdown frontmatter，位于 `src/content/books/`。
- **目录大纲**：从 PDF 书签自动提取的 JSON，位于 `src/data/outlines/`。

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

### 首次发布

1. 确定索书号，例如 `A12-8-2`。
2. 编译 PDF，命名为 `A12-8-2_v1.pdf`。
3. 创建 GitHub Release，tag 为 `A12-8-2_v1`，上传 PDF。
4. 新建 `src/content/books/A12-8-2.md`，填写 frontmatter。
5. 运行目录提取脚本：
   ```bash
   ./scripts/extract-outline-from-release.sh A12-8-2 1
   ```
6. 检查生成的 `src/data/outlines/A12-8-2_v1.json`。
7. 提交 Markdown 和 JSON，推送到 `main` 分支。
8. GitHub Actions 自动部署网站。

### 更新新版

1. 将 edition 从 1 改为 2。
2. 新 PDF 命名为 `A12-8-2_v2.pdf`。
3. 新建 Release：tag 为 `A12-8-2_v2`，上传 PDF。
4. 重新提取目录 JSON：
   ```bash
   ./scripts/extract-outline-from-release.sh A12-8-2 2
   ```
5. 更新 `src/content/books/A12-8-2.md` 的 `edition` 字段。
6. 提交更新。

### 目录提取脚本

需要安装依赖：

```bash
pip install PyMuPDF
```

需要安装 [GitHub CLI](https://cli.github.com/) 并登录：

```bash
gh auth login
```

也可以直接从本地 PDF 提取（无需 Release）：

```bash
python scripts/extract-outline.py path/to/book.pdf src/data/outlines/A12-8-2_v1.json
```

## 索书号规则

### 单册书

```
分类号-入库序号
```

示例：`A8-3` = A8 类下第 3 种入库书。

### 多册书

```
分类号-入库序号-册次
```

示例：`A12-8-2` = A12 类下第 8 种入库书的第 2 册。

### 版次

版次在 frontmatter 中用 `edition` 字段记录。PDF 文件名和 Release tag 格式为：

```
A12-8-2_v1.pdf    A12-8-2_v1
```

下载链接自动生成为：

```
https://github.com/poyinte/ebook-library/releases/download/A12-8-2_v1/A12-8-2_v1.pdf
```

## 分类表

分类表位于 `src/data/classifications.yml`，采用自定义分类法。第一版仅用于显示分类页标题，不做层级树浏览。

## 技术栈

- [Astro](https://astro.build) + TypeScript
- [Pagefind](https://pagefind.app) — 静态搜索
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF 书签提取
- GitHub Pages + GitHub Releases

## 许可

本项目为个人公益项目。PDF 文件的版权归原作者所有。
