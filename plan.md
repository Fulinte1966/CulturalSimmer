# Codex Plan: 静态 PDF 电子书馆第一版实现

## 0. 项目目标

实现一个个人公益性质的小型 PDF 电子书分享网站。第一版只关注功能实现，不做复杂 UI 风格化设计。

核心目标：

1. 使用 Astro 生成静态网站。
2. 使用 Markdown 管理书目。
3. 使用 GitHub Pages 部署网页。
4. 使用 GitHub Releases 存放 PDF。
5. 使用 Pagefind 提供静态站内搜索。
6. PDF 由 LaTeX 编译生成，网站只提供 PDF 格式。
7. 每本书使用“索书号”作为唯一 ID。
8. 从 PDF 的 hyperref 书签自动提取目录大纲，生成 JSON 并提交进仓库。
9. 详情页读取目录 JSON 并显示目录。
10. 不做账号、评论、后台、数据库、在线阅读、About 页、独立版权说明页。

---

## 1. 技术栈

使用：

* Astro
* TypeScript
* Markdown frontmatter
* Pagefind
* GitHub Pages
* GitHub Releases
* Python + PyMuPDF，用于提取 PDF 书签目录

不要使用：

* 数据库
* 用户系统
* 评论系统
* CMS
* 服务端渲染
* PHP
* 在线 PDF 阅读器
* EPUB / MOBI / HTML 等其他电子书格式

---

## 2. 项目结构

创建或整理为以下结构：

```txt
ebook-library/
├── src/
│   ├── content/
│   │   ├── config.ts
│   │   └── books/
│   │       ├── A8-3.md
│   │       └── A12-8-2.md
│   │
│   ├── data/
│   │   ├── classifications.yml
│   │   └── outlines/
│   │       ├── A8-3_v1.json
│   │       └── A12-8-2_v1.json
│   │
│   ├── lib/
│   │   ├── bookId.ts
│   │   ├── books.ts
│   │   └── site.ts
│   │
│   ├── components/
│   │   ├── Layout.astro
│   │   ├── BookCard.astro
│   │   ├── BookMeta.astro
│   │   ├── DownloadButton.astro
│   │   └── Outline.astro
│   │
│   ├── pages/
│   │   ├── index.astro
│   │   ├── search.astro
│   │   ├── books/
│   │   │   ├── index.astro
│   │   │   └── [id].astro
│   │   └── categories/
│   │       └── [classification].astro
│   │
│   └── styles/
│       └── global.css
│
├── public/
│   ├── covers/
│   │   ├── A8-3.jpg
│   │   └── A12-8.jpg
│   └── favicon.svg
│
├── scripts/
│   ├── extract-outline.py
│   ├── extract-outline-from-release.sh
│   └── validate-books.ts
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── package.json
├── astro.config.mjs
├── tsconfig.json
└── README.md
```

---

## 3. 索书号规则

网站中 `id` 即索书号。

### 3.1 单册书

格式：

```txt
分类号-入库序号
```

示例：

```txt
A8-3
I242-12
K207-5
H14-2
```

含义：

```txt
A8-3 = A8 类下第 3 种入库书
```

### 3.2 多册书

格式：

```txt
分类号-入库序号-册次
```

示例：

```txt
A12-8-1
A12-8-2
A12-8-3
```

含义：

```txt
A12-8-2 = A12 类下第 8 种入库书的第 2 册
```

### 3.3 版次

元数据中只写数字：

```yaml
edition: 1
```

页面显示：

```txt
第 1 版
```

PDF 文件名：

```txt
A12-8-2_v1.pdf
```

GitHub Release tag：

```txt
A12-8-2_v1
```

下载 URL 自动生成：

```txt
https://github.com/{owner}/{repo}/releases/download/A12-8-2_v1/A12-8-2_v1.pdf
```

---

## 4. 最小书目元数据

每本书一个 Markdown 文件。

普通单册书示例：

