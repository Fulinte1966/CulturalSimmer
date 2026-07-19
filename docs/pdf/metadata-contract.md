# PDF 元数据契约

**适用对象：** 电子书制作者、LaTeX 模板维护者与入库脚本维护者。

契约版本：`1`。新上传 PDF 是人工书目元数据的唯一事实来源。入库程序不得从文件名、Release 标题、OCR 或正文猜测书名、索书号、版次和内容提要。

## 必填字段

| 含义 | XMP 路径 | `hyperxmp` 键 | 校验 |
| --- | --- | --- | --- |
| 索书号 | `dc:identifier` | `pdfidentifier` | 符合书号正则，分类号存在 |
| 主标题 | `dc:title/rdf:Alt` | `pdftitle` | 非空 |
| 版次 | `prism:bookEdition` | `pdfbookedition` | 正整数，并符合仓库预期版次 |
| 内容提要 | `dc:description/rdf:Alt` | `pdfsubject` | 非空，不得为占位文字 |
| PDF 创建日期 | `xmp:CreateDate` | 由 PDF 工具写入 | 合法 ISO 日期，用于派生 `editionDate` |

## 可选字段

| 含义 | XMP 路径 | `hyperxmp` 键 |
| --- | --- | --- |
| 作者、编者、整理者 | `dc:creator/rdf:Seq` | `pdfauthor` |
| 语言 | `dc:language/rdf:Bag` | `pdflang` |
| 副标题 | `prism:subtitle/rdf:Alt` | `pdfsubtitle` |
| 标签 | `dc:subject/rdf:Bag` | `pdfkeywords` |
| 丛书 | `prism:publicationName/rdf:Alt` | `pdfpublication` |
| PDF 内部卷号 | `prism:volume` | `pdfvolumenum` |
| 出版者 | `dc:publisher` | `pdfpublisher` |
| 来源 | `dc:source` | `pdfsource` |
| 权利说明 | `dc:rights/rdf:Alt` | `pdfcopyright` |
| 权利说明 URL | `xmpRights:WebStatement` | `pdflicenseurl` |
| Z-Library 页面 URL | `prism:url` | `pdfurl` |

提取器接受 PRISM basic metadata `2.1` 与 `3.0` 命名空间。非 LaTeX 制作的 PDF 可用 `dc:relation` 作为相关资源 URL 后备。URL 必须为 HTTP(S)。缺少语言时使用 `zh-CN`；作者和副标题均可为空。

`hyperxmp` 的 `pdfsubject` 对应内容提要，不得解释为副标题。副标题经 Unicode NFC 和首尾空白清理后原样传递，入库和网页不得自动添加、删除或替换括号。

## 内部书号与分类

书号格式固定为 `<分类号>-<作品序号>[-<册次>]`。分类号只允许使用
`src/data/classifications.yml` 中存在的代码；正则匹配只负责结构，不能代替
分类表校验。

当前分类为 A—K。B—K 只使用单字母大类；A 允许 A1、A2、A3、A4、A5、
A8、A9 一层子类。不得继续使用历史测试代码 A93、B0、F0、T 或 Z。

例如：`A9-1` 表示 A9 类第 1 种作品，`B-1` 表示 B 类第 1 种作品，
`F-1-1` 表示 F 类第 1 种作品的第 1 册。版次不属于书号，继续由
`prism:bookEdition` 单独表达。

## 自定义 PDF Info

| PDF Info 键 | 类型 | 含义 |
| --- | --- | --- |
| `/EbookTotalVolumes` | ASCII 正整数字符串 | 全书总册数 |

该字段可选。若索书号或 `prism:volume` 表示当前册数，则总册数不得小于当前册数。

## LaTeX 接口

仓库提供 `docs/latex/culturalsimmer-ebook-metadata.sty`。模板只在一个位置定义元数据，其余排版位置通过公开访问器复用：

