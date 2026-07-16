# ntfy 备用信号源订阅指南

文火广播站同时通过自托管 ntfy 发布网站更新通知。该通道用于接收新书上架、电子书更新和网站公告；正式电子书版本记录仍以书目详情页和 GitHub Releases 为准。

## 订阅信息

- 显示名称：`文火广播站`
- 服务器：`https://culturalsimmer-notify.duckdns.org`
- Topic：`cultural-simmer-updates`
- Topic 地址：`https://culturalsimmer-notify.duckdns.org/cultural-simmer-updates`

<div align="center">
  <a href="https://culturalsimmer-notify.duckdns.org/cultural-simmer-updates"><img src="assets/ntfy/topic.svg" width="180" alt="打开文火广播站 Topic"></a><br>
  <strong>文火广播站 Topic</strong>
</div>

请勿将本通道用于发布消息，也不要向他人发送账号、密码或访问令牌。

## Android 客户端

1. 扫描或点击“Android 客户端”二维码，按照 ntfy 官方页面提供的 Google Play、F-Droid 或 GitHub Releases 渠道安装客户端。

   <a href="https://docs.ntfy.sh/subscribe/phone/"><img src="assets/ntfy/android-client.svg" width="160" alt="打开 ntfy Android 客户端安装说明"></a>

2. 扫描“Android 一键订阅”二维码。二维码包含 ntfy 官方 `ntfy://` 深层链接，会打开客户端并添加文火广播站。

   <a href="https://culturalsimmer-notify.duckdns.org/cultural-simmer-updates"><img src="assets/ntfy/android-subscribe.svg" width="160" alt="扫描后使用 Android ntfy 一键订阅文火广播站；点击打开 Topic 备用页"></a>

3. 确认服务器和 Topic 后完成订阅，并允许 ntfy 发送系统通知。
4. 若一键订阅没有唤起客户端，请扫描或点击上方“文火广播站 Topic”二维码，然后在 ntfy 中手动添加以下地址：

   ```text
   https://culturalsimmer-notify.duckdns.org/cultural-simmer-updates
   ```

5. 如需减少后台延迟，请根据客户端提示启用即时传递，并在 Android 系统设置中允许 ntfy 后台运行。

Android 深层链接的完整格式与兼容性说明：

<a href="https://docs.ntfy.sh/subscribe/phone/#ntfy-links"><img src="assets/ntfy/android-deep-links.svg" width="160" alt="打开 ntfy Android 深层链接说明"></a>

## iOS Safari

iOS Web Push 需要 iOS 16.4 或更高版本，并且 ntfy 必须作为 Web App 添加到主屏幕。

ntfy 的 iOS PWA 安装说明：

<a href="https://docs.ntfy.sh/subscribe/pwa/#safari-on-ios"><img src="assets/ntfy/ios-pwa.svg" width="160" alt="打开 ntfy iOS PWA 安装说明"></a>

1. 使用 Safari 扫描或点击上方“文火广播站 Topic”二维码。不要使用 Safari 以外的内置浏览器完成安装。

   <a href="https://culturalsimmer-notify.duckdns.org/cultural-simmer-updates"><img src="assets/ntfy/topic.svg" width="160" alt="使用 Safari 打开文火广播站 Topic"></a>

2. 点击 Safari 的“分享”按钮，选择“添加到主屏幕”。
3. 保持“作为 Web App 打开”开启，然后点击“添加”。

   <a href="https://support.apple.com/guide/iphone/iphea86e5236/ios"><img src="assets/ntfy/ios-web-app.svg" width="160" alt="打开 Apple 主屏幕 Web App 指南"></a>

4. 返回主屏幕，从新添加的 ntfy 图标打开 Web App。
5. 在 ntfy 中订阅 `cultural-simmer-updates`。若 Topic 没有自动显示，请点击添加订阅并输入完整 Topic 地址。
6. 点击订阅或启用后台通知，并在 iOS 的系统弹窗中选择“允许”。通知权限只能由已安装的 Web App 在用户操作后申请。

   <a href="https://docs.ntfy.sh/subscribe/web/#background-notifications"><img src="assets/ntfy/web-push.svg" width="160" alt="打开 ntfy Web Push 说明"></a>

安装完成后，无需保持 Safari 或 ntfy Web App 打开。为避免浏览器暂停长期未使用的后台订阅，建议至少每周打开一次 ntfy Web App。

## 故障检查

未收到通知时，依次检查：

1. 设备能够正常访问 `https://culturalsimmer-notify.duckdns.org`。
2. ntfy 中的 Topic 名称准确，且没有被静音。
3. 系统通知设置允许 ntfy 或 ntfy Web App 显示通知。
4. iOS 用户是从主屏幕图标启动 Web App，而不是仅在 Safari 标签页中打开网页。
5. 重新打开 ntfy，刷新订阅状态后等待下一条正式通知。

请勿通过公开渠道提交账号、密码、令牌、设备标识或完整诊断日志。