```yaml
---
id: A8-3
title: 马克思主义学习资料重排本
author: 佚名
edition: 1
date: 2026-06-17
tags:
  - 马克思主义
  - 学习资料
---

这里写简介、底本来源、重排说明。
```

多册书示例：

```yaml
---
id: A12-8-2
title: 某某著作集
author: 马克思
edition: 1
date: 2026-06-17
tags:
  - 马克思
  - 著作集
---

这里写第二册简介、底本来源、重排说明。
```

可选字段：

```yaml
cover: /covers/A12-8.jpg
total_volumes: 3
```

不需要以下字段：

```yaml
call_number
classification
accession_number
volume
volume_number
format
typesetting
release_tag
pdf_filename
download_url
classification_label
status
```

这些全部由程序从 `id`、`edition` 和分类表中推导。

---

## 5. 数据推导规则

在 `src/lib/bookId.ts` 中实现以下函数。

### 5.1 parseBookId

输入：

```ts
parseBookId("A12-8-2")
```

输出：

```ts
{
  id: "A12-8-2",
  classification: "A12",
  accessionNumber: 8,
  volumeNumber: 2,
  workId: "A12-8",
  isVolume: true
}
```

输入：

```ts
parseBookId("A8-3")
```

输出：

```ts
{
  id: "A8-3",
  classification: "A8",
  accessionNumber: 3,
  volumeNumber: null,
  workId: "A8-3",
  isVolume: false
}
```

ID 正则建议：

```ts
/^[A-Z](?:\d+(?:\.\d+)?)?-\d+(?:-\d+)?$/
```

这个规则需要支持：

```txt
A8-3
A12-8-2
I210.4-1
K926.3-2
T-1
Z228-1
```

### 5.2 formatEdition

```ts
formatEdition(1) => "第 1 版"
```

### 5.3 formatVolume

```ts
formatVolume(2) => "第 2 册"
```

若没有册次，不显示该字段。

若存在 `total_volumes`：

```ts
formatVolume(2, 3) => "第 2 册 / 共 3 册"
```

### 5.4 getReleaseTag

```ts
getReleaseTag("A12-8-2", 1) => "A12-8-2_v1"
```

### 5.5 getPdfFilename

```ts
getPdfFilename("A12-8-2", 1) => "A12-8-2_v1.pdf"
```

### 5.6 getDownloadUrl

使用全站配置：

```ts
owner = "poyinte"
repo = "ebook-library"
```

生成：

```ts
https://github.com/poyinte/ebook-library/releases/download/A12-8-2_v1/A12-8-2_v1.pdf
```

### 5.7 getOutlinePath

```ts
getOutlinePath("A12-8-2", 1) => "src/data/outlines/A12-8-2_v1.json"
```

---

## 6. 分类表

创建 `src/data/classifications.yml`。

第一版只需要用于显示分类页标题和书籍所属分类，不需要做复杂树状 UI。

将用户给出的自定义分类法录入为 key-value。

示例：

