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

### Ingest PDF

触发：发布 tag 以 `ingest-` 开头的临时 Release。

流程：校验唯一 PDF、读取 XMP、检查版次、生成差异与资产、运行完整验证、创建正式 Release、提交派生文件、清理临时 Release，并触发部署。工作流使用 `ebook-ingest` 全局并发锁，不允许两个入库任务同时修改书目。

权限：只授予完成正式 Release、提交派生文件和触发部署所需的仓库权限。PDF 只保存在 Release，不进入 Git 历史。

### Deploy

触发：`main` push、每日定时刷新或手动运行。

流程：运行完整验证并生成唯一 `dist` 产物；GitHub Pages 发布该产物作为永久主站。Cloudflare job 复制同一产物，根据书目最新版 manifest 从 GitHub Releases 下载并校验每本书的最新版 PDF，只在镜像副本中把下载按钮改为同源地址，然后发布到 `/CulturalSimmer/`。两个部署任务相互独立，镜像失败不会阻止永久主站更新。PDF 入库以 `notify_updates=true` 手动触发部署；GitHub Pages 发布成功后，Deploy 请求私有通知仓库分别运行 QQ 与 ntfy live workflow。

跨仓库触发使用公开仓库 secret `NOTIFIER_DISPATCH_TOKEN`。它必须是只授权 `Fulinte1966/CulturalSimmer-notifier`、仅含 Actions 读写权限且设有有效期的 fine-grained personal access token，不得复用项目管理 token。即时触发失败只产生部署注释，不回滚网站；私有通知仓库的每日定时轮询继续作为独立兜底。

### Sync Release Changelog

触发：维护者手动输入正式 `releaseTag`。

用途：在人工修订结构化 changelog 后重新计算统计、校验仓库数据并同步正式 Release 正文、changelog 资产和 manifest。该流程不替换 PDF。

### Route issue to project

触发：新建 GitHub Issue。

用途：按 `书籍勘误` 或 `网站捉虫` 标签把 Issue 加入 GitHub Project，并为勘误提取索书号。公开 workflow 只引用 `PROJECT_TOKEN` 名称，凭据实值不得写入仓库。

## 失败边界

- 任一元数据、版次、差异、测试、字体或构建检查失败时，不发布正式书目提交。
- 正式 Release 创建后若提交失败，入库清理逻辑删除本次正式 Release 与 tag，不影响历史版本。
- 临时 ingest Release 在成功或失败后均由清理步骤处理；失败工作区只存在于 Actions 临时环境。
- 部署使用并发组串行化，不取消正在发布的版本。
- 读者通知只依赖永久主站发布成功；Cloudflare 镜像、最新版 PDF 下载或跨仓库调用失败不改变 Release 与 GitHub Pages 部署结果，每日轮询仍会补发未发送事件。
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
