# xhs-wechat-publisher

把开发日志、版本更新、运营记录或产品日记整理成可发布的小红书笔记和微信公众号文章的 Codex/Claude Code skill。

这个仓库包含运行时技能说明、平台发布边界、内容审稿规则、图片规划与生成脚本、公众号 API 辅助脚本，以及小红书人工发布包生成工具。

## 能力概览

- 从真实工作记录生成小红书文案、公众号文章和发布素材计划。
- 支持 `daily-dev-log`、`weekly-dev-log`、`release-note`、`daily-ops`、`product-diary` 五类写作角色。
- 使用 `scripts/review_content.py` 做反 AI 味、翻译腔和角色一致性检查。
- 使用 `scripts/plan_xhs_assets.py` 规划 1-5 张小红书图片卡片。
- 使用 `scripts/generate_gpt_image2.py` 通过 GPT Image 2 或兼容 relay 生成图片。
- 使用 `scripts/package_xhs_note.py` 生成小红书人工发布包。
- 使用 `scripts/publish_wechat.py` 走微信公众号官方 API：上传封面素材、上传正文图片、创建草稿、提交发布、查询发布状态。
- 明确区分可稳定自动化的公众号官方 API 和需要人工确认的小红书普通账号发布流程。

## 目录结构

```text
.
├── SKILL.md                    # skill 运行入口
├── agents/openai.yaml           # Codex skill UI 元数据
├── references/                  # 需要时加载的参考资料
├── scripts/                     # 内容审稿、图片生成、发布和安装脚本
├── tests/                       # pytest 测试
├── examples/                    # 示例 payload
├── .env.example                 # 生图和 API 环境变量模板
└── README.md                    # 仓库说明
```

## 安装

安装到 Codex 和 Claude Code 的本地 skill 目录：

```bash
python3.12 scripts/install_skill.py --target both
```

只安装到 Codex：

```bash
python3.12 scripts/install_skill.py --target codex
```

覆盖已存在的安装目录：

```bash
python3.12 scripts/install_skill.py --target both --force
```

## 环境配置

复制环境模板：

```bash
cp .env.example .env
```

至少配置：

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_MODEL=gpt-image-2
```

如果使用代理或 relay，把 `OPENAI_BASE_URL` 改成对应的 `/v1` 地址。真实 `.env` 不要提交，仓库已经通过 `.gitignore` 排除。

## 内容工作流

1. 选择角色：`daily-dev-log`、`weekly-dev-log`、`release-note`、`daily-ops` 或 `product-diary`。
2. 根据真实记录写初稿，保留具体模块、指标、调试过程和取舍。
3. 运行内容审稿：

```bash
python3.12 scripts/review_content.py \
  --text-file outputs/demo/xhs-caption.md \
  --role daily-dev-log \
  --out outputs/demo/review.json
```

4. 规划小红书图片：

```bash
python3.12 scripts/plan_xhs_assets.py \
  --text-file outputs/demo/xhs-caption.md \
  --role daily-dev-log \
  --out outputs/demo/asset-plan.json
```

5. 根据规划生成图片，或先 dry-run 检查请求：

```bash
python3.12 scripts/generate_gpt_image2.py \
  --prompt-file outputs/demo/prompts/card-01.md \
  --out outputs/demo/card-01.png \
  --aspect portrait \
  --resolution 1k
```

## 小红书发布测试

普通小红书账号默认走人工确认发布包，不承诺稳定一键发布。

```bash
python3.12 scripts/package_xhs_note.py \
  --title "局域网 HTTP 传书链路跑通了" \
  --caption-file outputs/demo/xhs-caption.md \
  --tag 开发日志 \
  --tag 局域网传输 \
  --image outputs/demo/card-01.png \
  --out outputs/demo/xhs-package
```

发布包包含：

- `title.txt`
- `caption.md`
- `tags.txt`
- `images/`
- `publish-checklist.md`
- `metadata.json`

测试方式是登录小红书后台或 App，按 `images/` 编号顺序上传图片，再人工复制标题、正文和标签，最后人工确认发布。

## 微信公众号发布测试

公众号发布分三层测试：本地 dry-run、创建草稿、提交发布。

本地 dry-run 不需要真实触发接口：

```bash
python3.12 scripts/publish_wechat.py draft \
  --payload examples/wechat_draft_payload.json \
  --dry-run \
  --out outputs/demo/wechat-draft-dry-run.json
```

真实 API 测试需要满足：

- `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`，或直接提供 `WECHAT_ACCESS_TOKEN`
- 公众号后台已配置 IP 白名单
- 账号有草稿、素材和发布接口权限
- 封面缩略图是 JPG/JPEG，且小于 64KB

上传封面素材：

```bash
python3.12 scripts/publish_wechat.py upload-material \
  --file outputs/demo/cover-thumb.jpg \
  --material-type thumb \
  --out outputs/demo/wechat-thumb-upload.json
```

把返回的 `media_id` 写入 payload 的 `thumb_media_id` 后创建草稿：

```bash
python3.12 scripts/publish_wechat.py draft \
  --payload outputs/demo/wechat-draft-payload.json \
  --out outputs/demo/wechat-draft-created.json
```

确认草稿无误后再提交发布：

```bash
python3.12 scripts/publish_wechat.py publish \
  --media-id DRAFT_MEDIA_ID \
  --out outputs/demo/wechat-publish-submit.json
```

查询发布状态：

```bash
python3.12 scripts/publish_wechat.py status \
  --publish-id PUBLISH_ID \
  --out outputs/demo/wechat-publish-status.json
```

注意：草稿创建成功不等于发布成功，发布后必须查询状态。

## 发布边界

- 小红书普通账号：默认只生成发布包并要求人工确认；不承诺 Cookie 自动化、逆向接口或 `access_key` 直发稳定可用。
- 微信公众号：只使用官方 API；是否能发布取决于账号类型、认证状态、接口权限和后台配置。
- 图片生成：优先使用 GPT Image 2；如果 relay 不支持对应模型，需要在 `.env` 中显式覆盖 `OPENAI_IMAGE_MODEL`。
- 密钥：不要提交 `.env`、access token、AppSecret 或 relay key。

## 开发与验证

安装依赖：

```bash
python3.12 -m pip install -r requirements.txt
```

运行测试：

```bash
python3.12 -m pytest -q
```

建议提交前检查：

```bash
git status --short
python3.12 -m pytest -q
```

