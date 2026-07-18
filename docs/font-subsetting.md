# 字体子集化

**适用对象：** 网站样式与构建维护者。

网站只发布 `public/fonts/subset/` 中的 WOFF2 子集。完整源字体位于 `tools/font-sources/`，Astro 不会把它们复制到站点产物。逐文件许可和许可证全文见 `tools/font-sources/LICENSES.md`。

## 为什么需要双遍构建

字体字符不仅来自 `src/`，还来自构建期生成的 HTML，例如书目元数据、首页日期与天气。正确顺序是：

```text
第一次构建生成最终可见文字
  -> 扫描 src、public/assets 与 dist
  -> 生成 WOFF2 子集
  -> 第二次构建写入最新字体
```

统一命令：

```bash
mise run fonts
# 等同于 npm run fonts:refresh
```

不要用人工 safelist 猜测构建期字符，也不要只在第一次构建前生成子集。新增公告、书名、分类、按钮文案或其他可见中文后都应执行双遍构建。

## 生成器

`scripts/subset_fonts.py` 使用 FontTools：

- CJK 字体只保留扫描到的字符；
- 拉丁字体使用明确的 Unicode 范围；
- 保留布局特性和名称信息；
- 输出 WOFF2，并移除 hinting 以减小体积。

需要单独运行生成器时：

```bash
python -m pip install -r scripts/requirements.txt
npm run fonts:subset
```

CSS 的 `@font-face` 应继续指向 `public/fonts/subset/*.woff2` 并使用 `font-display: swap`。`npm run verify` 和生产部署都会执行双遍构建，因此构建产物以当次生成的字体为准。

第二次构建完成后，`scripts/apply-public-asset-origin.mjs` 会根据实际 WOFF2
内容生成 SHA-256 短指纹，并把它写入构建产物中的字体 URL 查询参数。字体内容
变化时 URL 必然变化，因此浏览器和 CDN 可以长期缓存字体，而不会在发布新版后
继续复用缺字的旧子集。不要手工填写或固定这个指纹。

## 验证

1. 运行 `npm run fonts:refresh`；
2. 在 Chromium 中等待 `document.fonts.ready`；
3. 用 `document.fonts.check()` 检查目标字族、字号和实际文案；
4. 检查控制台、横向溢出和字体请求的 `font/woff2` MIME；
5. 同时验证 Cloudflare Pages 主站与 GitHub Pages 备份的同源字体响应。

字体源文件、授权信息或文件名变化时，应同步修改 `scripts/subset_fonts.py` 和本文件。不要把临时子集文本、浏览器缓存或本地字体安装目录提交到仓库。
