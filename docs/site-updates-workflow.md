# 本站消息维护规范

**适用对象：** 公告编辑者、通知系统维护者与网站维护者。

主页“本站消息”统一显示电子书入库生成的自动消息和人工维护的公告。数据在 Astro 构建期完成校验、关联、排序和 Markdown 渲染；浏览器只负责列表与全文之间的状态切换，不请求 GitHub API，也不在客户端解析 Markdown。

## 数据来源

### 自动消息

自动消息保存在 `src/data/generated-updates.json`。入库脚本在正式 GitHub Release 创建成功后读取其 `published_at`，再以原子写入方式追加记录。

```json
[
  {
    "id": "F0-1-1-listed",
    "type": "book-added",
    "publishedAt": "2026-07-08T18:01:03Z",
    "bookId": "F0-1-1"
  },
  {
    "id": "F0-1-1-v2",
    "type": "book-updated",
    "publishedAt": "2026-07-11T10:00:00Z",
    "bookId": "F0-1-1",
    "edition": 2
  }
]
```

`book-added` 的 ID 固定为 `{bookId}-listed`，`book-updated` 固定为 `{bookId}-v{edition}`。文件不保存书名、标签或文案；构建时从当前书目派生这些内容。自动生成的 `［新书］` 与 `［更新］` 都是纯文本，不创建链接。

同一 ID 与相同内容再次写入时不产生重复记录；同一 ID 对应不同内容时入库失败并报告冲突。自动流程不会读取或改写置顶配置。

需要让某本已上架书籍停止向 QQ 与 ntfy 广播后续版次时，在该书
`src/content/books/{bookId}.md` 的 frontmatter 中设置：

```yaml
notifyUpdates: false
```

该字段默认值为 `true`，入库新版本时会保留，不会被 PDF XMP 覆盖。它只从公开
通知 feed 中排除该书的 `book_version` 事件：首次上架消息、首页简讯、仓库更新归档、
Release、部署、检查更新、勘误、人工公告和重要勘误均保持正常。重新启用时删除该字段
或改为 `true`；通知器只会处理当时仍在最近 100 条 feed 中且尚未发送的事件。

### 人工消息

人工消息位于 `src/content/announcements/`，每个 Markdown 文件对应一条消息。

无正文简讯：

```md
---
title: 检查更新功能已启用。
label: 功能
publishedAt: 2026-07-09T10:00:00+08:00
kind: site-announcement
summary: []
---
```

带全文公告：

```md
---
title: 文火《发刊词》
label: 公告
publishedAt: 2026-07-09T09:00:00+08:00
kind: site-announcement
summary:
  - 公布本站维护方式
---

这里填写 Markdown 正文。
```

正文是否存在由 Markdown 内容自动判断，不设置 `hasFullText`。正文为空时标题是普通文本；正文非空时标题可在栏目内打开全文。本站消息中只有这类人工全文标题可以点击。`publishedAt` 使用完整 ISO 8601 时间，推荐显式写出 `+08:00`；修改标题或正文不会自动改变发布时间，也不读取 Git 文件时间。

人工标签须满足以下规则：

- 去除首尾空格后不得为空；
- 不得包含 `[]`、`［］` 或 HTML；
- 不得超过六个字符；
- 不得使用自动消息保留标签 `新书`、`更新`。

`kind` 默认为 `site-announcement`。需要发布重要勘误时设为 `important-erratum`，并同时填写有效的 `bookId`、`edition` 和简短 `summary`；构建会核对该书及版次是否存在。普通公告也可填写最多八条 `summary`，这些摘要进入公开更新源，Markdown 正文仍只用于站内全文。

## 公开更新源

每次生产构建生成：

- `/updates/feed.json`：最近 100 条权威事件；
- `/updates/latest.json`：最新时间点的事件组；
- `/updates/feed.schema.json`：Draft 2020-12 JSON Schema；
- `docs/site-updates-archive.md`：包含全部事件的仓库 Markdown 归档。

网站不提供完整更新正文页。`/updates/` 只为已经发布的旧链接保留静态跳转，并指向 GitHub 默认分支中的 Markdown 归档。公开 feed 为兼容现有消费者继续保留字段名 `updatesPageUrl`，其值同样指向该归档，不代表站内页面。

归档不设置文件标题或说明文字，只按时间倒序写入记录。每条记录采用统一格式，日期按北京时间输出且不补零：

```markdown
### `YYYY-M-D` `标签` ReleaseTag 或公告标题

正文

<!-- update-id: 稳定事件 ID -->
```

自动消息的标签固定为 `新书` 或 `更新`，标题使用对应的 Release tag；正文分别为“《书名》已上架。”或“《书名》已更新第 n 版。”。人工公告使用源文件中的 `label`、`title` 和 Markdown 正文；正文为空时使用 `summary` 作为回退内容。

