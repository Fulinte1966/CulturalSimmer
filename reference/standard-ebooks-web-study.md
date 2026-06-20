# Standard Ebooks Web 代码学习总结

> 仓库: `https://github.com/standardebooks/web`
> 克隆位置: `reference/web/`
> 技术栈: PHP (自研模板引擎) + MariaDB + Manticore Search + 纯 CSS (无 JS 框架)

---

## 一、整体架构

### 1.1 技术选型

| 层 | 技术 | 说明 |
|---|---|---|
| 后端语言 | PHP | 无框架，自研路由+模板 |
| 数据库 | MariaDB | `Ebooks` 表为主，约20个表 |
| 搜索引擎 | Manticore Search | MySQL协议，端口9306，`morphology = 'lemmatize_en'` |
| 前端 | 纯 HTML/CSS | **零 JavaScript 依赖**（仅一个 XSLT polyfill 给 ereader） |
| 路由 | Apache mod_rewrite | PHP 内部有 `Http::$Request->Route()` |
| 模板 | 自研 `TemplateBase` | `Template::MethodName()` → `templates/MethodName.php` |

### 1.2 URL 路由结构

```
/ebooks                              → www/ebooks/index.php      (浏览/搜索页)
/ebooks/{author}/{title}/{translator} → www/ebooks/http-get.php   (书本详情页)
/subjects/{tag}                       → 重写至 /ebooks?tags[]={tag}
/collections/{name}                   → www/collections/http-get.php
/feeds/{atom|opds|rss}/all           → www/feeds/search.php
```

路由规则定义在 `config/apache/rewrites/ebooks.conf`。

### 1.3 目录结构

```
config/
  apache/rewrites/       # Apache rewrite 规则
  manticore/ebooks.sql   # Manticore 搜索索引定义
  sql/se/Ebooks.sql      # MariaDB 表结构
lib/
  Ebook.php              # 核心模型 (93KB, ~2800行)
  SearchDb.php           # 搜索数据库封装
  Constants.php          # 全局常量
  Template.php           # 模板方法注册
  Enums/                 # 枚举 (EbookSortType, EbookFormatType, ViewType等)
templates/
  SearchForm.php         # 搜索表单组件
  EbookGrid.php          # 书本网格/列表组件
  RealisticEbook.php     # 3D书本模型组件
  EbookCarousel.php      # 相关书本轮播
  Header.php / Footer.php
www/
  ebooks/index.php       # 浏览页入口
  ebooks/http-get.php    # 详情页入口
  ebooks/download.php    # 下载处理
  css/core.css           # 主样式表 (~4700行)
  images/logo-spine.svg  # 书脊 SVG
  images/pages-texture.svg # 书页纹理 SVG
```

---

## 二、Browse Ebooks 页面 —— 搜索、布局、过滤

### 2.1 入口和处理流程

**文件**: `www/ebooks/index.php`

核心查询参数（第4-10行）:
```php
$page     = GET['page']       // 页码，默认1
$perPage  = GET['per-page']   // 每页数量，默认12 (EBOOKS_PER_PAGE)
$query    = GET['query']      // 搜索关键词
$tags     = GET['tags']       // 主题标签过滤（数组）
$view     = GET['view']       // Grid 或 List
$sort     = GET['sort']       // Default/Newest/AuthorAlpha/ReadingEase/Length/Popularity/Relevance
```

数据获取（第106行）:
```php
$ebooks = Ebook::GetAllByFilter($query, $tags, $sort, $view, $perPage, $page, $totalResultCount);
```

### 2.2 搜索引擎 —— Manticore

**文件**: `lib/SearchDb.php`

- 连接: MySQL协议，`127.0.0.1:9306`
- `EscapeMatch()`: 转义搜索特殊字符 (`"`, `-`, `(`, `)` 等)
- `QueryMatch()`: 执行 `match()` 查询，语法错误时自动回退
- `GetLastQueryTotalResultCount()`: `SHOW meta like 'total%'` 获取总数

**索引定义** (`config/manticore/ebooks.sql`):
```sql
create table ebooks (
    id bigint,
    Title text, FullTitle text, AlternateTitle text,
    Authors text, AuthorSortName string,
    Collections text, Tags text, TagUrlNames text,
    IsPlaceholder int,
    ReadingEase float,
    WordCount int,
    DownloadsPast30Days int,
    EbookCreated timestamp
) morphology = 'lemmatize_en' index_exact_words = '1';
```

