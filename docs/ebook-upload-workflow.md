# 电子书上传工作流

本文档记录当前电子书馆的 PDF 上传、自动导入、正式发布和网页部署流程。

## 核心原则

- PDF 是人工录入书目元数据的唯一来源。
- 不根据文件名、Release 标题或正文内容猜测书目信息。
- 不手写 `downloadUrl`、`releaseTag`、`pdfFilename`、`classification` 或 `volume`。
- 索书号和版次共同组成正式发布键：`F0-1-1_v1`。
- 网页显示使用出版语义：`2026 年 6 月第 1 版`。
- PDF 托管在 GitHub Releases；网页是 GitHub Pages 上的 Astro 静态站。

## 上传者工作流

1. 制作 PDF，并写入完整 XMP 元数据。
2. 在 GitHub 创建临时 Release。
3. 临时 Release tag 必须以 `ingest-` 开头，建议格式：

   ```txt
   ingest-YYYYMMDD-索书号-v版次
   ```

   示例：

   ```txt
   ingest-20260707-F0-1-1-v1
   ```

4. 在临时 Release 中上传且只上传一个 PDF。
5. 发布临时 Release。
6. 等待 `Ingest PDF` GitHub Actions 工作流完成。
7. 工作流成功后，`main` 分支会被自动提交，随后 `Deploy` 工作流自动部署网站。

临时 Release 的标题和 PDF 文件名不会被用作书目数据来源。

## 自动导入流程

```text
临时 ingest-* Release 发布
  -> 下载 Release 中的 PDF
  -> 要求恰好 1 个 PDF
  -> 计算 PDF SHA-256
  -> 读取并校验 PDF XMP 元数据
  -> 计算正式 tag 和文件名
  -> 检查重复 Release、Git tag、Markdown 和生成资产
  -> 生成 Markdown、manifest、封面、书脊、目录和阅读数据
  -> 运行检查、测试和生产构建
  -> 创建正式 Release
  -> 上传规范化 PDF
  -> 提交生成文件到 main
  -> 删除临时 Release 和临时 tag
  -> main push 触发 GitHub Pages 部署
```

## 必需 PDF 元数据

| 含义 | XMP 字段 | 示例 | 规则 |
|---|---|---|---|
| 索书号 | `dc:identifier` | `F0-1-1` | 必须符合索书号正则，且分类号已存在 |
| 主标题 | `dc:title` | `政治经济学基础知识` | 非空 |
| 作者 | `dc:creator` | `《政治经济学基础知识》编写组` | 非空；无名作者显式写 `佚名` |
| 版次 | `prism:bookEdition` | `1` | 正整数 |
| 简介 | `dc:description` | `系统介绍……` | 非空 |
| 语言 | `dc:language` | `zh-CN` | 非空 |

## 可选 PDF 元数据

| 含义 | XMP 字段或 PDF Info 键 | 示例 |
|---|---|---|
| 副标题 | `prism:subtitle` | `资本主义部分` |
| 标签 | `dc:subject` | `政治经济学, 资本主义` |
| 丛书 | `prism:publicationName` | `青年自学丛书` |
| PDF 内部卷号 | `prism:volume` | `1` |
| 出版者 | `dc:publisher` | `人民出版社` |
| 来源 | `dc:source` | `1975年版扫描本` |
| 权利说明 | `dc:rights` | `版权归原作者所有` |
| 授权说明 URL | `xmpRights:WebStatement` | `https://example.com/license` |
| 总册数 | `/EbookTotalVolumes` | `2` |
| 人工阅读时间 | `/EbookReadtime` | `120` |

## 正式发布命名

正式发布键由索书号和版次组成：

```txt
{bookId}_v{edition}
```

示例：

```txt
F0-1-1_v1
```

对应正式 PDF 文件名：

```txt
F0-1-1_v1.pdf
```

网页下载链接自动生成：

```txt
https://github.com/Fulinte1966/CulturalSimmer/releases/download/F0-1-1_v1/F0-1-1_v1.pdf
```

## 自动生成文件

以 `F0-1-1` 第 1 版为例，导入成功后提交以下文件：

```txt
src/content/books/F0-1-1.md
src/data/manifests/F0-1-1_v1.json
src/data/outlines/F0-1-1_v1.json
src/data/reading/F0-1-1_v1.json
public/covers/F0-1-1_v1.png
public/covers/F0-1-1_v1_spine.png
```

下载用 PDF 不进入 Git 历史，只保存在 GitHub Release。

## 新版发布规则

同一本书发布新版时：

- `dc:identifier` 保持不变。
- `prism:bookEdition` 递增。
- 新正式 Release 为新的 `{bookId}_v{edition}`。
- Markdown 书目记录更新为最新版。
- 网页下载入口指向当前 Markdown 记录的最新版。

示例：

```txt
F0-1-1_v1 -> 2026 年 6 月第 1 版
F0-1-1_v2 -> 2026 年 7 月第 2 版
```

## 重复检查

导入会拒绝覆盖已有发布。以下任一项存在都会失败：

- 正式 GitHub Release；
- 正式 Git tag；
- 同一书目 Markdown 已记录相同 `edition`；
- 同名 manifest；
- 同名封面、书脊、目录或阅读数据文件。

## 失败与回滚

- 元数据、重复检查、测试或构建失败：不创建正式 Release，不提交。
- 正式 Release 创建成功但提交或推送失败：删除正式 Release 和正式 tag。
- 推送成功后临时 Release 删除失败：不回滚已发布书籍，只在 Actions 摘要中提示。
- 不使用 force push。

## 部署流程

导入工作流提交到 `main` 后，`Deploy` 工作流自动运行：

```text
npm ci
npm run test:ui
npm run validate
npm run check
npm run build
```

部署工作流还会每天北京时间 00:00 定时运行一次，用于刷新静态天气等每日数据。

## 上传前建议检查

上传前建议人工确认：

- PDF 能正常打开，且不是加密文件。
- PDF XMP 元数据完整。
- 索书号分类存在于 `src/data/classifications.yml`。
- 版次没有和已有发布重复。
- 临时 Release 中只有一个 PDF。
- 临时 tag 以 `ingest-` 开头。
