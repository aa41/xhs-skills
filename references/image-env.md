# 生图环境配置

`scripts/generate_gpt_image2.py` 会自动读取当前目录下的 `.env`。真实测试前先执行：

```bash
cp .env.example .env
```

然后编辑 `.env`。

## 官方 OpenAI

```env
OPENAI_API_KEY=你的真实 key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=high
OPENAI_IMAGE_BACKGROUND=opaque
OPENAI_IMAGE_TIMEOUT=120
OPENAI_IMAGE_RETRIES=2
OPENAI_EXTRA_HEADERS={}
```

## 中转服务

如果使用 OpenAI-compatible relay，只改两项：

```env
OPENAI_API_KEY=中转服务给你的 key
OPENAI_BASE_URL=https://your-relay.example.com/v1
```

有些中转服务需要额外 header，把它写成 JSON：

```env
OPENAI_EXTRA_HEADERS={"X-Relay-Project":"xhs-publisher"}
```

## 先做 dry-run

dry-run 不会调用接口，用来确认 endpoint、model、size 和 prompt：

```bash
python3 scripts/generate_gpt_image2.py \
  --prompt "小红书竖版封面：一次真实的开发日志，干净排版，有日志块和手写标注" \
  --out outputs/test-cover.png \
  --aspect portrait \
  --resolution 1k \
  --dry-run \
  --dry-run-output outputs/test-cover.request.json
```

检查 `outputs/test-cover.request.json` 后，再去掉 `--dry-run` 做真实测试。

## 常用参数

- `--aspect portrait`: 小红书竖版，API size 为 `1024x1536`。
- `--aspect square`: 方图，API size 为 `1024x1024`。
- `--aspect landscape`: 横图，API size 为 `1536x1024`。
- `--resolution 1k`: 直接保存 API 图。
- `--resolution 2k` / `4k`: 先生成对应 aspect 的 API 图，再本地放大。

## 注意

- `.env` 已被 `.gitignore` 忽略，不要把真实 key 写进 `.env.example`。
- 如果接口返回模型无权限，把 `OPENAI_IMAGE_MODEL` 改成你的账号或中转服务支持的模型。
- 如果中转服务的 base URL 已经包含 `/v1`，不要再额外拼一次 `/v1`。