```yaml
A: 马列毛主义
A1: 马克思、恩格斯著作
A11: 马克思、恩格斯著作·选集、文集、选读
A12: 马克思、恩格斯著作·单行著作
A13: 马克思、恩格斯著作·书信集、日记、函电
A2: 列宁著作
A21: 列宁著作·选集、文集、选读
A22: 列宁著作·单行著作
A3: 斯大林著作
A32: 斯大林著作·单行著作
A4: 毛泽东著作
A41: 毛泽东著作·选集、选读
A42: 毛泽东著作·单行著作
A44: 毛泽东著作·诗词
A46: 毛泽东著作·专题汇编
A5: 马克思、恩格斯、列宁、斯大林、毛泽东著作汇编
A8: 马克思主义、列宁主义、毛泽东思想的学习、研究和参考资料
A9: 张春桥、姚文元著作
A91: 张春桥、姚文元著作·选集、文集、选读
A92: 张春桥、姚文元著作·单行著作
A93: 张春桥、姚文元著作·书信集、日记、函电

B: 哲学
B1: 世界哲学
B2: 中国哲学
B22: 中国哲学·先秦哲学
B81: 逻辑学（论理学）
B812: 逻辑学·形式逻辑（名学、辩学）
B9: 无神论、宗教
B932: 无神论、宗教·神话

D: 政治
D4: 工人、农民、青年、妇女运动与组织

F: 经济
F0: 马克思主义政治经济学

H: 语言、文字
H1: 汉语
H14: 汉语·语法、修辞
H19: 汉语·汉语教学

I: 文学
I0: 文艺理论
I04: 文艺理论·文艺创作方法和经验
I1: 世界文学
I11: 世界文学·文学作品集
I109: 世界文学·文学史
I2: 中国文学
I209: 中国文学·文学史、文学思想史
I210.4: 中国文学·鲁迅著作·杂文、散文
I22: 中国文学·诗歌、韵文
I242: 中国文学·小说·古代作品
I262: 中国文学·散文、杂著·古代作品
I28: 中国文学·儿童文学、儿童读物

J: 艺术
J2: 绘画
J21: 绘画·绘画技法
J22: 绘画·中国绘画作品
J6: 音乐
J61: 音乐技术理论与方法
J642: 中国音乐作品·歌曲
J643: 中国音乐作品·戏剧音乐、配乐音乐曲

K: 历史、地理
K1: 世界史
K2: 中国史
K207: 中国史·通史·研究、考订、评论
K209: 中国史·通史·普及读物
K25: 中国史·半殖民地、半封建社会（1840—1949年）
K9: 地理
K926: 中国地理·中南地区
K926.3: 中国地理·中南地区·湖北省

T: 课程教材

Z: 综合性图书
Z2: 百科全书、类书
Z228: 中国百科全书、类书·综合性普及读物
Z3: 辞典
Z6: 期刊、连续性出版物
Z8: 图书目录、文摘、索引

P: 印刷工业
```

复分表第一版暂不用于索书号逻辑，只作为备用数据，不进入页面功能。

---

## 7. Astro Content Collection

创建 `src/content/config.ts`。

Schema 要求：

必填：

* `id`: string
* `title`: string
* `edition`: positive integer
* `date`: date

建议：

* `author`: string, optional
* `tags`: string[], default []
* `cover`: string, optional
* `total_volumes`: positive integer, optional

校验：

1. `id` 必须符合索书号规则。
2. `edition` 必须是正整数。
3. Markdown 文件名建议与 `id` 相同，例如 `A12-8-2.md`。
4. 如果 `id` 是多册书格式，页面自动显示册次。
5. 如果 `total_volumes` 存在，必须大于或等于当前册次。

---

## 8. 页面

### 8.1 首页 `/`

功能：

* 显示站点标题。
* 显示简短说明。
* 显示搜索入口。
* 显示最近发布的书籍，按 `date` 倒序。
* 显示分类入口。
* 不做 About 链接。
* 不做版权说明页链接。

### 8.2 全部书目页 `/books/`

功能：

* 显示全部书籍。
* 按索书号排序或发布日期倒序，任选一种，第一版建议发布日期倒序。
* 每个条目显示：

  * 书名
  * 作者
  * 索书号
  * 多册书显示“第 n 册”
  * 版次显示“第 n 版”
  * 日期
  * 标签
  * 下载 PDF 按钮
  * 详情页链接

### 8.3 书籍详情页 `/books/[id]/`

显示：

* 标题
* 作者，若存在
* 封面，若存在；没有封面则不显示占位图
* 下载 PDF 按钮
* 索书号：`id`
* 册次：仅多册书显示，例如“第 2 册”
* 若有 `total_volumes`，显示“第 2 册 / 共 3 册”
* 版次：第 `edition` 版
* 发布日期：`date`
* Markdown 正文
* 自动提取的目录大纲
* 标签

不要显示：

* 分类号
* 入库号
* 格式：PDF
* 排版：LaTeX
* About
* 独立版权说明

### 8.4 分类页 `/categories/[classification]/`

功能：

