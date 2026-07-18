# Cloudflare Pages 静态镜像

**适用对象：** 网站部署维护者。本文只记录变量名称和公开地址，不记录任何 secret 实值。

GitHub Pages 是网站的永久主站和 canonical。Cloudflare Pages 通过 Direct Upload 部署同一份静态构建产物，提供完整备用镜像。镜像不代理 GitHub Pages，也不作为主站的字体或封面资源源；两个站点分别使用同源资源。为改善常用下载路径，镜像额外保存每本书的最新版 PDF；GitHub Releases 仍是全部正式 PDF 和历史版本的唯一事实来源。Tally 与 Z-Library 不经过 Cloudflare Pages。

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

`Deploy` workflow 只构建一次。GitHub Pages 直接发布 `dist/`；`scripts/prepare-cloudflare-pages.mjs` 将同一产物复制到 `cloudflare-dist/CulturalSimmer/`，下载并验证最新版 PDF，再用锁定版本的 Wrangler 上传。两个部署任务相互独立，Cloudflare Pages 失败不会阻止 GitHub Pages 更新。

打包环境必须提供 `curl`。下载命令只访问公开的 HTTPS Release URL，并设置失败重试、连接超时、总超时和最大文件大小；不使用 GitHub API token。

Pages 项目是一次性基础设施。新账户首次接入时使用
`wrangler pages project create culturalsimmer-mirror --production-branch=main`
建立 Direct Upload 项目；日常工作流只部署到已经存在的项目，避免把项目管理
权限和初始化分支混入每次生产发布。

镜像根路径通过 `_redirects` 永久跳转到 `/CulturalSimmer/`。`_headers` 为整个镜像发送 `X-Robots-Tag: noindex`，所有 HTML 的 canonical 仍指向 GitHub Pages。Astro 已生成目录式路由和尾斜杠，不再做额外的 Pretty URL 改写。

构建后会为字体、封面和 `public/assets/` 图形的公开 URL 附加内容指纹。`_astro/` 中带文件哈希的产物使用长期 immutable 缓存；稳定文件名的字体和封面使用一天浏览器缓存，并依靠内容指纹在更新时换用新 URL。

## PDF 镜像

包装脚本读取 `src/content/books/*.md` 的 YAML front matter，按数值最高的 `edition` 选择对应 manifest。每个最新版 PDF 从 manifest 的 GitHub Release URL 下载到临时部署产物的 `downloads/`，随后核对：

- `bookId`、版次、release tag 和文件名；
- manifest 记录的字节数；
- `sourceSha256` 与 `githubAssetDigest`；
- 下载文件的实际 SHA-256；
- Cloudflare Pages 的 25 MiB 单文件限制。

只有全部 PDF 验证成功后，包装脚本才使用 HTML 解析器把详情页中带有专用镜像标记的下载链接改写为同源地址。GitHub Pages 的原始 `dist/` 不被修改，仍直接下载 GitHub Release。任一下载、身份或摘要校验失败时，脚本删除整个不完整镜像产物并使 Cloudflare job 失败；Wrangler 不会上传半成品。

PDF 文件名包含 release tag，因此镜像端使用一年 immutable 缓存和下载响应头。新版本上线后使用新 URL，旧版本不继续复制到当前镜像产物；历史版始终由 GitHub Releases 提供。

包装脚本在上传前执行 Cloudflare Pages 免费层约束检查：免费计划每月最多 500 次构建、单站最多 20,000 个文件、单文件不超过 25 MiB。纯静态资源请求免费且不限量。若将来任一 PDF 达到 25 MiB，或最新版 PDF 总量不再适合随站点部署，应先继续使用 GitHub Release 下载，再评估通过自有域名提供 R2；受限的 `r2.dev` 地址不用于生产。

## 验证与回退

生产发布后检查首页、索引、详情、检查更新和勘误入口；确认根路径重定向、`X-Robots-Tag`、canonical、字体 MIME、缓存头和同源资源 URL。逐本检查镜像详情页下载链接、PDF 大小和 SHA-256，并确认 GitHub Pages 仍指向 GitHub Release。Cloudflare Pages 的普通全球网络不属于 Cloudflare China Network，是否改善中国大陆访问必须通过实际网络持续测试，不应据此宣称具备大陆 CDN 节点。

需要停用镜像时，禁用 `deploy-cloudflare` job 或删除 `cloudflare-pages` Environment。GitHub Pages 不依赖镜像凭据，可以继续正常发布。

## 官方参考

- [Cloudflare Pages 定价](https://developers.cloudflare.com/pages/functions/pricing/)
- [Cloudflare Pages 平台限制](https://developers.cloudflare.com/pages/platform/limits/)
- [Cloudflare R2 定价](https://developers.cloudflare.com/r2/pricing/)
- [Cloudflare R2 公共桶](https://developers.cloudflare.com/r2/buckets/public-buckets/)
