# Cloudflare Pages 主站与 GitHub Pages 备份

**适用对象：** 网站部署维护者。本文只记录变量名称和公开地址，不记录任何 secret 实值。

Cloudflare Pages 是面向读者的主站和 canonical，负责页面、字体、封面及每本书最新版 PDF 的交付。GitHub 保存源码、Actions、结构化书目数据和全部正式 Release，并通过 GitHub Pages 发布同一网站的独立备份。两个站点分别使用同源资源，不在浏览器端互相加载字体或封面。GitHub Releases 始终是全部正式 PDF 和历史版本的唯一事实来源；Tally 与 Z-Library 不经过 Cloudflare Pages。

## 地址约定

- 主站：`https://fulinte.pages.dev/CulturalSimmer/`
- GitHub Pages 备份：`https://fulinte1966.github.io/CulturalSimmer/`
- Pages 项目：`fulinte`
- 旧 Cloudflare 地址：`https://culturalsimmer-mirror.pages.dev/CulturalSimmer/`，仅保留永久重定向

## GitHub 配置

在仓库的 **Settings > Environments** 中创建 `cloudflare-pages`，然后配置：

| 类型 | 名称 | 内容 |
| --- | --- | --- |
| Environment secret | `CLOUDFLARE_API_TOKEN` | 当前账户的 Account API Token，仅授予 Pages Write |
| Environment variable | `CLOUDFLARE_ACCOUNT_ID` | Pages 项目所属 Cloudflare Account ID |

Account API Token 作为独立服务身份，不依赖某个用户令牌。不要使用
Global API Key 或宽权限 Workers 模板；定期轮换长期有效的部署令牌。不要把
token、Account ID、本地 Wrangler 状态目录或环境文件提交到仓库。

候选发布、删除预览与测试书库初始化继续通过 `cloudflare-pages` Environment 使用同一最小权限部署身份，避免复制 Cloudflare secret。另建不持有部署凭据的 `ebook-production` Environment 并设置 required reviewers；正式发布或公开删除 job 必须先通过该批准关卡。三个预览分支域名 `ebook-preview.fulinte.pages.dev`、`removal-preview.fulinte.pages.dev` 与 `catalog-reset-preview.fulinte.pages.dev` 必须由 Cloudflare Access 应用以默认拒绝策略保护。GitHub Environment 只负责凭据或批准，不能代替 Cloudflare Access。

预览 workflow 在部署后必须以无 Cookie 请求验证 Access：响应应为 `302`，同时包含 Cloudflare Access 登录地址和 `WWW-Authenticate: Cloudflare-Access`。若匿名请求直接得到 `200`，工作流必须失败，不得把候选部署成功误认为访问控制已经生效。

公开仓库还需要 `PUBLICATION_LEDGER_TOKEN` repository secret，用于只读私有删除台账和 dispatch 私有记录工作流。迁移期间 workflow 可回退使用原 `NOTIFIER_DISPATCH_TOKEN`；确认新 token 具备最小 Contents read 与 Actions write 权限后，应删除旧 secret。

## 发布顺序

`Deploy` workflow 只构建一次。`scripts/prepare-cloudflare-pages.mjs` 将 `dist/` 复制到 `cloudflare-dist/CulturalSimmer/`，下载并验证最新版 PDF，再用锁定版本的 Wrangler 发布 Cloudflare 主站。GitHub Pages 直接发布原始 `dist/` 作为备份，不附带 PDF 副本。两个部署任务相互独立，任一站点失败不会覆盖另一个站点的上一版。

撤回、下架或测试书库初始化会在清洁部署成功后删除旧 Pages 部署。清理脚本使用 Pages API 返回的默认分页大小和 `total_pages`，避免传入服务端不接受的页大小。若事务只在此步骤失败，可运行 `Clean Stale Cloudflare Deployments`，输入精确确认短语后单独重试；工作流只保留 `main`、`ebook-preview`、`removal-preview` 与 `catalog-reset-preview` 各自最新部署。

除每日天气刷新外，生产部署开始和最终状态会通过私有 notifier 仓库的 `notify-ops.yml` 实时写入 ntfy ops。只有两处公开站点都成功才发送完成状态；任一失败会保留为活动告警，下一次成功部署负责恢复。该观测链路使用独立状态与最小权限 dispatch token，失败不得阻断网站发布。