* 从索书号第一段识别分类号。
* 例如 `A12-8-2` 属于 `A12`。
* 页面标题显示分类表中的中文名称。
* 列出该分类下所有书。
* 第一版只做精确分类，不需要自动包含下级分类。

  * 即 `/categories/A12/` 只列出 `A12-*`。
  * 不要求 `/categories/A/` 自动列出全部 A 类下级。
* 可在后续版本优化为层级分类浏览。

### 8.5 搜索页 `/search/`

使用 Pagefind。

功能：

* 提供搜索框。
* 搜索范围包括：

  * 标题
  * 作者
  * 索书号
  * 标签
  * Markdown 正文
  * 目录内容，如果目录渲染在详情页 HTML 中，也会被索引

---

## 9. PDF 目录提取

### 9.1 原则

PDF 已经带有 LaTeX hyperref 书签。

网站不手写目录。

目录提取流程：

1. 从 PDF 提取书签。
2. 生成 JSON。
3. JSON 提交进仓库。
4. Astro 详情页读取 JSON 并显示。

不要在用户访问页面时实时读取 PDF。

不要在每次网站构建时下载全部 PDF。

### 9.2 JSON 文件命名

对于：

```yaml
id: A12-8-2
edition: 1
```

生成：

```txt
src/data/outlines/A12-8-2_v1.json
```

### 9.3 JSON 格式

```json
[
  {
    "level": 1,
    "title": "第一章 绪论",
    "page": 1
  },
  {
    "level": 2,
    "title": "第一节 问题的提出",
    "page": 3
  }
]
```

### 9.4 Python 脚本

创建 `scripts/extract-outline.py`。

要求：

* 输入 PDF 路径。
* 输入输出 JSON 路径。
* 使用 PyMuPDF。
* 读取 `doc.get_toc()`。
* 输出 `{ level, title, page }` 数组。
* 如果没有书签，输出空数组 `[]`。
* 保持中文不转义。
* 自动创建输出目录。

示例实现：

```python
import json
import sys
from pathlib import Path

import fitz


def extract_outline(pdf_path: str, out_path: str) -> None:
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    outline = [
        {
            "level": int(level),
            "title": str(title),
            "page": int(page),
        }
        for level, title, page in toc
    ]

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(outline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/extract-outline.py input.pdf output.json")
        sys.exit(1)

    extract_outline(sys.argv[1], sys.argv[2])
```

### 9.5 从 GitHub Release 下载并提取

创建 `scripts/extract-outline-from-release.sh`。

用途：

```bash
./scripts/extract-outline-from-release.sh A12-8-2 1
```

逻辑：

```bash
id="$1"
edition="$2"
tag="${id}_v${edition}"
pdf="${tag}.pdf"
out="src/data/outlines/${tag}.json"

mkdir -p .cache/pdfs
gh release download "$tag" --pattern "$pdf" --dir ".cache/pdfs" --clobber
python scripts/extract-outline.py ".cache/pdfs/$pdf" "$out"
```

要求：

* 如果参数缺失，打印用法并退出。
* 如果 `gh` 不可用，提示安装 GitHub CLI。
* 如果下载失败，退出非零状态。
* 成功后提示生成的 JSON 路径。
* JSON 文件需要提交进仓库。

---

## 10. 下载链接生成

不要在 Markdown 里手写 `download_url`。

在 `src/lib/site.ts` 中设置：

```ts
export const siteConfig = {
  githubOwner: "poyinte",
  githubRepo: "ebook-library",
};
```

在 `src/lib/bookId.ts` 或 `src/lib/books.ts` 中生成：

