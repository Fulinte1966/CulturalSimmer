# 自动化与构建总览

**适用对象：** 仓库维护者与贡献者。

本文说明公开仓库中的数据边界、GitHub Actions 工作流和统一验证入口。凭据实值、远程节点信息、备份与破坏性恢复步骤不属于公开文档。

## 数据边界

| 数据 | 人工事实来源 | 仓库中的结果 |
| --- | --- | --- |
| 书目与版次 | 正式上传 PDF 的 XMP | `src/content/books/`、`src/data/manifests/` |
| 封面、书脊、目录、阅读统计 | 正式上传 PDF | `public/covers/`、`src/data/outlines/`、`src/data/reading/` |
| 版本差异 | 相邻正式 PDF 的规范化正文 | `src/data/changelogs/` 与 Release 资产 |
| 自动本站消息 | 正式 Release | `src/data/generated-updates.json` |
| 人工公告 | `src/content/announcements/*.md` | 构建期渲染并写入公开归档 |
| 公告置顶顺序 | `src/data/site-update-pins.json` | 首页置顶区 |
| 单书更新广播策略 | 书目中的 `notifyUpdates` | 公开通知 feed 是否包含后续 `book_version` |
| 分类树 | `src/data/classifications.yml` | 索引页与书号校验 |

派生文件不得作为第二个人工数据源。需要修订书目信息时应修正 PDF 元数据并重新发布；只有更新日志的人工复核项允许按对应规范编辑结构化 changelog。

## 统一验证

```bash
npm run verify
```

执行顺序为：

1. Node 与 Python 单元测试；
2. 书目、分类和派生文件校验；
3. 强制刷新 Astro 内容集合并执行类型检查；
4. 检查本站消息归档是否与源数据一致；
5. 第一次生产构建；
6. 从源码、静态资源和第一次构建产物收集实际用字，生成 WOFF2 子集；
7. 第二次生产构建；
8. 校验实际书目条目与 `dist/books/*` 详情页完全一致，并生成 Pagefind 索引。

空书库是受支持的初始化状态。此时首页、索引、检查更新与勘误入口仍可构建，书目详情页和 Pagefind 书目索引为空；构建后断言会拒绝内容缓存遗留的“幽灵”详情页。

## GitHub Actions

### CI

触发：Pull Request 或手动运行。

权限：只读仓库内容。安装锁定的 Node、Python 依赖后运行 `npm run verify`。CI 不创建 Release、不推送提交、不部署站点。

### Ebook Candidate

触发：维护者手动运行，选择 `preview` 或 `promote`，并提供 Draft `ingest-*` Release tag。

`preview` 校验唯一 PDF、读取 XMP、检查公开书目和私有删除台账中的历史版次、生成差异与资产、运行完整验证，并部署受 Cloudflare Access 保护的完整候选站。候选锁绑定 Draft Release ID、PDF 摘要、字节数、源提交、书号、版次和跳版策略。

`promote` 需要 `ebook-production` Environment 人工批准，并重新下载 Draft、重建全部派生数据和验证候选锁。通过后才创建正式 Release、提交派生文件并等待生产部署；成功后更新旧 Release 的取代提示，再清理 Draft 和候选站。工作流使用全局并发锁，不允许两个候选同时修改书目。

权限：只授予完成正式 Release、提交派生文件和触发部署所需的仓库权限。PDF 只保存在 Release，不进入 Git 历史。

### Remove Publication

触发：维护者手动运行，选择撤回单个版次或下架整本书，并提供本地加密备份产生的 inventory 摘要和精确确认短语。

`preview` 先确认私有台账已登记，再重算本地与远程 inventory、应用删除变换、运行完整验证并部署受 Access 保护的候选站。`promote` 需要 `ebook-production` 人工批准；生产清洁版本部署成功后才删除 GitHub Release/tag 和旧 Cloudflare 部署。后半段失败时私有台账记录 `failed` 检查点，重跑同一 inventory 继续收口，不重写 Git 历史。

### Deploy

触发：`main` push、每日定时刷新或手动运行。

流程：运行完整验证并生成唯一 `dist` 产物。Cloudflare job 复制该产物，根据书目最新版 manifest 从 GitHub Releases 下载并校验每本书的最新版 PDF，只在 Cloudflare 副本中把下载按钮改为同源地址，然后发布主站 `/CulturalSimmer/`。GitHub Pages 独立发布原始产物作为备份，下载仍指向 GitHub Release。部署不再触发读者广播，QQ 与 ntfy 在每日固定窗口独立读取已公开 feed。

跨仓库凭据只用于读取私有删除台账和记录撤回/下架结果，不再用于普通发布后的即时广播。`PUBLICATION_LEDGER_TOKEN` 必须限制到 `Fulinte1966/CulturalSimmer-notifier` 所需的最小 Contents/Actions 权限并设置有效期，不得复用其他管理 token。某书设置 `notifyUpdates: false` 时，通知 feed 不包含该书后续版次事件，网站、Release 和部署仍保持正常。

### Sync Release Changelog

触发：维护者手动输入正式 `releaseTag`。

用途：在人工修订结构化 changelog 后重新计算统计、校验仓库数据并同步正式 Release 正文、changelog 资产和 manifest。该流程不替换 PDF。

### Route issue to project

触发：新建 GitHub Issue。

用途：按 `书籍勘误` 或 `网站捉虫` 标签把 Issue 加入 GitHub Project，并为勘误提取索书号。公开 workflow 只引用 `PROJECT_TOKEN` 名称，凭据实值不得写入仓库。

## 失败边界

- 任一元数据、版次、差异、测试、字体或构建检查失败时，不发布正式书目提交。
- 正式 Release 创建后若生成提交尚未推送即失败，工作流删除本次正式 Release 与 tag，并保留 Draft 供检查；提交已推送后若部署失败，保留有效 Release 和公开提交，修复部署而不是回滚数据。
- Draft ingest Release 只在正式站部署和候选清理都成功后删除；候选失败时保留 Draft 供重新预览。
- 撤回与下架只有在生产清洁版本部署成功后才删除 Release/tag；后续清理失败写入私有检查点并通过同一 inventory 幂等重试。
- 部署使用并发组串行化，不取消正在发布的版本。
- 读者通知只读取已经公开的 feed；最新版 PDF 下载或跨仓库台账调用失败不改变已创建的 GitHub Release。GitHub Pages 备份可独立发布，每日 06:00 主运行和 08:00 补跑都会依靠稳定 ID 防重。
- GitHub Actions secret 只通过对应 Environment 或 repository secret 注入，日志和公开文档不得包含实值。

## 本地入口

```bash
mise trust
mise install
mise run setup
mise run test
mise run check
```

开发服务器使用 `mise exec -- npm run dev`。PDF 上传入口、公告管理和 changelog 修订分别见本目录中的对应文档。

## 参考

- [Astro：Deploy to GitHub Pages](https://docs.astro.build/en/guides/deploy/github/)
- [GitHub Actions：Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub Actions：Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub REST API：Create a workflow dispatch event](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
- [GitHub：Managing fine-grained personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub Releases documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