**搜索权重** (`lib/Constants.php`):
```php
EBOOK_SEARCH_WEIGHT_TITLE       = 10
EBOOK_SEARCH_WEIGHT_AUTHORS     = 8
EBOOK_SEARCH_WEIGHT_COLLECTIONS = 3
```

### 2.3 数据库查询策略 (`lib/Ebook.php::GetAllByFilter()`, 第2559行)

**无搜索词时**（纯 SQL）:
- 直接查询 MariaDB `Ebooks` 表
- 可选 JOIN `EbookTags` 过滤标签
- 支持排序: `AuthorAlpha`, `ReadingEase`, `Length`(WordCount), `Popularity`(DownloadsPast30Days), `Newest`(EbookCreated)

**有搜索词时**（混合查询）:
1. 先查询 Manticore: `SELECT id FROM ebooks WHERE match(?) ... ORDER BY weight() DESC`
2. 获取匹配 ID 列表
3. 再到 MariaDB: `SELECT * FROM Ebooks WHERE EbookId IN (...) ORDER BY find_in_set(EbookId, ...)` 保持 Manticore 的排序顺序
4. 标签过滤转为 `"(tag) original_query"` 格式追加

### 2.4 搜索表单

**文件**: `templates/SearchForm.php`

- 纯 HTML `<form method="GET" action="/ebooks">` —— 无任何 JS
- 主题过滤: `<select multiple name="tags[]">` (普通浏览器) 或 `<select>` (ereader)
- 关键词: `<input type="search" name="query">`
- 排序: `<select name="sort">` (Relevance 仅在有关键词时显示)
- 视图: `<select name="view">` (Grid / List)
- 每页: `<select name="per-page">` (12 / 24 / 48)
- 所有切换触发整页刷新（无 AJAX）

### 2.5 书本列表展示 —— Grid / List

**文件**: `templates/EbookGrid.php`

**Grid 视图** (第46-49行):
```php
<ol class="ebooks-list grid">
  <? foreach($ebooks as $ebook): ?>
    <li>
      <a href="<?= $ebook->Url ?>">
        <picture><!-- AVIF + JPEG 封面缩略图 --></picture>
        <p><?= $ebook->Title ?></p>
        <p><?= $ebook->AuthorsHtml ?></p>
      </a>
    </li>
```

**List 视图** (第50-75行):
```php
<ol class="ebooks-list list">
  <li> <!-- 封面缩略图(6rem) + 详细信息 -->
    <p><?= $ebook->Title ?> (<?= $ebook->AuthorsHtml ?>)</p>
    <p><?= $ebook->ContributorsHtml ?></p>
    <p><?= number_format($ebook->WordCount) ?> words • <?= $ebook->ReadingEase ?> reading ease</p>
    <? foreach($ebook->Tags as $tag): ?><a href="<?= $tag->Url ?>"><?= $tag->Name ?></a><? endforeach ?>
  </li>
```

**CSS 关键样式** (`www/css/core.css`):
- Grid: `grid-template-columns: repeat(4, minmax(0, 1fr))`，4列等宽，gap 4rem
- List: Flexbox 单列，max-width 30rem，每项内部 `grid-template-columns: 6rem 1fr`

### 2.6 分页

**实现** (在 `www/ebooks/index.php` 第141-151行，直接内联):
```php
<nav class="pagination">
  <? if($page > 1): ?>
    <a rel="prev" href="?query=...&page=<?= $page - 1 ?>">Back</a>
  <? else: ?>
    <span aria-disabled="true">Back</span>
  <? endif ?>
  <ol>
    <? foreach($pages as $p): ?>
      <li><? if($p == $page): ?><em><?= $p ?></em><? else: ?><a href="..."><?= $p ?></a><? endif ?></li>
    <? endforeach ?>
  </ol>
  <!-- Next 链接同理 -->
</nav>
```

CSS 用伪元素实现页码折叠：当前页附近显示 `...`（`core.css` 第2353-2379行）。

---

## 三、书本详情页 —— 阅读数据信息

### 3.1 详情页结构

**文件**: `www/ebooks/http-get.php`

