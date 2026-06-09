import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_wechat.py"


def load_module():
    spec = importlib.util.spec_from_file_location("publish_wechat", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_draft_payload_contains_required_wechat_fields():
    mod = load_module()

    payload = mod.build_draft_payload(
        title="一次发布链路整理",
        author="产品小记",
        digest="这次把发布链路里的几个坑记下来。",
        html="<p>今天主要处理草稿和发布状态。</p>",
        thumb_media_id="MEDIA_ID_123",
        source_url="https://example.com/changelog",
        open_comment=True,
    )

    article = payload["articles"][0]
    assert article["title"] == "一次发布链路整理"
    assert article["author"] == "产品小记"
    assert article["thumb_media_id"] == "MEDIA_ID_123"
    assert article["content_source_url"] == "https://example.com/changelog"
    assert article["need_open_comment"] == 1
    assert article["only_fans_can_comment"] == 0


def test_digest_is_truncated_to_wechat_limit():
    mod = load_module()

    payload = mod.build_draft_payload(
        title="标题",
        author="作者",
        digest="x" * 200,
        html="<p>正文</p>",
        thumb_media_id="MEDIA_ID_123",
    )

    assert len(payload["articles"][0]["digest"]) == 120


def test_api_urls_are_built_with_access_token():
    mod = load_module()

    assert mod.wechat_url("draft/add", "TOKEN") == (
        "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=TOKEN"
    )


def test_material_upload_url_and_form_fields_are_supported(tmp_path):
    mod = load_module()
    image = tmp_path / "cover.jpg"
    image.write_bytes(b"jpg")

    request = mod.build_material_upload_request("TOKEN", image, material_type="thumb")

    assert request["url"] == (
        "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=TOKEN&type=thumb"
    )
    assert request["file_field"] == "media"
    assert request["file_path"] == str(image)


def test_thumb_upload_rejects_non_jpg_or_large_file(tmp_path):
    mod = load_module()
    png = tmp_path / "cover.png"
    png.write_bytes(b"png")
    jpg = tmp_path / "cover.jpg"
    jpg.write_bytes(b"x" * (64 * 1024 + 1))

    for file_path in [png, jpg]:
        try:
            mod.build_material_upload_request("TOKEN", file_path, material_type="thumb")
        except ValueError as exc:
            assert "thumb" in str(exc)
        else:
            raise AssertionError("invalid thumb file should fail")


def test_inline_image_upload_uses_uploadimg_endpoint(tmp_path):
    mod = load_module()
    image = tmp_path / "inline.png"
    image.write_bytes(b"png")

    request = mod.build_inline_image_upload_request("TOKEN", image)

    assert request["url"] == "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=TOKEN"
    assert request["file_field"] == "media"
    assert request["file_path"] == str(image)
