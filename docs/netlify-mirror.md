# Netlify 静态镜像与资源源

**适用对象：** 网站部署维护者。本文只记录变量名称和公开地址，不记录任何 secret 实值。

GitHub Pages 是网站的永久主站和 canonical。Netlify 部署同一份静态构建产物，提供完整备用镜像，并优先承载构建后的 WOFF2 字体和书籍封面。PDF、Tally、Z-Library、JavaScript、CSS 和其他装饰资源不经过 Netlify。

## 地址约定

- 主站：`https://fulinte1966.github.io/CulturalSimmer/`
- 镜像：`https://culturalsimmer-mirror.netlify.app/CulturalSimmer/`
- 资源源变量：`PUBLIC_ASSET_BASE_URL=https://culturalsimmer-mirror.netlify.app`

`PUBLIC_ASSET_BASE_URL` 必须是没有路径、查询参数和片段的 HTTPS origin。变量未设置时，本地开发和生产构建均使用同源资源。

## GitHub 配置

在仓库的 **Settings > Environments** 中创建 `netlify-mirror`，然后配置：

| 类型 | 名称 | 内容 |
| --- | --- | --- |
| Environment secret | `NETLIFY_AUTH_TOKEN` | Netlify personal access token |
| Environment variable | `NETLIFY_SITE_ID` | Netlify 站点 API ID |
| Environment variable | `PUBLIC_ASSET_BASE_URL` | `https://culturalsimmer-mirror.netlify.app` |

不要把 token、站点状态目录或本地环境文件提交到仓库。

## 发布顺序

`Deploy` workflow 只构建一次。构建产物先包装到 Netlify 的 `/CulturalSimmer/` 路径并发布；Netlify 成功后，GitHub Pages 才切换到同一版本。镜像失败时，主站保留上一版，不会发布引用缺失资源的新 HTML。

Netlify 的 Pretty URLs 后处理保持关闭，避免把区分大小写的书号路径改写为小写；Astro 已经生成所有目录式路由和尾斜杠。

字体声明按 Netlify、GitHub Pages 的顺序包含两个 WOFF2 地址。封面图片记录同源回退地址，镜像加载失败时只重试一次。Netlify 镜像发送 `X-Robots-Tag: noindex`，所有页面的 canonical 均指向 GitHub Pages。

构建后会为字体、封面和 `public/assets/` 图形的公开 URL 附加内容指纹。Netlify
主资源地址与 GitHub Pages 后备地址使用同一个指纹；资源内容未变时继续命中
缓存，内容变化时自动使用新 URL，无需用户清理浏览器缓存。

## 验证与回退

生产发布后检查首页、索引、详情、检查更新和勘误入口，并确认字体与封面响应包含预期的 CORS 和缓存头。网站 HTML、CSS 和 JavaScript 应继续由 GitHub Pages 提供。

需要停止资源加速时，清空 `netlify-mirror` 环境中的 `PUBLIC_ASSET_BASE_URL` 并重新构建。构建脚本会恢复全部同源 URL；Netlify 完整镜像可以继续保留。
