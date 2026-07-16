# 勘误与网站问题流程

**适用对象：** 网站维护者与问题处理者。

本文记录读者入口到 GitHub Issue/Project 的公开接口。Tally、Make 和 GitHub 的凭据、字段索引、账号信息及事故记录只保存在本地维护资料中。

## 读者入口

电子书中的勘误二维码使用：

```text
https://fulinte1966.github.io/CulturalSimmer/errata/?bookId={bookId}&edition={edition}
```

页面只接受仓库中存在的索书号和正整数版次：

- 参数对应最新版时，跳转到详情页并一次性打开嵌入表单；
- 参数对应旧版时，先进入检查更新页并提示取得最新版；
- 参数无效或书目不存在时，不根据 URL 构造书名、封面或下载地址。

详情页使用一次性 `errata=1` 状态打开表单，并立即从地址栏移除参数。整页刷新回到默认勘误提示；表单内返回会重建嵌入 iframe，方便再次提交。

## 提交链路

```text
详情页勘误入口
  -> Tally 隐藏字段接收 bookId 与 edition
  -> Make webhook 转换为 GitHub Issue
  -> Issue 使用“书籍勘误”标签
  -> Route issue to project workflow
  -> 加入 GitHub Project 并写入“索书号”字段
```

自动创建的勘误 Issue 标题应保留 `{bookId}_v{edition}: {submissionId}` 结构，正文至少包含索书号、版次、位置和勘误内容。不得把含签名参数的 Tally 提交预览或 PDF URL 写入公开 Issue。

Make 应通过 GitHub REST API 创建 Issue，并使用满足当前调用所需的最小权限凭据。仓库只保存输入输出契约，不保存 webhook URL、Authorization header、字段数组位置或 token。

## 网站问题

网站功能和显示问题使用 `.github/ISSUE_TEMPLATE/website-bug.yml`。该表单自动添加 `网站捉虫` 标签；路由 workflow 将其加入同一 Project，并把“索书号”字段写为“网站捉虫”。

`.github/ISSUE_TEMPLATE/config.yml` 不提供裸 Tally URL，因为直接访问不能可靠携带书目隐藏字段；联系入口只提示读者从网站详情页进入。

## GitHub 配置

公开 workflow 依赖：

- Issue 标签：`书籍勘误`、`网站捉虫`；
- Project 文本字段：`索书号`；
- repository secret：`PROJECT_TOKEN`。

`PROJECT_TOKEN` 只用于把 Issue 加入用户级 Project 和更新字段。更新 Project 编号、字段名或 owner 时，应在同一提交中更新 workflow 和本文；secret 实值始终通过 GitHub 设置页维护。

## 验证

网站修改后至少检查：

1. 最新版勘误 URL 能打开对应详情页表单；
2. 旧版勘误 URL 转入检查更新页；
3. 刷新详情页不会再次自动打开表单；
4. 网站问题表单能创建带正确标签的 Issue；
5. 测试勘误经 Tally/Make 创建 Issue 后能进入 Project，并写入正确索书号；
6. workflow 日志不包含表单内容之外的凭据或签名 URL。

自动化代码修改后运行 `npm run verify`，并在合并后观察一次真实但不含隐私内容的端到端测试。

## 参考

- [GitHub Issue forms syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues/syntax-for-githubs-form-schema)
- [GitHub Projects GraphQL API](https://docs.github.com/en/graphql/reference/objects#projectv2)
- [GitHub Actions secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
