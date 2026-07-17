# CulturalSimmer 文档索引

本目录只保存读者使用、公开数据契约、可复现构建和贡献维护所必需的文档。根目录 `README.md` 保持简短，详细流程以本页为入口。

## 读者文档

- [ntfy 备用信号源订阅教程](ntfy-subscription-guide.md)：Android 客户端与 iOS Safari/PWA 订阅方法。
- [本站更新归档](site-updates-archive.md)：构建生成的全部公开事件记录。

## 电子书制作与发布

- [电子书上传工作流](ebook-upload-workflow.md)：本地预检、临时 Release、自动入库、正式发布和失败恢复。
- [PDF 元数据契约](pdf/metadata-contract.md)：XMP 字段、校验规则和派生数据。
- [LaTeX 元数据模块](latex/culturalsimmer-ebook-metadata.sty)：供外部 LaTeX 项目复用的元数据接口。
- [电子书版本更新日志规范](release-changelog-conventions.md)：正文快照、差异算法、结构化 changelog 与人工补录。

## 网站维护

- [自动化与构建总览](automation-overview.md)：数据来源、工作流触发条件、权限、验证和失败边界。
- [勘误与网站问题流程](errata-workflow.md)：检查更新、Tally、GitHub Issues 与 Projects 的公开接口契约。
- [本站消息维护规范](site-updates-workflow.md)：人工公告、自动消息、置顶、公开 feed 和归档。
- [字体子集化](font-subsetting.md)：双遍构建和 WOFF2 生成。
- [Cloudflare Pages 镜像](cloudflare-pages.md)：双站部署、缓存边界和凭据配置。
- [静态资源规范](asset-conventions.md)：目录职责、文件命名和 URL 规则。

## 文档公开边界

以下内容应随代码公开，因为它们决定可复现构建、公开接口或贡献行为：

- 安装、测试、构建和发布命令；
- PDF 元数据、更新 feed、书号和 URL 契约；
- 生成文件的来源与维护规则；
- 不含秘密值的 GitHub Actions、Cloudflare Pages 和通知订阅说明。

以下内容只保留在本地，不得提交：

- token、密码、Cookie、私钥、账号、实例 OCID、IP 清单和 `.env` 实值；
- Release 重置备份、事故日志、恢复演练记录和临时测试报告；
- 测试 PDF、设计草稿、完整 Figma 导出和一次性调试文件；
- Codex、Claude 或其他智能体的提示词、规则、会话记录和 Skill。

仓库通过 `.gitignore` 排除 `.codex/`、`.claude/`、`AGENTS.md`、`CLAUDE.md`、`Work/`、`Outputs/`、`.DS_Store` 和 PDF。只对单个克隆生效且不适合共享的额外规则，可写入 `.git/info/exclude`。

## 更新责任

- 修改脚本、workflow、字段或路径时，同一提交必须更新对应流程文档。
- 修改公告后先运行 `npm run updates:archive`。
- 所有提交在合并前运行 `npm run verify`；该命令会根据最终构建产物刷新字体。
- 发布流程变更合并后检查 GitHub Pages、Cloudflare Pages 和对应 GitHub Actions 运行。
