import importlib.util
import http.client
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_gpt_image2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_gpt_image2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolves_defaults_and_relay_base_url(monkeypatch):
    mod = load_module()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example.com/openai/v1/")

    settings = mod.resolve_settings(
        prompt="做一张小红书封面",
        aspect="portrait",
        resolution="2k",
        output_format="png",
    )

    assert settings.model == "gpt-image-2"
    assert settings.endpoint == "https://relay.example.com/openai/v1/images/generations"
    assert settings.api_size == "1024x1536"
    assert settings.target_size == (2048, 3072)
    assert settings.api_key == "test-key"


def test_build_payload_uses_supported_gpt_image_fields():
    mod = load_module()
    settings = mod.ImageSettings(
        prompt="生成一张开发日志封面",
        model="gpt-image-2",
        endpoint="https://api.openai.com/v1/images/generations",
        api_key="key",
        api_size="1536x1024",
        target_size=(1536, 1024),
        quality="high",
        output_format="webp",
        background="opaque",
        timeout=60,
        retries=2,
        extra_headers={},
    )

    payload = mod.build_payload(settings)

    assert payload == {
        "model": "gpt-image-2",
        "prompt": "生成一张开发日志封面",
        "n": 1,
        "size": "1536x1024",
        "quality": "high",
        "output_format": "webp",
        "background": "opaque",
    }


def test_dry_run_does_not_require_api_key(monkeypatch, tmp_path):
    mod = load_module()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("小红书风格运营封面", encoding="utf-8")
    out_file = tmp_path / "request.json"

    exit_code = mod.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--out",
            str(tmp_path / "cover.png"),
            "--dry-run",
            "--dry-run-output",
            str(out_file),
        ]
    )

    assert exit_code == 0
    data = out_file.read_text(encoding="utf-8")
    assert '"model": "gpt-image-2"' in data
    assert '"prompt": "小红书风格运营封面"' in data


def test_cli_timeout_overrides_env(monkeypatch, tmp_path):
    mod = load_module()
    monkeypatch.setenv("OPENAI_IMAGE_TIMEOUT", "120")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    out_file = tmp_path / "request.json"

    exit_code = mod.main(
        [
            "--prompt",
            "测试超时参数",
            "--out",
            str(tmp_path / "cover.png"),
            "--timeout",
            "15",
            "--dry-run",
            "--dry-run-output",
            str(out_file),
        ]
    )

    assert exit_code == 0
    data = out_file.read_text(encoding="utf-8")
    assert '"timeout": 15' in data


def test_request_image_uses_stdlib_fallback_when_requests_missing(monkeypatch):
    mod = load_module()
    settings = mod.ImageSettings(
        prompt="生成一张开发日志封面",
        model="gpt-image-2",
        endpoint="https://relay.example.com/v1/images/generations",
        api_key="key",
        api_size="1024x1536",
        target_size=(1024, 1536),
        quality="high",
        output_format="png",
        background="opaque",
        timeout=60,
        retries=0,
        extra_headers={"X-Test": "1"},
    )
    captured = {}

    monkeypatch.setitem(sys.modules, "requests", None)

    def fake_post_json(url, headers, payload, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {"data": [{"b64_json": "aGVsbG8="}]}

    monkeypatch.setattr(mod, "post_json_stdlib", fake_post_json)

    response = mod.request_image(settings)

    assert response["data"][0]["b64_json"] == "aGVsbG8="
    assert captured["url"] == settings.endpoint
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["headers"]["X-Test"] == "1"


def test_stdlib_post_recovers_json_from_incomplete_read(monkeypatch):
    mod = load_module()
    payload = {"data": [{"b64_json": "aGVsbG8="}]}
    partial = json.dumps(payload).encode("utf-8")

    class BrokenResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            raise http.client.IncompleteRead(partial=partial, expected=10)

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda request, timeout: BrokenResponse())

    result = mod.post_json_stdlib(
        "https://relay.example.com/v1/images/generations",
        {"Authorization": "Bearer key"},
        {"model": "gpt-image-2"},
        30,
    )

    assert result == payload
