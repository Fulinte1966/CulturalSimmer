# 上线前测试书库初始化

**适用对象：** 仓库维护者。此流程会删除全部测试书目、电子书 Release 和 tag，只能用于正式上线前或明确可丢弃的测试仓库。

## 使用边界

初始化与正式撤回不是同一件事：

- 初始化允许测试结束后重新从第 1 版发布，因此不会写入正式撤回台账。
- 正式上线后，公开版次一经发行即永久占用；应使用候选预览、撤回版次或整书下架。
- 脚本不会重写 Git 历史。旧提交和既有克隆仍可能保存测试时期的派生文本，但 PDF 从未进入 Git 历史。
- GitHub Immutable Releases 必须保持关闭；启用后删除的 tag 不能复用，脚本会拒绝生成计划。
- 本地管理员凭据直接读取仓库级开关；Actions 的 `GITHUB_TOKEN` 无此权限时，
  只在标准 Releases API 为每个现存 Release 明确返回 `immutable` 状态后继续。
  空 Release 仓库等无法证明状态的场景必须配置具有 `Administration: read` 的
  `CATALOG_RESET_ADMIN_TOKEN`，不得把 403 当作关闭状态。

## 清理范围

脚本清理：

- `src/content/books/` 中的全部书目；
- manifest、目录、阅读统计、结构化及汇总更新日志；
- 书籍封面、书脊和按当前内容生成的字体子集；
- 自动本站消息和书籍勘误公告；
- GitHub 中由书目数据、`ingest-*` Draft 或规范发行资产证明为本项目电子书的 Release/tag；
- 清洁生产部署完成后的旧 Cloudflare Pages 部署。

脚本保留：

- 手工网站公告及仍有效的手工置顶顺序；
- 分类、口号、页面、样式、字体源文件和发布策略；
- Git 提交历史、Issue、Pull Request、Actions 和仓库设置；
- 正式撤回私有台账。

Release 归属按书目中声明的 tag、`ingest-*` Draft 或同时具备规范 manifest/正文快照资产判断。普通代码 Release/tag 不会仅因存在于仓库而被删除。

## 本地准备

本机需要 `gh`、`age`、`zstd`、`tar` 和项目依赖；`gh` 必须已登录目标仓库。

1. 生成无副作用的清单：

   ```bash
   npm run catalog:reset -- plan \
     --reason "private pre-launch reset reason" \
     --output Outputs/catalog-resets/reset-plan.json
   ```

2. 仔细查看 `bookIds`、`remote.releases`、`remote.tags` 和 `originalUpdateIds`。清单中出现非书籍 Release/tag 时不得继续。

3. 生成加密备份：

   ```bash
   export AGE_RECIPIENT="$(age-keygen -y "$HOME/.config/age/keys.txt")"
   npm run catalog:reset -- backup \
     --plan Outputs/catalog-resets/reset-plan.json \
     --age-recipient "$AGE_RECIPIENT"
   ```

   `Outputs/catalog-resets/` 会生成加密归档和 receipt。归档包含完整 Git bundle、所有待清理仓库文件、计划和全部目标 Release 资产；receipt 提供工作流所需的 `backupSha256`。

4. 从计划和 receipt 生成不易抄错的 workflow 输入：

   ```bash
   npm run catalog:reset -- workflow-inputs \
     --plan Outputs/catalog-resets/reset-plan.json \
     --receipt Outputs/catalog-resets/<backup>.receipt.json \
     --mode preview \
     --output Outputs/catalog-resets/preview-inputs.json
   ```

   可在网页中照此填写，或直接通过 GitHub CLI 启动：

   ```bash
   gh workflow run reset-test-catalog.yml --json \
     < Outputs/catalog-resets/preview-inputs.json
   ```

   正式执行前把 `--mode` 改为 `promote` 重新生成输入；不要手工修改 JSON。

## 候选预览与批准

手动运行 `Reset Pre-launch Test Catalog`：

1. 先选择 `preview`。
2. 填写计划中的 `reasonSha256`、`inventorySha256`，receipt 中的 `backupSha256`，以及确认短语：

   ```text
   RESET PRELAUNCH TEST CATALOG
   ```

3. 确认匿名请求 `catalog-reset-preview.fulinte.pages.dev` 会被 Cloudflare Access 拒绝；workflow 会自动检查 `302` 登录跳转和 `WWW-Authenticate` 响应头，直接返回 `200` 时停止。
4. 登录 Cloudflare Access 后检查 `catalog-reset-preview`：首页手工置顶公告仍在，书架、索引、搜索和书籍详情为空，检查更新及勘误的未知资源路径正常。
5. 使用完全相同的输入选择 `promote`，并在 `ebook-production` Environment 中人工批准。

工作流会重新计算清单、构建并验证空站、提交空书库，并显式 dispatch 一次 `notify_updates=false` 的生产部署；Cloudflare 主站和 GitHub Pages 备份站成功后，才删除 GitHub Release/tag。之所以显式 dispatch，是因为使用 GitHub Actions `GITHUB_TOKEN` 推送的提交不会再次触发依赖 `push` 的工作流。最后用清洁内容覆盖三个持久预览分支并清理旧 Cloudflare 部署，全程不广播读者更新。

## 通知器与恢复测试

网站初始化不会自动修改固定节点上的 QQ/ntfy 状态。结果文件中的 `notifierUpdateIds` 是测试期间已经产生的事件 ID：

- 仅测试网站和发布链路时，无需处理通知器状态。
- 需要重新测试同一书号和版次的通知时，必须先备份固定节点状态，再由通知器维护流程归档并清除这些测试 ID。
- 存在未决发送批次时不得清除状态；应先按通知器 runbook 解决 pending。

这样可以避免网站工作流凭跨仓库权限静默改写服务器状态。正式上线前应完成一次通知状态复核，并保留 OCI 状态备份。

## 失败与恢复

- 清单或远端资源发生任何变化，预览和正式执行都会拒绝继续，必须重新备份。
- 空站生产部署失败时，不删除任何 Release/tag。
- 生产部署成功后远端清理失败时，不回滚空站。使用本地保存的同一 `reset-plan.json` 重新运行 `finalize-remote`；若仅剩 Cloudflare 历史部署未清理，手动运行 `Clean Stale Cloudflare Deployments` 并输入 `DELETE STALE CLOUDFLARE DEPLOYMENTS`，从该检查点继续。
- Actions artifact 只是短期诊断资料，不是备份。权威备份是本地加密归档及其独立保存的 age 身份。

## 正式上线

空站验收后，按电子书候选工作流从第 1 版依次重新发布。确认正式版本、两个公开站点、二维码、更新检查、勘误和通知均正常后，再启用 GitHub Immutable Releases。启用后不得再次运行本初始化流程。

参考：[GitHub Immutable Releases](https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/preventing-changes-to-your-releases)、[GitHub Release 删除](https://cli.github.com/manual/gh_release_delete)、[Git refs 删除 API](https://docs.github.com/en/rest/git/refs)、[Cloudflare Pages 部署 API](https://developers.cloudflare.com/pages/configuration/api/)。
