# 本站消息维护规范

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

### 人工消息

人工消息位于 `src/content/announcements/`，每个 Markdown 文件对应一条消息。

无正文简讯：

```md
---
title: 检查更新功能已启用。
label: 功能
publishedAt: 2026-07-09T10:00:00+08:00
---
```

带全文公告：

```md
---
title: 文火《发刊词》
label: 公告
publishedAt: 2026-07-09T09:00:00+08:00
---

这里填写 Markdown 正文。
```

正文是否存在由 Markdown 内容自动判断，不设置 `hasFullText`。正文为空时标题是普通文本；正文非空时标题可在栏目内打开全文。本站消息中只有这类人工全文标题可以点击。`publishedAt` 使用完整 ISO 8601 时间，推荐显式写出 `+08:00`；修改标题或正文不会自动改变发布时间，也不读取 Git 文件时间。

人工标签须满足以下规则：

- 去除首尾空格后不得为空；
- 不得包含 `[]`、`［］` 或 HTML；
- 不得超过六个字符；
- 不得使用自动消息保留标签 `新书`、`更新`。

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

置顶消息严格按配置顺序显示。其后只显示最新五条非置顶消息，排序规则为 `publishedAt` 降序、来源、全局 ID；置顶消息不占五条额度，也不会在普通区重复。只有置顶区与普通区同时存在时才显示星号分隔线。

人工全文在 Astro 构建期通过 `render()` 转为静态 HTML，并且只嵌入首页当前可见消息对应的正文。打开全文会保存列表滚动位置和触发按钮；`〔返回〕` 或 `Escape` 恢复列表、滚动位置和焦点。全文区域使用浏览器原生滚动，支持鼠标滚轮、触控板、触屏和键盘，滚动不会改变主页布局。

本站消息区域已排除 Pagefind，不提供独立归档页、永久链接、搜索、RSS、邮件订阅或后台管理界面。

## 验证

修改消息数据、脚本或界面后运行：

```bash
npm run check
npm run validate
npm run test:ingest
npm run test:ui
npm run build
```

Node 测试覆盖消息派生、正文判断、标签和数据校验、排序、置顶、最近五条、URL、状态资格与幂等性；Python 入库测试覆盖正式 Release 时间写入及原子追加。