打包环境必须提供 `curl`。下载命令只访问公开的 HTTPS Release URL，并设置失败重试、连接超时、总超时和最大文件大小；不使用 GitHub API token。

Pages 项目是一次性基础设施。工作流通过 Cloudflare Pages API 幂等检查 `fulinte` 项目；只在项目不存在时执行 `wrangler pages project create fulinte --production-branch=main`。日常发布不会修改项目配置。

主站根路径通过 `_redirects` 永久跳转到 `/CulturalSimmer/`。Cloudflare 主站允许索引，所有 HTML 都包含指向 `fulinte.pages.dev` 的自引用 canonical；GitHub Pages 的同一 HTML 也指向该 canonical。旧 Cloudflare 项目只部署 `_redirects` 和 `X-Robots-Tag: noindex`，把原地址及其子路径永久转到新主站。Astro 已生成目录式路由和尾斜杠，不再做额外的 Pretty URL 改写。

构建后会为字体、封面和 `public/assets/` 图形的公开 URL 附加内容指纹。`_astro/` 中带文件哈希的产物使用长期 immutable 缓存；稳定文件名的字体和封面使用一天浏览器缓存，并依靠内容指纹在更新时换用新 URL。

## 最新 PDF 交付

包装脚本读取 `src/content/books/*.md` 的 YAML front matter，按数值最高的 `edition` 选择对应 manifest。每个最新版 PDF 从 manifest 的 GitHub Release URL 下载到临时部署产物的 `downloads/`，随后核对：

- `bookId`、版次、release tag 和文件名；
- manifest 记录的字节数；
- `sourceSha256` 与 `githubAssetDigest`；
- 下载文件的实际 SHA-256；
- Cloudflare Pages 的 25 MiB 单文件限制。

只有全部 PDF 验证成功后，包装脚本才使用 HTML 解析器把详情页中带有专用标记的下载链接改写为 Cloudflare 同源地址。GitHub Pages 的原始 `dist/` 不被修改，下载按钮仍指向 GitHub Release。任一下载、身份或摘要校验失败时，脚本删除整个不完整主站产物并使 Cloudflare job 失败；Wrangler 不会上传半成品。

PDF 文件名包含 release tag，因此 Cloudflare 使用一年 immutable 缓存和下载响应头。新版本上线后使用新 URL，旧版本不继续复制到当前 Pages 产物；历史版始终由 GitHub Releases 提供。

包装脚本在上传前执行 Cloudflare Pages 免费层约束检查：免费计划每月最多 500 次构建、单站最多 20,000 个文件、单文件不超过 25 MiB。纯静态资源请求免费且不限量。若将来任一 PDF 达到 25 MiB，或最新版 PDF 总量不再适合随站点部署，应先继续使用 GitHub Release 下载，再评估通过自有域名提供 R2；受限的 `r2.dev` 地址不用于生产。

## 验证与回退

生产发布后检查首页、索引、详情、检查更新和勘误入口；确认主站根路径重定向、canonical、字体 MIME、缓存头和同源资源 URL。逐本检查 Cloudflare 主站的下载链接、PDF 大小和 SHA-256，并确认 GitHub Pages 备份仍指向 GitHub Release。检查旧 Cloudflare 地址保持 `301`、路径和查询参数不丢失。Cloudflare Pages 的普通全球网络不属于 Cloudflare China Network，是否改善中国大陆访问必须通过实际网络持续测试，不应据此宣称具备大陆 CDN 节点。

Cloudflare 发布失败时，主站保留上一版，GitHub Pages 仍可独立发布；读者通知只在每日广播窗口读取已经公开的 feed。需要临时停用 Cloudflare 时，禁用 `deploy-cloudflare` job 或删除 `cloudflare-pages` Environment，GitHub Pages 不依赖 Cloudflare 凭据。

## 官方参考

- [Cloudflare Pages 定价](https://developers.cloudflare.com/pages/functions/pricing/)
- [Cloudflare Pages 平台限制](https://developers.cloudflare.com/pages/platform/limits/)
- [Cloudflare R2 定价](https://developers.cloudflare.com/r2/pricing/)
- [Cloudflare R2 公共桶](https://developers.cloudflare.com/r2/buckets/public-buckets/)
