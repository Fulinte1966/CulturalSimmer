# 发布、取代、撤回与下架

**适用对象：** 仓库维护者。撤回与下架是破坏性操作，必须先完成本地加密备份。

## 生命周期

- **候选预发布**：PDF 只进入 Draft `ingest-*` Release。候选站通过 Cloudflare Access 保护，不写入 `main`，也不创建正式 Release。
- **正式发布**：`ebook-production` Environment 批准后重新验证不可变候选锁，创建正式 Release、提交生成数据并部署。部署成功后才清理 Draft 和候选站。
- **已被取代**：新版成为默认版本，旧版 Release 保留并显示指向最新版的统一提示。历史二维码和版本比较继续有效。
- **撤回版次**：从当前网站、GitHub Release/tag 和 Cloudflare 活跃部署删除指定版次；版次号永久占用。
- **下架书目**：删除整本书的全部当前公开资源；再次上架时从私有台账记录的历史最高版次继续递增。

正常新版不会删除旧版。保留旧 Release 是版本比较、旧二维码、回滚和可审计发行记录的基础。

## 候选发布

1. 本地预检并创建 Draft：

   ```bash
   npm run ebook:upload /absolute/path/book.pdf -- --dry-run
   npm run ebook:upload /absolute/path/book.pdf
   ```

2. 手动运行 `Ebook Candidate`，选择 `preview` 并填写 Draft tag。
3. 在受 Cloudflare Access 保护的 `ebook-preview` 候选站检查全部页面和 PDF。
4. 记录工作流输出的 PDF SHA-256。
5. 再次运行 `Ebook Candidate`，选择 `promote`，填写同一 Draft tag 和 SHA-256。
6. `ebook-production` Environment 的指定审核者批准后才会公开发布。

候选锁同时绑定 PDF SHA-256、字节数、Draft Release ID、书号、版次、跳版策略和源提交。任一内容变化都会使旧批准失效。正式发布提交会显式触发生产部署；两个公开站点都成功后即时 dispatch QQ 与 ntfy，通知仓库的定时检查继续作为失败兜底。两个通道使用独立状态和稳定事件 ID，不因重复触发而重复发送。

## 撤回或下架

以下流程中的 `reason` 仅进入私有运维仓库。公开 inventory 只保存原因的 SHA-256。

1. 生成远程和本地资源清单：

   ```bash
   npm run publication:remove -- plan \
     --operation withdraw-edition \
     --book-id A9-1 \
     --edition 2 \
     --reason "private operational reason" \
     --output Outputs/removals/A9-1-v2.json
   ```

   整书下架改用 `--operation delist-book` 并省略 `--edition`。

2. 使用 age 接收者生成本地加密备份：

   ```bash
   export AGE_RECIPIENT="$(age-keygen -y "$HOME/.config/age/keys.txt")"
   npm run publication:remove -- backup \
     --plan Outputs/removals/A9-1-v2.json \
     --age-recipient "$AGE_RECIPIENT"
   ```

   备份位于被 Git 忽略的 `Outputs/removals/`，包含清单、相关仓库数据和全部目标 Release 资产。没有成功备份不得继续。
   本机必须提供 `age`、`zstd`、`tar`、`gh`，且 `gh` 已登录目标仓库。`AGE_RECIPIENT` 是公开接收者，可以进入本地命令；`~/.config/age/keys.txt` 是解密身份，必须保持 `0600` 权限并与仓库工作区分开备份，不得提交或写入工作流日志。

3. 把私有原因登记到私有台账：

   ```bash
   npm run publication:remove -- register-private \
     --plan Outputs/removals/A9-1-v2.json \
     --reason "private operational reason"
   ```

   等待私有仓库的 `Record publication removal` 成功后再启动公开预览。公开 workflow 会复核 inventory、操作类型和书号均与已登记记录一致。

4. 手动运行 `Remove Publication`，选择 `preview`，按清单填写 operation、book ID、edition、`reasonSha256`、`inventorySha256` 和确认短语。
5. 在受 Access 保护的 `removal-preview` 候选站检查删除结果。
6. 使用完全相同的输入选择 `promote`；等待 `ebook-production` 人工批准。

工作流会重新计算本地与远程 inventory。任一文件、Release 正文、资产 ID、大小或摘要变化都会拒绝执行。生产清洁版本部署成功后才删除 Release/tag；随后用清洁内容覆盖持久预览分支并删除其他历史 Cloudflare 部署。

若公开提交已经部署、但 Release 或 Cloudflare 历史部署清理失败，不回滚公开删除。私有台账会把该 inventory 记为 `failed`；使用完全相同的输入重新运行 `promote`，从已完成边界继续收口。不得生成新的 inventory 掩盖未完成事务。

## 变换规则

- 撤回唯一版次会被拒绝，必须改用整书下架。
- 撤回最新版后，上一现存版恢复为默认和 GitHub Latest Release。
- 撤回中间版后，后继版重新与最近的前一现存版比较。
- 撤回最早版后，下一现存版标记为“现存最早版本”，不会伪称初版。
- 下架会删除书目、全部版次数据、封面、自动简讯、显式关联勘误和对应 pins。
- 普通公告出现目标书号、书名或 tag 时预检失败，要求人工处理，避免误删正文。
- 失效的检查更新和勘误二维码只显示“资源不可用”，不显示已删除书名、版次或原因。

## 广播更正

删除发生在每日广播前时，目标事件从公开 feed 消失，尚未发送的通道保持静默。若 QQ 或 ntfy 的状态文件已经记录原事件，私有台账会只为实际发送过的通道生成具名更正，并在下一次 06:00 广播中发送。更正不公开原因。

## 删除边界

“删除”只保证当前公开网站、GitHub Release/tag 和受项目控制的 Cloudflare 部署不再提供目标资源。Git 历史、第三方缓存、用户下载和本地克隆无法保证消失。只有敏感信息或法律要求才另行执行 Git 历史清理。

参考：[GitHub CLI Release 删除](https://cli.github.com/manual/gh_release_delete)、[Cloudflare Pages 部署 API](https://developers.cloudflare.com/pages/configuration/api/)、[GitHub 敏感数据清除](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)。
