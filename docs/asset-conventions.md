# 静态资源规范

**适用对象：** 前端与构建维护者。

## 目录职责

- `src/assets/`：由 Astro/Vite 导入、需要指纹或打包的资源。
- `public/assets/brand/`：稳定品牌标志。
- `public/assets/badges/`：徽章、标签和印章。
- `public/assets/decor/`：边框、分隔和装饰元素。
- `public/assets/textures/`：供 CSS 平铺的纹理。
- `public/assets/announcements/`：人工公告正文引用的公开资源。
- `public/covers/`：PDF 入库自动生成的封面和书脊，不手工编辑。
- `public/fonts/subset/`：构建生成的 WOFF2 字体子集。
- `tools/font-sources/`：子集化所需的完整源字体和许可证，不进入站点产物。

## 命名

- 项目自制资源使用小写 kebab-case。
- 通用 UI 资源采用“职责在前”的名称，如 `badge-download.svg`、`border-vertical-repeat.svg`。
- 品牌资源使用项目名前缀，如 `culturalsimmer-wordmark.svg`。
- 不保留 `Group13`、`Frame 2`、哈希、画板编号等导出名称。
- 用户提供的源文件进入项目时，应先规范命名并放入职责明确的目录。

## 路径

Astro 组件和页面通过 `joinBasePath(import.meta.env.BASE_URL, "...")` 生成公开 URL。字体、封面、脚本和样式均使用当前站点的同源路径；GitHub Pages 与 Cloudflare Pages 各自提供完整资源，不在运行时跨站混用。

CSS 背景和 mask 必须验证 `/CulturalSimmer/` 基路径。公告 Markdown 中的站内公开资源同样使用 `/CulturalSimmer/...`，GitHub 仓库文档中的相对链接则优先使用相对路径。

`cloudflare-dist/CulturalSimmer/downloads/` 是部署时生成的临时目录，只包含从 GitHub Releases 下载并通过 manifest 摘要校验的最新版 PDF。该目录和 PDF 不属于网站源码，不得复制到 `public/` 或提交到 Git。详情页源 HTML 仍以 GitHub Release 为下载地址，Cloudflare 主站打包阶段只改写带专用标记的链接。

生产构建会为 `public/assets/`、`public/covers/` 和 `public/fonts/` 的实际引用附加
基于文件内容的 SHA-256 短指纹。源码仍只写稳定路径；不得把构建生成的
`?v=...` 参数复制回 Astro、CSS、Markdown 或数据文件。

## 不应提交

- 完整 Figma Make 工程、网页整页导出和未裁剪设计源；
- 临时截图、调试渲染、重复资源和历史版本；
- PDF 测试文件、系统缓存、`.DS_Store`；
- 可由构建恢复的 `dist/`、`.astro/` 和 `cloudflare-dist/`。

新增或移动资源后运行 `npm run verify`，并进行浏览器检查。该命令已包含字体双遍构建；只有排查字体生成器时才需要单独运行 `npm run fonts:refresh`。