```tex
\usepackage{culturalsimmer-ebook-metadata}

\EbookMetadata{
  id = F-1-1,
  title = 政治经济学基础知识,
  subtitle = （资本主义部分）,
  author = 《政治经济学基础知识》编写组,
  edition = 2,
  volume = 1,
  total-volumes = 1,
  description = 系统介绍资本主义政治经济学的基础知识。,
  keywords = {政治经济学,资本主义},
  language = zh-CN,
  series = 青年自学丛书,
  publisher = 上海人民出版社,
  source = 1975 年第 2 版,
  rights = 权利归原作者及相关权利人所有,
  license-url = {},
  zlibrary-url = https://z-library.sk/book/...
}

当前版次：\EbookEdition
内部书号：\EbookId
```

样式文件内部按 `hyperref`、`hyperxmp` 的顺序加载依赖并写入 XMP；有 `total-volumes` 时通过 `xdvipdfmx` 的 `\special` 写入自定义 PDF Info。

## 提取结果

`scripts/extract_metadata.py` 返回：

```py
@dataclass
class PdfBookMetadata:
    id: str
    title: str
    edition: int
    edition_date: str
    edition_date_source: str
    pdf_create_date: str
    description: str
    tags: list[str]
    language: str
    author: str | None = None
    subtitle: str | None = None
    series: str | None = None
    volume: int | None = None
    total_volumes: int | None = None
    publisher: str | None = None
    source: str | None = None
    rights: str | None = None
    license_url: str | None = None
    zlibrary_url: str | None = None
```

XML 使用安全解析器读取，支持简单元素、`rdf:Alt`、`rdf:Seq` 和 `rdf:Bag`。字符串统一 NFC、清理首尾空白；空可选值移除；标签按首次出现顺序去重。

## 严格校验

以下情况必须拒绝入库：

- XMP 缺失、XML 非法或必填字段为空；
- 索书号格式、分类号或版次非法；
- `prism:volume` 与索书号册次冲突；
- 总册数小于当前册数；
- 外部资源 URL 不是 HTTP(S)；
- PDF 加密、需要密码或页数为零；
- 任一页面与 A5 纵横比相差超过 1%；
- 内容提要为“暂无简介”“待补充”或包含 `TODO`。

严格入库不接受缺字段的历史 PDF。仅本地资产重建可以使用专用兼容模式；GitHub 入库始终执行完整契约。

## 派生值与文件

- `editionDate` 取 `xmp:CreateDate` 的 `YYYY-MM`；
- 分类号和作品编号从索书号解析；
- 正式 tag 与 PDF 文件名固定为 `{id}_v{edition}` 和 `{id}_v{edition}.pdf`；
- 封面和书脊取 PDF 第 1 页；
- 目录取 PDF bookmarks；
- 页数、字数与文件大小从 PDF 生成；
- 下载地址由仓库 owner、repo、正式 tag 和文件名派生。

书目文件位于 `src/content/books/{id}.md`，保存书目级字段和有序 `editions[]`。版本 manifest 位于 `src/data/manifests/{id}_v{edition}.json`，当前 schema 为 `4`，记录来源 Release、SHA-256、GitHub asset digest、PDF 属性、快照、changelog 和生成时间。阅读数据位于 `src/data/reading/{id}_v{edition}.json`，使用 `pageCount`、`fileSizeBytes`、`cjkCharacterCount` 和 `latinTokenCount`。

结构化 YAML 和 JSON 必须通过序列化器生成，不得拼接转义字符串。Astro 继续读取书目 Markdown；manifest 是审计记录，不构成第二套运行时书目数据。

## 参考

- [Adobe XMP specification](https://developer.adobe.com/xmp/docs/)
- [PRISM metadata specification](https://www.prismstandard.org/specifications/)
- [`hyperxmp` package documentation](https://ctan.org/pkg/hyperxmp)
- [`hyperref` package documentation](https://ctan.org/pkg/hyperref)