```
article.ebook
  ├── header (hero image + 标题/作者)
  ├── aside#reading-ease    ← "56,426 words (3h 26m) with reading ease of 77 (fairly easy)"
  ├── section#description   (LongDescription)
  ├── section#read-free     (下载 + 在线阅读 + 3D 书本模型)
  ├── section#history       (Git 提交历史)
  ├── section#details       (GitHub/Wikipedia 链接)
  ├── section#sources       (转录来源、扫描件)
  ├── section#improve       (改进链接)
  └── section#more-ebooks   (相关书本轮播 Carousel)
```

### 3.2 阅读数据的来源和计算

**数据源头**: SE 工具链在生产电子书时计算，写入 `content.opf`:
```xml
<meta property="se:word-count">56426</meta>
<meta property="se:reading-ease.flesch">77.0</meta>
```

**解析入库** (`lib/Ebook.php` 第1029-1041行):
```php
$wordCountElement = $xml->xpath('/package/metadata/meta[@property="se:word-count"]') ?: [];
$ebook->WordCount = (int)$wordCountElement[0];  // 存入 MariaDB: WordCount int(10) unsigned

$readingEaseElement = $xml->xpath('/package/metadata/meta[@property="se:reading-ease.flesch"]') ?: [];
$ebook->ReadingEase = (float)$readingEaseElement[0];  // 存入 MariaDB: ReadingEase float
```

**运行时计算**（lazy-loaded via PHP `__get` Accessor trait）:

**阅读时间** (`lib/Ebook.php` 第550-579行):
```php
function GetReadingTime(): string {
    $readingTime = ceil($this->WordCount / AVERAGE_READING_WORDS_PER_MINUTE);
    // AVERAGE_READING_WORDS_PER_MINUTE = 275 (lib/Constants.php:99)
    // 输出: "3 hours 26 minutes" 或 "45 minutes" 等
}
```

**阅读难度描述** (`lib/Ebook.php` 第522-548行):
```php
function GetReadingEaseDescription(): string {
    // Flesch-Kincaid 分数映射:
    // > 89        → "very easy"
    // 79-89       → "easy"
    // 70-79       → "fairly easy"
    // 60-69       → "average difficulty"
    // 50-59       → "fairly difficult"
    // 40-49       → "difficult"
    // < 40        → "very difficult"
}
```

### 3.3 阅读数据的显示

**详情页** (`www/ebooks/http-get.php` 第105-108行):
```php
<aside id="reading-ease">
    <? if($ebook->WordCount !== null): ?>
        <meta property="schema:wordCount" content="<?= $ebook->WordCount ?>"/>
        <p>
            <?= number_format($ebook->WordCount) ?> words
            (<?= $ebook->ReadingTime ?>)
            with a reading ease of <?= $ebook->ReadingEase ?>
            (<?= $ebook->ReadingEaseDescription ?>)
        </p>
    <? endif ?>
</aside>
```

**最终输出效果**:
> **56,426 words (3 hours 26 minutes) with a reading ease of 77 (fairly easy)**

**列表视图** (`templates/EbookGrid.php` 第64行):
```php
<p><?= number_format($ebook->WordCount) ?> words • <?= $ebook->ReadingEase ?> reading ease</p>
```

---

## 四、Download 栏目 + 3D 书本模型

### 4.1 下载栏目布局

**文件**: `www/ebooks/http-get.php` 第136-243行

```
section#read-free
  ├── h2 "Read free"
  ├── div.downloads-container (flex 横向布局)
  │   ├── figure.realistic-ebook  ← 3D 书本模型
  │   └── div
  │       ├── section#download
  │       │   ├── h3 "Download for ereaders"
  │       │   └── ul
  │       │       ├── li  Compatible epub   "All devices except Kindles and Kobos"
  │       │       ├── li  azw3              "Kindle devices and apps..."
  │       │       ├── li  kepub             "Kobo devices and apps..."
  │       │       └── li  Advanced epub     "Latest technology not yet fully supported..."
  │       └── section#read-online
  │           ├── li  "Start from the table of contents"
  │           └── li  "Read on one page" (附文件大小)
```

### 4.2 四种下载格式

| 格式 | 文件类型 | MIME | 目标设备 |
|------|----------|------|----------|
| Compatible epub | `*.epub` | `application/epub+zip` | 所有设备（除 Kindle/Kobo） |
| azw3 | `*.azw3` | `application/x-mobipocket-ebook` | Kindle 设备和应用 |
| kepub | `*.kepub.epub` | `application/kepub+zip` | Kobo 设备和应用 |
| Advanced epub | `*_advanced.epub` | `application/epub+zip` | 支持最新技术的设备 |

