# 调研记录

调研日期：2026-06-09。

## OpenAI / GPT Image 2

- OpenAI Images API exposes image generation through `/v1/images/generations`; the current image guide and API reference describe `model`, `prompt`, `size`, `quality`, `background`, and output controls for GPT image models.
- This skill targets `gpt-image-2` because the user explicitly requested it and current official OpenAI image-generation examples describe `gpt-image-2` as the latest GPT Image model. Account verification, org access, regional availability, or relay support can still differ; if an environment has not enabled that model, set `OPENAI_IMAGE_MODEL` to the officially available replacement and keep the rest of the workflow.
- Common API aspect sizes used by this skill are `1024x1024`, `1536x1024`, and `1024x1536`. They map cleanly to square, landscape, and portrait 小红书 cards. 2k/4k outputs are produced by generating the nearest supported API size and then upscaling locally.
- Relay support: OpenAI-compatible proxy or relay services usually preserve the `/v1/images/generations` path. Set `OPENAI_BASE_URL` to the relay base, not the full endpoint.

Primary sources checked:

- OpenAI image generation guide: https://platform.openai.com/docs/guides/image-generation
- OpenAI Images API reference: https://platform.openai.com/docs/api-reference/images
- baoyu image generation reference in `JimLiu/baoyu-skills`: https://github.com/JimLiu/baoyu-skills

## 微信公众号

微信公众号存在成熟官方接口路径，但账号必须具备相应权限、IP 白名单、AppID/AppSecret、素材和发布权限。

- `access_token`: official credential for calling 公众号 APIs; token is obtained from `https://api.weixin.qq.com/cgi-bin/token` with `grant_type=client_credential`, `appid`, and `secret`.
- Permanent material upload through `material/add_material` is needed for article cover `thumb_media_id` in most draft flows.
- Inline article images must be uploaded through `media/uploadimg`; external image URLs in article HTML can be filtered or fail in draft/publish flows.
- Draft creation uses `draft/add` and an `articles` array with fields such as `title`, `author`, `digest`, `content`, `thumb_media_id`, `content_source_url`, `need_open_comment`, and `only_fans_can_comment`.
- Publishing a draft uses `freepublish/submit` with `media_id`; the response returns a publish id/article id depending on account state and API version. Status should be polled before claiming success.
- WeChat publish API eligibility changed in July 2025: 个人账号, uncertified enterprise accounts, and accounts that cannot complete certification may not have publish API permissions. Verify account type before promising `freepublish/submit`.

Primary sources checked:

- Get access token: https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html
- Draft box / add draft: https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html
- Free publish submit/status docs under the WeChat offiaccount API documentation: https://developers.weixin.qq.com/doc/offiaccount/Publish/

## 小红书

没有找到面向普通创作者账号、稳定公开、可直接通过 `access_key` 一键发布图文笔记的官方服务端 API 文档。小红书确有开放平台、专业号、商业/广告/生态合作入口，但这些入口通常面向特定业务、资质或合作场景，不能等同于普通账号的通用发笔记 API。

可行方案分层：

1. 稳定默认方案：生成可发布包，包括标题、正文、标签、图片、图片顺序和发布清单，由人登录小红书确认发布。
2. 半自动方案：使用浏览器自动化预填内容，人工确认发布。需要登录态/Cookie，稳定性受网页改版、风控和验证码影响。
3. 不推荐方案：逆向私有接口直接发笔记。存在封禁、风控、接口失效和合规风险，不应由 skill 默认实现。
4. 分享开放平台/第三方发布工具可以把素材拉起或填充到小红书客户端，但这通常不是“服务端直接发布成功”；至少需要用户确认，且状态可能只代表已提交或已拉起。

Primary sources checked:

- 小红书开放平台入口: https://redopen.xiaohongshu.com/
- 小红书分享开放平台入口: https://agora.xiaohongshu.com/
- 小红书 Marketing API / 商业开放入口: https://ad-market.xiaohongshu.com/
- 小红书商业/品牌合作入口: https://www.xiaohongshu.com/

## baoyu-xhs-skill 风格参考

公开搜索结果显示 `JimLiu/baoyu-skills` 下有与小红书图片相关的 skill，例如 `baoyu-xhs-images`。可参考的不是具体私有素材，而是工作方式：

- 先把内容拆成封面、核心观点、细节、总结等卡片。
- 小红书图常用竖版卡片、强标题、清晰留白、对比块、贴纸式标注、真实截图/渲染感。
- 文案必须像真人笔记，不要像把英文 changelog 翻译成中文。

Source checked:

- https://github.com/JimLiu/baoyu-skills
