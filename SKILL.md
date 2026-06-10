---
name: xhs-wechat-publisher
description: Use when creating 小红书 or 微信公众号 posts from dev logs, release notes, operations updates, or product diaries; when planning GPT Image 2 visuals; when reviewing copy for anti-AI tone; or when packaging/publishing content to XHS or WeChat.
---

# 小红书 / 微信公众号发布系统

Use this skill to turn real work notes into publishable 小红书 notes and 微信公众号 articles. The default output is a reviewed manuscript, a 1-5 image plan, generated image commands, and a platform-specific publishing package.

## Required Flow

1. Identify the role: `daily-dev-log`, `weekly-dev-log`, `release-note`, `daily-ops`, or `product-diary`.
2. Draft in the chosen role's voice from `references/roles.md`.
3. Run `scripts/review_content.py` before treating copy as ready. This is the required 反AI味 gate. Fix every `ai_tone`, `translation_smell`, and `role_fit` issue.
4. Run `scripts/plan_xhs_assets.py` to decide whether the note needs 1-5 images. Use the plan to build GPT Image 2 prompts.
5. Generate or dry-run images with `scripts/generate_gpt_image2.py`. Use `.env` or environment variables for keys and relay endpoints. `gpt-image-2` is the requested default; if the user's account or relay does not expose it, set `OPENAI_IMAGE_MODEL` to the officially available image model for that environment.
6. Run a multi-agent review: one agent checks role/personality, one checks platform fit, one checks publishing risk. If external subagents are unavailable, do the same review as three named passes and report issues separately.
7. Package:
   - 小红书: use `scripts/package_xhs_note.py`; default to manual upload with assets and captions.
   - 微信公众号: use `scripts/publish_wechat.py` for inline image upload, cover material upload, draft creation, or official publish only when the account has valid credentials, certification status, and API permission.
   - GUI-assisted publishing: if the user explicitly asks for browser-use, Browser, Chrome, or GUI login/prefill, read `references/gui-automation.md` and treat it as assisted prefill/checking unless an official API is available.

## Role Rules

Load `references/roles.md` when choosing or writing for a role. Keep voice concrete and lived-in:

- Prefer real nouns: module names, metrics, bugs, screenshots, decisions, tradeoffs.
- Keep the first person when it helps authenticity.
- Use short Chinese sentences; avoid translated English sentence order.
- Never use filler such as "在这个快节奏的时代", "赋能", "全面升级", "以下是", or "希望对你有帮助".

## Image Generation

Use `scripts/plan_xhs_assets.py` first. The planner maps content complexity to 1-5 cards:

- 1 card: short daily update or one clear takeaway.
- 2-3 cards: note has before/after, steps, or a small story arc.
- 4-5 cards: release notes, weekly logs, multi-part operations summaries.

Use `scripts/generate_gpt_image2.py` with `gpt-image-2`. Supported presets:

- `--resolution 1k`: native API size.
- `--resolution 2k` or `4k`: generate at the nearest supported API aspect size, then upscale locally with Pillow when installed.
- `--aspect square|portrait|landscape`: maps to `1024x1024`, `1024x1536`, or `1536x1024`.

Environment variables:

- `OPENAI_API_KEY`: required unless `--dry-run`.
- `OPENAI_BASE_URL`: optional relay or proxy base, for example `https://relay.example.com/v1`.
- `OPENAI_IMAGE_MODEL`: defaults to `gpt-image-2`.
- `OPENAI_IMAGE_TIMEOUT`, `OPENAI_IMAGE_RETRIES`: optional network controls.

For setup details, copy `.env.example` to `.env` and read `references/image-env.md`.

## Publishing Boundaries

Read `references/publishing.md` before promising automation.

- 微信公众号 has official API paths using `access_token`: inline image upload (`upload-inline-image`), permanent material upload (`upload-material`), draft creation, publish submit, and publish status polling. Check current account eligibility; after July 2025, some personal/uncertified accounts may not have publish API permission.
- 小红书: do not promise stable one-click public-note publishing for normal creator accounts. This skill does not claim that an `access_key` can publish notes unless the user provides official 小红书 partner/API documentation for their account type.
- For 小红书, default to a prepared publish package and manual confirmation. Browser/Cookie automation is optional, fragile, and must be labeled experimental.
- For GUI work, prefer Chrome when logged-in state matters, Browser for clean web inspection, and Computer Use only when DOM/browser automation is insufficient. Never read cookies or bypass login, CAPTCHA, review, or risk controls. Stop before final public publish unless the user confirms at action time.

## Multi-Agent Review Rubric

Run these three review passes before final delivery:

1. **人格/角色审稿**: Does it sound like the chosen role wrote it today? Remove generic marketing and AI filler.
2. **平台适配审稿**: 小红书 needs a strong first screen, searchable title, swipe-worthy card order, and natural tags. 公众号 needs a durable headline, clean digest, readable article structure.
3. **发布风险审稿**: Check credentials, API permissions, platform policy risk, image rights, sensitive claims, and whether 小红书 automation is being overstated.

## Reference Map

- `references/research.md`: current research notes and source links.
- `references/roles.md`: role presets and voice constraints.
- `references/style-guide.md`: anti-AI writing and 小红书 visual guidance.
- `references/image-env.md`: GPT Image 2 `.env` setup for official OpenAI or relay services.
- `references/publishing.md`: WeChat API and XHS publishing decision tree.
- `references/gui-automation.md`: explicit Browser/Chrome/Computer Use/browser-use assisted publishing modes and safety boundaries.
- `scripts/generate_gpt_image2.py`: GPT Image 2 request builder/generator.
- `scripts/plan_xhs_assets.py`: content complexity to image plan.
- `scripts/review_content.py`: deterministic copy smell check.
- `scripts/publish_wechat.py`: official WeChat draft/publish helper.
- `scripts/package_xhs_note.py`: manual-ready XHS package builder.
- `scripts/install_skill.py`: copy this skill to Claude Code or Codex skill directories.
