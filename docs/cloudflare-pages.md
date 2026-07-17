# Cloudflare Pages 静态镜像

**适用对象：** 网站部署维护者。本文只记录变量名称和公开地址，不记录任何 secret 实值。

GitHub Pages 是网站的永久主站和 canonical。Cloudflare Pages 通过 Direct Upload 部署同一份静态构建产物，提供完整备用镜像。镜像不代理 GitHub Pages，也不作为主站的字体或封面资源源；两个站点分别使用同源资源。PDF、Tally 和 Z-Library 不经过 Cloudflare Pages。

## 地址约定

- 主站：`https://fulinte1966.github.io/CulturalSimmer/`
- 镜像：`https://culturalsimmer-mirror.pages.dev/CulturalSimmer/`
- Pages 项目：`culturalsimmer-mirror`

## GitHub 配置

在仓库的 **Settings > Environments** 中创建 `cloudflare-pages`，然后配置：

| 类型 | 名称 | 内容 |
| --- | --- | --- |
| Environment secret | `CLOUDFLARE_API_TOKEN` | 当前账户的 Account API Token，仅授予 Pages Write |
| Environment variable | `CLOUDFLARE_ACCOUNT_ID` | Pages 项目所属 Cloudflare Account ID |

Account API Token 作为独立服务身份，不依赖某个用户令牌。不要使用
Global API Key 或宽权限 Workers 模板；定期轮换长期有效的部署令牌。不要把
token、Account ID、本地 Wrangler 状态目录或环境文件提交到仓库。

## 发布顺序

`Deploy` workflow 只构建一次。GitHub Pages 直接发布 `dist/`；`scripts/prepare-cloudflare-pages.mjs` 将同一产物包装到 `cloudflare-dist/CulturalSimmer/`，再用锁定版本的 Wrangler 上传。两个部署任务相互独立，Cloudflare Pages 失败不会阻止 GitHub Pages 更新。

Pages 项目是一次性基础设施。新账户首次接入时使用
`wrangler pages project create culturalsimmer-mirror --production-branch=main`
建立 Direct Upload 项目；日常工作流只部署到已经存在的项目，避免把项目管理
权限和初始化分支混入每次生产发布。

镜像根路径通过 `_redirects` 永久跳转到 `/CulturalSimmer/`。`_headers` 为整个镜像发送 `X-Robots-Tag: noindex`，所有 HTML 的 canonical 仍指向 GitHub Pages。Astro 已生成目录式路由和尾斜杠，不再做额外的 Pretty URL 改写。

构建后会为字体、封面和 `public/assets/` 图形的公开 URL 附加内容指纹。`_astro/` 中带文件哈希的产物使用长期 immutable 缓存；稳定文件名的字体和封面使用一天浏览器缓存，并依靠内容指纹在更新时换用新 URL。

包装脚本在上传前执行 Cloudflare Pages 免费层约束检查：站点最多 20,000 个文件，单文件不超过 25 MiB。正式 PDF 不进入 Pages 产物，因此仍以 GitHub Releases 为唯一正式下载源。

## 验证与回退

生产发布后检查首页、索引、详情、检查更新和勘误入口；确认根路径重定向、`X-Robots-Tag`、canonical、字体 MIME、缓存头和同源资源 URL。Cloudflare Pages 的普通全球网络不属于 Cloudflare China Network，是否改善中国大陆访问必须通过实际网络持续测试，不应据此宣称具备大陆 CDN 节点。

需要停用镜像时，禁用 `deploy-cloudflare` job 或删除 `cloudflare-pages` Environment。GitHub Pages 不依赖镜像凭据，可以继续正常发布。