```ts
export function getReleaseTag(id: string, edition: number) {
  return `${id}_v${edition}`;
}

export function getPdfFilename(id: string, edition: number) {
  return `${id}_v${edition}.pdf`;
}

export function getDownloadUrl(id: string, edition: number) {
  const tag = getReleaseTag(id, edition);
  const file = getPdfFilename(id, edition);
  return `https://github.com/${siteConfig.githubOwner}/${siteConfig.githubRepo}/releases/download/${tag}/${file}`;
}
```

下载按钮统一显示：

```txt
下载 PDF · 第 n 版
```

---

## 11. 目录组件

创建 `src/components/Outline.astro`。

功能：

* 接收 `outline` 数组。
* 如果数组为空，不显示“目录”区块。
* 若有内容，显示标题“目录”。
* 按 level 缩进。
* 显示标题和页码。
* 不需要点击跳转到 PDF 内部页码，第一版只展示目录文本。
* 避免复杂样式。

示例显示：

```txt
目录

第一章 绪论  1
  第一节 问题的提出  3
  第二节 文献综述  8
第二章 正文  15
```

---

## 12. Pagefind 搜索

在 `package.json` 中设置：

```json
{
  "scripts": {
    "dev": "astro dev",
    "build": "astro build && pagefind --site dist",
    "preview": "astro preview",
    "check": "astro check",
    "validate": "tsx scripts/validate-books.ts"
  }
}
```

安装：

```bash
npm install pagefind
```

搜索页加载 Pagefind UI。

第一版可以使用 Pagefind 默认 UI，不做风格化。

---

## 13. GitHub Pages 部署

创建 `.github/workflows/deploy.yml`。

要求：

* push 到 main 时触发。
* 安装 Node。
* `npm ci`
* `npm run validate`
* `npm run build`
* 上传 `dist`
* 使用 GitHub Pages deploy action 部署。

基本流程：

```yaml
name: Deploy

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run validate
      - run: npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v4
        with:
          path: dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## 14. 校验脚本

创建 `scripts/validate-books.ts`。

校验内容：

1. 每本书的 `id` 符合规则。
2. Markdown 文件名与 `id` 一致。
3. `edition` 是正整数。
4. `date` 存在。
5. `title` 存在。
6. `total_volumes` 如果存在，必须是正整数。
7. 如果 `id` 是多册书且 `total_volumes` 存在，则 `volumeNumber <= total_volumes`。
8. 分类号必须存在于 `src/data/classifications.yml`。
9. 对每本书，检查是否存在对应 outline JSON：

   * 路径：`src/data/outlines/{id}_v{edition}.json`
   * 如果不存在，仅 warning，不 fail。
   * 因为有些 PDF 可能没有书签或尚未提取。
10. 检查是否有重复 `id`。

第一版不要校验 GitHub Release URL 是否真实存在，避免构建依赖网络。后续再加。

---

## 15. 示例内容

创建两本示例书目，方便第一版运行。

### `src/content/books/A8-3.md`

```yaml
---
id: A8-3
title: 马克思主义学习资料重排本
author: 佚名
edition: 1
date: 2026-06-17
tags:
  - 马克思主义
  - 学习资料
---

这是一份用于测试网站结构的示例书目。正文区域用于写简介、底本来源、重排说明等信息。
```

### `src/content/books/A12-8-2.md`

```yaml
---
id: A12-8-2
title: 某某著作集
author: 马克思
edition: 1
date: 2026-06-17
total_volumes: 3
tags:
  - 马克思
  - 著作集
---

这是一份用于测试多册书逻辑的示例书目。程序应从索书号中自动识别这是第 2 册。
```

创建空 outline JSON：

### `src/data/outlines/A8-3_v1.json`

```json
[]
```

### `src/data/outlines/A12-8-2_v1.json`

```json
[
  {
    "level": 1,
    "title": "第一章 示例目录",
    "page": 1
  },
  {
    "level": 2,
    "title": "第一节 子目录",
    "page": 3
  }
]
```

---

## 16. 第一版页面功能验收标准

完成后应满足：

1. `npm run dev` 可以本地启动。
2. `npm run validate` 可以运行。
3. `npm run build` 可以成功构建，并生成 Pagefind 索引。
4. 首页显示最近书籍。
5. `/books/` 显示全部书籍。
6. `/books/A8-3/` 可以打开。
7. `/books/A12-8-2/` 可以打开。
8. `A12-8-2` 详情页显示：

   * 索书号：A12-8-2
   * 册次：第 2 册 / 共 3 册
   * 版次：第 1 版
   * 下载 PDF 按钮
   * 自动目录大纲
