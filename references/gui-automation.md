# GUI 辅助发布

本 skill 默认不绑定某一个 GUI 框架。它可以在运行环境提供对应工具时，显式调用 Browser、Chrome、Computer Use 或外部 browser-use 做辅助登录、页面核对和表单预填。

## 支持矩阵

| 场景 | 推荐方式 | 稳定性 | 最终发布 |
| --- | --- | --- | --- |
| 小红书普通账号发布图文 | Chrome 或 Browser 辅助打开创作页、上传发布包、预填标题/正文/标签 | 实验性，受登录态、验证码、网页改版和风控影响 | 必须人工确认 |
| 微信公众号网页后台发文 | Chrome 辅助打开 `mp.weixin.qq.com`、扫码登录、检查草稿 | 可做核对/预填，但不如官方 API 稳定 | 必须人工确认 |
| 微信公众号官方 API | `scripts/publish_wechat.py` | 稳定性取决于账号权限、IP 白名单和素材审核 | 用户显式执行 `publish` 后可提交 |
| 本机 App 或浏览器无法被 DOM 自动化识别 | Computer Use | 只能做屏幕级辅助操作 | 必须人工确认 |
| 独立 Python browser-use 项目 | 用户另行配置 browser-use、LLM key、浏览器 profile 后可接入 | 不随本 skill 默认安装 | 必须遵守同样确认规则 |

## 显式调用短语

用户可以这样要求：

- `用 @chrome 辅助打开小红书创作平台，把 xhs-package 预填好，停在发布前让我确认`
- `用 @browser 打开小红书发布页，只检查登录状态和入口，不要点击发布`
- `用 @chrome 打开微信公众号后台，我扫码登录后帮我核对草稿`
- `用公众号 API 创建草稿，不发布`
- `用公众号 API 发布这个 draft media_id，并查询发布状态`

如果用户只说“一键发布小红书”，必须澄清为：

1. 生成发布包并人工发布。
2. GUI 辅助预填，人工确认发布。
3. 如果用户有官方合作/API 文档，再按文档评估直发。

## 操作边界

- 不读取、导出或复用 Cookie、localStorage、密码、短信码、扫码凭证。
- 登录、验证码、扫码授权由用户完成；agent 可以等待页面登录成功。
- 上传图片、粘贴正文、点击保存草稿属于向第三方传输数据。若用户没有在原始请求中明确授权具体数据和目标平台，操作前必须确认。
- 小红书和微信公众号网页后台的最终发布按钮属于外部副作用。即使用户提前说“自动发”，也应在最后一步再次确认，或停在发布按钮前交给用户。
- 不承诺绕过验证码、平台审核、账号风控、资质限制或接口权限限制。

## 推荐流程：小红书 GUI 辅助预填

1. 先用 `scripts/package_xhs_note.py` 生成 `xhs-package/`。
2. 使用 Chrome 优先复用用户现有登录态；没有登录态时打开页面并等待用户登录。
3. 打开 `https://creator.xiaohongshu.com/` 或当前可用的小红书创作入口。
4. 上传 `xhs-package/images/`，按编号顺序选择。
5. 粘贴 `title.txt`、`caption.md`、`tags.txt`。
6. 做首图裁切、错别字、标签、敏感表述检查。
7. 停在最终发布前，让用户确认或自行点击。

## 推荐流程：微信公众号网页核对

优先使用官方 API 创建草稿；网页 GUI 主要用于登录态检查、草稿预览和人工核对。

1. 用 `scripts/publish_wechat.py draft` 创建草稿，或准备 HTML/payload。
2. 用 Chrome 打开 `https://mp.weixin.qq.com/`。
3. 等待用户扫码登录。
4. 打开草稿箱或编辑器，核对标题、摘要、封面、正文图片和排版。
5. 若需要网页端提交发布，停在发布确认前让用户确认。

## 调研依据

- Browser Use 官方 quickstart 显示其定位是 AI browser agent，可配置浏览器、profile、cookies 和 production sandbox；这说明它适合作为 GUI 自动化框架，但不是小红书或微信的发布授权 API。
- 微信官方服务号文档列出草稿管理 `/cgi-bin/draft/add` 和发布能力 `/cgi-bin/freepublish/submit`、`/cgi-bin/freepublish/get`，因此公众号应优先走官方 API。
- 小红书公开网页可访问，但当前环境无法拉取 `creator.xiaohongshu.com`、`redopen.xiaohongshu.com`、`agora.xiaohongshu.com` 的 HTTPS 内容；在没有账号级官方发布 API 文档前，不应宣称普通账号一键发布。