自动消息映射为 `new_book` 和 `book_version`，人工消息映射为 `site_announcement` 或 `important_erratum`。设置 `notifyUpdates: false` 的书籍仍保留站内自动消息和归档，但其后续 `book_version` 不进入公开通知 feed。稳定 ID 格式为：

```text
new-book-F0-1-1-v1
book-version-F0-1-1-v2
announcement-2026-07-13-maintenance
erratum-2026-07-13-f0-1-1-v2-01
```

构建会按 Schema 校验日期、HTTPS URL、类型、摘要、最多 100 条记录和字段白名单，并额外拒绝重复 ID、本地路径及通知器配置名。`generatedAt` 表示本次构建时间，不参与事件去重；外部消费者必须使用 `updates[].id`。

正式 PDF 入库完成双站部署后，会以 `workflow_dispatch` 请求私有通知仓库立即检查该 feed；QQ 与 ntfy 使用独立状态文件和稳定事件 ID 去重。跨仓库触发不可用时不影响 Release 或网站，通知仓库的每日定时检查会补发仍未记录的事件。人工公告不会自动发送；需要即时广播时应先部署网站，再按通知仓库手册手动运行两个 live workflow。

## 创建人工消息

交互式创建：

```bash
npm run announcement:new
```

脚本依次询问标题、标签、英文 kebab-case slug、正文和是否置顶，并按 `Asia/Shanghai` 生成发布时间。选择带全文时正文不得为空，创建后仍可直接编辑 Markdown。

非交互示例：

```bash
npm run announcement:new -- \
  --title "维护完成" \
  --label "维护" \
  --slug "maintenance-complete" \
  --no-with-body \
  --no-pin
```

指定全文时使用 `--with-body --body "正文"`；需要回填历史时间时使用 `--published-at "2026-07-09T09:00:00+08:00"`。脚本不会覆盖同名文件，Markdown 和置顶配置均以临时文件替换方式写入。

## 置顶管理

置顶顺序保存在 `src/data/site-update-pins.json`：

```json
[
  "manual:2026-07-09-inaugural-message",
  "automatic:F0-1-1-v2"
]
```

数组顺序就是页面顺序。全局 ID 使用 `manual:{Markdown 文件名}` 或 `automatic:{自动消息 ID}`。配置可直接编辑，也可使用命令：

```bash
npm run updates:pin
npm run updates:pin -- manual:2026-07-09-inaugural-message --position 1
npm run updates:unpin -- manual:2026-07-09-inaugural-message
npm run updates:pins
```

不带 ID 的置顶和取消置顶命令进入交互选择。取消置顶只移除配置项，不删除消息，也不改变发布时间。无效 ID、重复 ID、空 ID、未知前缀或不存在的消息都会导致构建失败。

## 页面排序与交互

置顶消息严格按配置顺序显示。其后只显示最新五条非置顶消息，排序规则为 `publishedAt` 降序、来源、全局 ID；置顶消息不占五条额度，也不会在普通区重复。只有置顶区与普通区同时存在时才显示星号分隔线。三个全角星号使用三列等分网格，各自在分段符 frame 的三分之一处居中，因此会随栏宽自动调整，不使用固定像素内边距。

分段符的尺寸与跨视口验收规则见[前端排版合同](frontend-layout.md)。

人工全文在 Astro 构建期通过 `render()` 转为静态 HTML，并且只嵌入首页当前可见消息对应的正文。打开全文会保存列表滚动位置和触发按钮；`〔返回〕` 或 `Escape` 恢复列表、滚动位置和焦点。全文区域使用浏览器原生滚动，支持鼠标滚轮、触控板、触屏和键盘，滚动不会改变主页布局。

本站消息区域已排除 Pagefind，不提供独立正文归档页、搜索、RSS、邮件订阅或后台管理界面。完整事件记录由 `scripts/build_site_updates_archive.py` 从结构化数据确定性生成；Markdown 只是自动生成的可读镜像，不能反向作为事实来源，也不能替代独立备份。人工公告的可编辑正文仍以 `src/content/announcements/*.md` 为准。

归档文件不记录构建时间，避免每日天气部署产生无意义修改。新增电子书事件和使用管理命令创建公告时会立即重建归档；直接编辑公告后运行：

```bash
npm run updates:archive
```

CI 使用 `npm run updates:archive:check` 拒绝过期归档。

## 验证

修改消息数据、脚本或界面后运行：

```bash
npm run verify
```

Node 测试覆盖消息派生、正文判断、标签和数据校验、排序、置顶、最近五条、URL、状态资格与幂等性；Python 入库测试覆盖正式 Release 时间写入及原子追加。