9. `A8-3` 详情页不显示册次。
10. 页面不显示：

    * 分类号
    * 入库号
    * 格式：PDF
    * 排版：LaTeX
11. 下载按钮链接自动生成为：

    * `https://github.com/poyinte/ebook-library/releases/download/A8-3_v1/A8-3_v1.pdf`
    * `https://github.com/poyinte/ebook-library/releases/download/A12-8-2_v1/A12-8-2_v1.pdf`
12. `/search/` 可搜索书名、作者、标签、正文。
13. `/categories/A8/` 显示 A8 类书籍。
14. `/categories/A12/` 显示 A12 类书籍。
15. GitHub Actions 可构建并部署 GitHub Pages。

---

## 17. 第一版不要做的事

不要做以下内容：

1. 复杂 UI 风格化。
2. Standard Ebooks 风格复刻。
3. 深色模式。
4. 在线 PDF 阅读器。
5. 用户账号。
6. 评论。
7. CMS 后台。
8. 数据库。
9. 下载统计。
10. 自动检查 GitHub Release 是否存在。
11. 自动上传 Release。
12. PDF 全文搜索。
13. 多格式下载。
14. About 页。
15. 独立版权说明页。
16. 分类树复杂浏览。
17. 目录点击跳转 PDF 指定页。

---

## 18. README 内容

README 需要说明：

1. 这是一个静态 PDF 电子书馆。
2. 网页由 GitHub Pages 托管。
3. PDF 由 GitHub Releases 托管。
4. 书目数据在 `src/content/books/`。
5. 目录大纲在 `src/data/outlines/`，由 PDF 书签提取后提交。
6. 新增书籍流程：

```txt
1. 确定索书号，例如 A12-8-2
2. 编译 PDF，命名为 A12-8-2_v1.pdf
3. 创建 GitHub Release，tag 为 A12-8-2_v1
4. 上传 PDF 到 Release
5. 新建 src/content/books/A12-8-2.md
6. 运行 scripts/extract-outline-from-release.sh A12-8-2 1
7. 检查生成的 src/data/outlines/A12-8-2_v1.json
8. 提交 Markdown 和 JSON
9. GitHub Actions 自动部署网站
```

7. 更新新版流程：

```txt
1. edition 从 1 改为 2
2. 新 PDF 命名为 A12-8-2_v2.pdf
3. 新建 Release：A12-8-2_v2
4. 上传 PDF
5. 重新提取目录 JSON：A12-8-2_v2.json
6. 提交更新
```

---

## 19. 实施顺序

按以下顺序执行：

1. 初始化 Astro 项目。
2. 建立目录结构。
3. 实现 Content Collection schema。
4. 实现 `bookId.ts` 工具函数。
5. 建立 `classifications.yml`。
6. 添加示例书目。
7. 添加示例 outline JSON。
8. 实现 Layout 和基础组件。
9. 实现首页。
10. 实现全部书目页。
11. 实现书籍详情页。
12. 实现分类页。
13. 实现搜索页和 Pagefind。
14. 实现 Python 目录提取脚本。
15. 实现 release 下载提取脚本。
16. 实现 validate 脚本。
17. 添加 GitHub Pages workflow。
18. 编写 README。
19. 运行本地测试。
20. 修复所有 build、validate、routing 错误。

---

## 20. 最终交付物

最终提交应包含：

1. 可运行的 Astro 静态网站。
2. 极简 Markdown 书目数据。
3. 自动推导下载链接的逻辑。
4. 自动识别多册书的逻辑。
5. 自动显示“第 n 版”的逻辑。
6. 从 PDF 书签提取目录 JSON 的脚本。
7. 详情页显示目录 JSON 的组件。
8. Pagefind 搜索页。
9. 分类页。
10. GitHub Pages 部署 workflow。
11. README 使用说明。