格式发现 (`lib/Ebook.php` 第770-802行) 通过文件系统 glob:
```php
// Compatible epub: *.epub (排除 advanced 和 kepub)
// Advanced epub: *_advanced.epub
// Kepub: *.kepub.epub
// Azw3: *.azw3
```

每种格式都有 Schema.org RDFa 元数据、CSS 图标（SVG `::before` 伪元素）和设备兼容说明。

### 4.3 下载处理流程

**文件**: `www/ebooks/download.php`

1. 检测 `download-count` cookie 决定是否显示致谢页
2. 格式识别: `EbookFormatType::FromFilename($filename)`
3. 频率限制: 未登录用户 30秒/6小时 窗口
4. 文件服务: Apache `X-Sendfile` 头（高效传输大文件）
5. 致谢页: 显示封面 + 捐赠呼吁

### 4.4 3D 书本模型 —— 纯 CSS 实现（真·零 JS）

**这不是 3D 模型，没有 Three.js / WebGL / Canvas！** 而是一个用 CSS transform + 伪元素构建的 3D 视觉效果。

#### 4.4.1 HTML 模板

**文件**: `templates/RealisticEbook.php`

```php
<figure class="realistic-ebook <?= $sizeClass ?>">  <!-- small/medium/large/xlarge/xxlarge -->
    <picture>
        <source srcset="cover.avif 2x, cover.avif 1x" type="image/avif"/>
        <source srcset="cover.jpg 2x, cover.jpg 1x" type="image/jpg"/>
        <img src="cover.jpg" alt="" height="363" width="242"/>
        <!-- fallback: <img src="logo-spine.svg" class="no-cover"/> -->
    </picture>
</figure>
```

**厚度分级** (基于 WordCount):
| 字数 | CSS class | --size | 用途 |
|------|-----------|--------|------|
| < 100K | `.small` | 1rem | 薄书 |
| 100K-200K | `.medium` (默认) | 1.5rem | 中等 |
| 200K-300K | `.large` | 2rem | 厚书 |
| 300K-400K | `.xlarge` | 2.5rem | 很厚 |
| > 400K | `.xxlarge` | 3rem | 巨著 |

#### 4.4.2 CSS 3D 技术实现

**文件**: `www/css/core.css` 第3264-3374行

**基本原理**: 用 CSS `skewY` / `skewX` / `rotate` 模拟等距透视，共 5 个视觉层：

```
┌──────────────────────────────────────────────────────┐
│  🔲 figure::after  (spine 书脊)                      │
│     transform: skewY(45deg) + logo-spine.svg 背景    │
│     width: var(--size)，位置在封面左侧                │
│                                                      │
│  🔲 picture::before  (pages 书页)                    │
│     transform: rotate(90deg) skewY(-45deg)            │
│     background: pages-texture.svg (虚线纹理)          │
│     白色块，模拟纸张截面                               │
│                                                      │
│  🔲 picture::after  (back board 背板)                 │
│     background: #222 深色矩形                         │
│     位置在封面左后方                                   │
│                                                      │
│  🔲 figure::before  (shadow 阴影)                     │
│     transform: skewX(45deg) + blur(10px)              │
│     半透明黑色，投射在地面                             │
│                                                      │
│  🖼️ img  (cover 封面)                                │
│     transform: skewY(-10deg) scale(.75)              │
│     border-radius: 0 5px 5px 0 (右侧圆角)            │
└──────────────────────────────────────────────────────┘
```

**关键 CSS 代码**:

```css
/* 整体倾斜+缩放 */
figure.realistic-ebook {
    transform: skewY(-10deg) scale(.75);
    width: 242px;
    margin-left: -2rem;
    align-self: flex-start;
}

/* 书脊（::after 伪元素） */
figure.realistic-ebook::after {
    content: "";
    width: calc(var(--size) + 2px);
    height: 100%;
    left: calc(-1 * var(--size));
    background: url("/images/logo-spine.svg") #222;
    transform: skewY(45deg);
    transform-origin: right;
    z-index: -1;
}

/* 书页（picture::before 伪元素） */
figure.realistic-ebook picture::before {
    content: "";
    width: var(--size);
    height: 235px;
    background: url("/images/pages-texture.svg") #fff;
    transform: rotate(90deg) skewY(-45deg);
    transform-origin: bottom;
    z-index: -1;
}

/* 背板（picture::after 伪元素） */
figure.realistic-ebook picture::after {
    content: "";
    width: 100%;
    height: 100%;
    background: #222;
    left: calc(-1 * var(--size));
    transform: translateY(calc(-1 * var(--size)));
    z-index: -2;
}

/* 阴影（::before 伪元素） */
figure.realistic-ebook::before {
    content: "";
    background: rgba(0, 0, 0, .5);
    transform: skewX(45deg);
    filter: blur(10px);
    border-radius: 2rem;
    z-index: -1;
}
```

