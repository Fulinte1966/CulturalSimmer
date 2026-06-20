# PDF metadata contract

## Purpose

A newly imported PDF is the source of truth for all manually supplied book
metadata. The extraction process generates the Astro Markdown entry and all
derived assets. No title parsing, OCR, or filename guessing is permitted.

Contract version: `1`.

## Required XMP fields

| Form field | XMP path | hyperxmp key | Example | Validation |
|---|---|---|---|---|
| Call number | `dc:identifier` | `pdfidentifier` | `F0-1-1` | Existing call-number regex and known classification |
| Main title | `dc:title/rdf:Alt` | `pdftitle` | `政治经济学基础知识` | Non-empty string |
| Author | `dc:creator/rdf:Seq` | `pdfauthor` | `《政治经济学基础知识》编写组` | At least one non-empty value; use `佚名` explicitly when appropriate |
| Edition | `prism:bookEdition` | `pdfbookedition` | `1` | Positive integer |
| Summary | `dc:description/rdf:Alt` | `pdfsubject` | `系统介绍……` | Non-empty plain text |
| Language | `dc:language/rdf:Bag` | `pdflang` | `zh-CN` | Non-empty BCP 47-style value |

## Optional XMP fields

| Form field | XMP path | hyperxmp key | Example |
|---|---|---|---|
| Subtitle | `prism:subtitle/rdf:Alt` | `pdfsubtitle` | `资本主义部分` |
| Tags | `dc:subject/rdf:Bag` | `pdfkeywords` | `政治经济学,资本主义` |
| Series | `prism:publicationName/rdf:Alt` | `pdfpublication` | `青年自学丛书` |
| Volume | `prism:volume` | `pdfvolumenum` | `1` |
| Publisher | `dc:publisher` | `pdfpublisher` | `人民出版社` |
| Source | `dc:source` | `pdfsource` | `1975年版扫描本` |
| Rights | `dc:rights/rdf:Alt` | `pdfcopyright` | `版权归原作者所有` |
| License URL | `xmpRights:WebStatement` | `pdflicenseurl` | `https://example.com/license` |

Hyperxmp 5.13 emits `pdfsubtitle` as `prism:subtitle`; the extractor must read
that XMP field. It must not reinterpret `pdfsubject` as a subtitle.

## Optional custom PDF Info fields

| PDF Info key | Type | Meaning |
|---|---|---|
| `/EbookTotalVolumes` | positive integer string | Total number of volumes |
| `/EbookReadtime` | positive integer string | Manual reading-time override in minutes |

These keys contain ASCII digits only. They are optional. Automatic reading
time remains the default.

## LaTeX form

Load `hyperref` before `hyperxmp`:

```tex
\usepackage[unicode]{hyperref}
\usepackage{hyperxmp}

\hypersetup{
  pdftitle        = {政治经济学基础知识},
  pdfsubtitle     = {资本主义部分},
  pdfauthor       = {《政治经济学基础知识》编写组},
  pdfsubject      = {系统介绍资本主义政治经济学的基础知识。},
  pdfkeywords     = {政治经济学, 资本主义, 青年自学丛书},
  pdfidentifier   = {F0-1-1},
  pdfbookedition  = {1},
  pdfvolumenum    = {1},
  pdflang         = {zh-CN},
  pdfmetalang     = {zh-CN},
  pdfpubtype      = {book},
  pdfpublication  = {青年自学丛书},
  pdfpublisher    = {},
  pdfsource       = {},
  pdfcopyright    = {版权归原作者所有},
  pdflicenseurl   = {}
}

% Optional xdvipdfmx document-info values. Omit empty values.
\special{pdf:put @docinfo <<
  /EbookTotalVolumes (2)
>>}
```

The desired future template-facing form is:

```tex
\EbookMetadata{
  id             = F0-1-1,
  title          = 政治经济学基础知识,
  subtitle       = 资本主义部分,
  author         = 《政治经济学基础知识》编写组,
  edition        = 1,
  volume         = 1,
  total-volumes  = 2,
  description    = 系统介绍资本主义政治经济学的基础知识。,
  keywords       = {政治经济学,资本主义,青年自学丛书},
  language       = zh-CN,
  series         = 青年自学丛书
}
```

This repository defines the contract. Implementing `\EbookMetadata` in the
external active LaTeX template is a separate task.

## Extracted type

```py
@dataclass
class PdfBookMetadata:
    id: str
    title: str
    subtitle: str | None
    author: str
    edition: int
    description: str
    tags: list[str]
    language: str
    series: str | None
    volume: int | None
    total_volumes: int | None
    readtime: int | None
    publisher: str | None
    source: str | None
    rights: str | None
    license_url: str | None
```

Use `document.get_xml_metadata()` and a safe XML parser. Handle simple
elements, `rdf:Alt`, `rdf:Seq`, and `rdf:Bag`. Normalize strings to Unicode NFC,
trim surrounding whitespace, remove empty optional values, and deduplicate
tags while preserving their first occurrence.

## Validation

Reject the import when:

- XMP is absent;
- a required field is absent or empty;
- call number or edition is invalid;
- classification is not present in `classifications.yml`;
- `prism:volume` conflicts with the volume parsed from the ID;
- total volumes is smaller than the current volume;
- manual readtime is not a positive integer;
- the PDF is encrypted or requires a password;
- it has zero pages;
- any page differs from the A5 aspect ratio by more than one percent.

Subtitle is optional. Its absence is not an error.

## Derived values

- Classification and work ID come from the call number.
- Release date comes from the intake Release publication timestamp.
- Cover and spine come from the first page.
- Outline comes from PDF bookmarks.
- Page count and reading estimate come from PDF content.
- Canonical tag is `{id}_v{edition}`.
- Canonical filename is `{id}_v{edition}.pdf`.
- Download URL is derived using existing `siteConfig` behavior.

## Generated Markdown

```yaml
---
id: F0-1-1
title: 政治经济学基础知识
subtitle: 资本主义部分
author: 《政治经济学基础知识》编写组
edition: 1
date: 2026-06-21
total_volumes: 2
tags:
  - 政治经济学
  - 资本主义
  - 青年自学丛书
---
```

The Markdown body is the extracted summary as plain text. Write frontmatter
through a structured YAML serializer, not ad hoc string escaping.

## Generated manifest

Path: `src/data/manifests/{id}_v{edition}.json`.

```json
{
  "schema_version": 1,
  "id": "F0-1-1",
  "edition": 1,
  "source_release_id": 123,
  "source_asset_id": 456,
  "source_sha256": "hex digest",
  "generated_at": "ISO-8601 timestamp",
  "metadata": {}
}
```

The manifest is an audit record. Astro continues to read the generated content
entry; it must not create a second runtime book-data source.

## Legacy behavior

The current `example/F0.1.pdf` has no complete XMP metadata and must not pass
strict ingestion. A local `--assets-only` option may continue generating cover,
spine, outline, and reading data for legacy PDFs, but GitHub ingestion must
always use strict metadata mode.

