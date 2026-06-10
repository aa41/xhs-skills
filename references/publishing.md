# 发布方案

## 决策树

1. 要发微信公众号，并且有 AppID/AppSecret/IP 白名单/API 权限：可以走官方 API。
2. 要发小红书普通账号：默认生成发布包，不承诺稳定一键发布。
3. 用户明确接受浏览器自动化风险：可以做半自动预填，但必须人工确认发布。
4. 用户要求 `access_key` 直发小红书：先要求其提供对应账号类型的官方文档；没有文档时不要承诺。
5. 用户要求 browser-use、Browser、Chrome 或 GUI 登录/预填：读取 `references/gui-automation.md`，按“辅助发布”处理，不把 GUI 操作说成官方 API。

## 微信公众号官方 API

需要：

- `WECHAT_APP_ID`
- `WECHAT_APP_SECRET`
- 服务器 IP 白名单
- 草稿箱、素材、发布权限
- 封面图对应的 `thumb_media_id`

发布权限 caveat：2025-07 后，个人账号、未认证企业账号、以及无法认证的账号可能无法继续使用发布接口权限。先确认账号类型和接口权限，再承诺 `freepublish/submit`。

常用接口：

- 获取 `access_token`: `GET https://api.weixin.qq.com/cgi-bin/token`
- 上传永久素材/封面: `POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=ACCESS_TOKEN&type=thumb`
- 上传正文内联图片: `POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN`
- 新增草稿: `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN`
- 发布草稿: `POST https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=ACCESS_TOKEN`
- 查询发布状态: `POST https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token=ACCESS_TOKEN`

注意：

- 先创建草稿，再发布；不要把草稿成功说成发布成功。
- 发布后需要查询状态。
- 素材上传和封面图审核可能失败。
- `thumb` 缩略图素材通常要求 JPG/JPEG 且 64KB 内。GPT 生成的大图不要直接当 `thumb`；先压缩/转换，或准备独立缩略图。
- 正文 HTML 中的图片先用 `upload-inline-image` 上传并替换成接口返回 URL，不要直接使用外部图片 URL。
- 摘要建议控制在 120 字以内。

命令顺序：

1. 准备合规封面缩略图，例如 `cover-thumb.jpg`，大小不超过 64KB。
2. `python3 scripts/publish_wechat.py upload-material --file cover-thumb.jpg --material-type thumb`
3. 正文内联图逐张执行 `python3 scripts/publish_wechat.py upload-inline-image --file inline.png`，用返回 URL 替换 HTML 图片地址。
4. 把封面返回的 `media_id` 放入草稿 payload 的 `thumb_media_id`。
5. `python3 scripts/publish_wechat.py draft --payload article.json`
6. 用草稿返回的 `media_id` 执行 `python3 scripts/publish_wechat.py publish --media-id MEDIA_ID`。
7. 用发布返回的 `publish_id` 执行 `python3 scripts/publish_wechat.py status --publish-id PUBLISH_ID`。

## 小红书

默认稳定交付物：

- `title.txt`
- `caption.md`
- `tags.txt`
- `images/`
- `publish-checklist.md`
- `metadata.json`

不要承诺：

- 不承诺普通账号通过 `access_key` 稳定一键发布。
- 不承诺 Cookie 自动化长期稳定。
- 不承诺绕过验证码、风控、审核或平台限制。

可以说明：

- Cookie/浏览器自动化可用于半自动预填，但需要用户授权、登录态和人工确认。
- GUI 自绘制发布只能做到“辅助操作”，不能绕过平台审核和风控。
- 逆向接口不是成熟稳定方案，不应作为默认实现。

## GUI 辅助调用

显式触发语：

- `用 @chrome 辅助打开小红书创作平台，把 xhs-package 预填好，停在发布前让我确认`
- `用 @browser 打开小红书发布页，只检查登录状态和入口，不要点击发布`
- `用 @chrome 打开微信公众号后台，我扫码登录后帮我核对草稿`
- `用公众号 API 创建草稿，不发布`
- `用公众号 API 发布这个 draft media_id，并查询发布状态`

原则：

- Chrome 适合复用用户登录态；Browser 适合干净页面检查；Computer Use 只在网页 DOM 自动化不可用时使用。
- 登录、扫码、验证码由用户完成，agent 不读取 Cookie、密码或短信码。
- 上传图片、粘贴正文、保存草稿和最终发布都可能向第三方传输数据；没有明确授权时，操作前必须确认。
- 最终公开发布需要 action-time 确认，或停在发布按钮前让用户自行点击。