**Hover 动画** (`core.css` 第4660-4684行):
```css
@media(prefers-reduced-motion: no-preference) {
    a:hover figure.realistic-ebook img {
        filter: brightness(1.15);
        transform: translateY(-.5rem); /* 封面上浮 + 变亮 */
    }
    /* 背板、书页、书脊、阴影全部联动位移，产生 3D 抬起效果 */
}
```

**响应式**: 视口 < 580px 时 `figure.realistic-ebook { display: none }` —— 移动端完全隐藏。

---

## 五、数据库 Schema —— Ebooks 表

**文件**: `config/sql/se/Ebooks.sql`

```sql
CREATE TABLE `Ebooks` (
  `EbookId` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Identifier` varchar(511) NOT NULL,           -- URL 标识符
  `WwwFilesystemPath` varchar(511) NULL,        -- 文件系统路径
  `Title` varchar(255) NOT NULL,
  `FullTitle` varchar(255) NULL,
  `AlternateTitle` varchar(255) NULL,
  `Description` text NULL,
  `LongDescription` text NULL,
  `Language` varchar(10) NULL,
  `WordCount` int(10) unsigned NULL,            -- 字数（来自 OPF）
  `ReadingEase` float NULL,                     -- Flesch 分数（来自 OPF）
  `EpubUrl` varchar(511) NULL,                  -- 四种格式下载URL
  `AdvancedEpubUrl` varchar(511) NULL,
  `KepubUrl` varchar(511) NULL,
  `Azw3Url` varchar(511) NULL,
  `KindleCoverUrl` varchar(511) NULL,
  `DistCoverUrl` varchar(511) NULL,
  `GitHubUrl` varchar(255) NULL,
  `WikipediaUrl` varchar(255) NULL,
  `EbookCreated` datetime NULL,
  `EbookUpdated` datetime NULL,
  `TextSinglePageByteCount` bigint unsigned NULL,
  `DownloadsPast30Days` int(10) unsigned NOT NULL DEFAULT 0,
  `DownloadsTotal` int(10) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`EbookId`),
  UNIQUE KEY (`Identifier`),
  KEY `idxPopularity` (`DownloadsPast30Days` DESC, `EbookCreated` DESC)
);
```

关联表: `EbookTags`, `Contributors`, `EbookSources`, `CollectionEbooks` 等。

---

## 六、核心设计模式与可借鉴之处

### 6.1 零 JavaScript 架构
- **所有交互**: 搜索、过滤、排序、分页、视图切换全部通过 `<form method="GET">` + 服务器渲染
- **OpenSearch**: `<link rel="search">` 支持浏览器地址栏直接搜索
- **优势**: 极快、无障碍友好、SEO 天然最优、零 bundle size

### 6.2 搜索架构（混合查询）
- **Manticore**: 处理全文搜索 + 相关性排序
- **MariaDB**: 处理结构化过滤 + 关联查询
- **分离读写**: Manticore 仅存索引，实物数据在 MariaDB
- **`find_in_set()` 技巧**: 保持搜索引擎返回的顺序

### 6.3 阅读数据管道
```
SE 生产工具链 → content.opf (se:word-count, se:reading-ease.flesch)
  → Ebook::FromFilesystem() 解析 OPF
    → MariaDB Ebooks.WordCount / ReadingEase
      → Accessor trait GetReadingTime() / GetReadingEaseDescription()
        → 模板直接渲染
```
- **数值源于制作环节，而非网站实时计算** —— 离线计算、一次写入、多次读取
- **描述性字段延迟计算** —— Lazy loading via PHP `__get`

### 6.4 纯 CSS 3D 书本模型
- 用 `skewY(-10deg) scale(.75)` 整体倾斜
- 用 4 个 `::before`/`::after` 伪元素分别构建书脊、书页、背板、阴影
- CSS 变量 `--size` 控制书本厚度（5 档，基于字数）
- SVG 纹理 (`pages-texture.svg`, `logo-spine.svg`) 增加真实感
- `prefers-reduced-motion` 尊重用户动画偏好
- 移动端直接隐藏 (`display: none`)

### 6.5 无框架自研模板
```php
// TemplateBase 使用 __callStatic 动态加载模板文件
// Template::EbookGrid(...) → require 'templates/EbookGrid.php'
// 模板是纯 PHP 文件，接收变量，输出 HTML
```
比传统 MVC 框架轻量得多，适合内容型站点。

---

## 七、文件索引（快速查找）

### 浏览/搜索
| 文件 | 内容 |
|------|------|
| `www/ebooks/index.php` | 浏览页主入口 + 分页 |
| `www/ebooks/http-router.php` | 书本 URL 路由 |
| `templates/SearchForm.php` | 搜索/过滤表单 |
| `templates/EbookGrid.php` | Grid/List 视图组件 |
| `lib/SearchDb.php` | Manticore 连接 + 查询 |
| `lib/Ebook.php:2559-2772` | `GetAllByFilter()` 核心查询 |
| `config/manticore/ebooks.sql` | 搜索索引定义 |
| `config/apache/rewrites/ebooks.conf` | URL 重写规则 |
| `lib/Enums/EbookSortType.php` | 排序枚举 |
| `lib/Enums/ViewType.php` | 视图类型枚举 |

### 书本详情/阅读数据
| 文件 | 内容 |
|------|------|
| `www/ebooks/http-get.php` | 详情页主模板 |
| `lib/Ebook.php:522-548` | `GetReadingEaseDescription()` 难度映射 |
| `lib/Ebook.php:550-579` | `GetReadingTime()` 阅读时间计算 |
| `lib/Ebook.php:1029-1041` | OPF 解析: word-count + reading-ease |
| `lib/Ebook.php:59-92` | Ebook 属性定义 |
| `lib/Constants.php:99` | `AVERAGE_READING_WORDS_PER_MINUTE = 275` |
| `config/sql/se/Ebooks.sql` | Ebooks 表结构 |
| `lib/Traits/Accessor.php` | Lazy loading getter trait |

### 下载/3D 模型
| 文件 | 内容 |
|------|------|
| `www/ebooks/http-get.php:136-243` | 下载栏目 + 书本模型 |
| `www/ebooks/download.php` | 下载处理（频率限制 + 致谢页） |
| `templates/RealisticEbook.php` | 3D 书本 HTML 模板 |
| `www/css/core.css:3264-3374` | CSS 3D 书本效果 |
| `www/css/core.css:4660-4684` | Hover 3D 动画 |
| `www/images/logo-spine.svg` | 书脊 SVG 纹理 |
| `www/images/pages-texture.svg` | 书页纹理 SVG |
| `lib/Ebook.php:770-802` | 文件系统格式发现 |
| `lib/Ebook.php:1254-1280` | 下载 URL 生成 |
| `lib/Enums/EbookFormatType.php` | 下载格式枚举 |

---

## 八、对 CulturalSimmer 项目的启发

1. **阅读数据**: Standard Ebooks 的数据来源于制作工具链（OPF metadata），如果 CulturalSimmer 没有类似工具链，可考虑用 PDF 解析库（如 PyMuPDF）提取字数，用 textstat 等库计算 readability。

2. **搜索**: Manticore 是轻量级替代 Elasticsearch 的好选择。对于静态 Astro 站点，Pagefind 已经提供了客户端搜索，如果有更高需求可考虑 Manticore。

3. **书本模型**: 纯 CSS 方案非常优雅，无需 Three.js 依赖，适合 v1 阶段。核心是 5 个定位层 + CSS 变量控制厚度。

4. **零 JS 架构**: Standard Ebooks 是内容型站点的典范 —— 所有交互都是服务器往返，但这要求 SSR 能力。Astro 可以走中间路线：SSG + 少量客户端 JS (Pagefind)。

5. **分类/标签系统**: 用 tags 做多对多分类，URL 结构 `/subjects/{tag}` → 重写至带过滤参数的列表页。比层级分类更灵活。
