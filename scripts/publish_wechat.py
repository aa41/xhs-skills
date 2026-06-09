#!/usr/bin/env python3
"""Create or publish WeChat official-account drafts through official APIs."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote


WECHAT_API = "https://api.weixin.qq.com/cgi-bin"


def load_dotenv(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def wechat_url(path, access_token):
    return f"{WECHAT_API}/{path}?access_token={quote(access_token)}"


def wechat_url_with_params(path, access_token, params):
    suffix = "".join(f"&{key}={quote(str(value))}" for key, value in params.items())
    return f"{wechat_url(path, access_token)}{suffix}"


def build_material_upload_request(access_token, file_path, material_type="thumb"):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if material_type == "thumb":
        if path.suffix.lower() not in {".jpg", ".jpeg"}:
            raise ValueError("WeChat thumb material must be JPG/JPEG")
        if path.stat().st_size > 64 * 1024:
            raise ValueError("WeChat thumb material must be 64KB or smaller")
    return {
        "url": wechat_url_with_params(
            "material/add_material",
            access_token,
            {"type": material_type},
        ),
        "file_field": "media",
        "file_path": str(path),
    }


def build_inline_image_upload_request(access_token, file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)
    return {
        "url": wechat_url("media/uploadimg", access_token),
        "file_field": "media",
        "file_path": str(path),
    }


def build_draft_payload(
    title,
    author,
    digest,
    html,
    thumb_media_id,
    source_url="",
    open_comment=False,
    fans_only_comment=False,
):
    article = {
        "title": title,
        "author": author,
        "digest": (digest or "")[:120],
        "content": html,
        "thumb_media_id": thumb_media_id,
        "content_source_url": source_url or "",
        "need_open_comment": 1 if open_comment else 0,
        "only_fans_can_comment": 1 if fans_only_comment else 0,
    }
    return {"articles": [article]}


def get_access_token(app_id, app_secret):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for WeChat API calls") from exc

    response = requests.get(
        f"{WECHAT_API}/token",
        params={
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "access_token" not in data:
        raise RuntimeError(f"failed to get access_token: {data}")
    return data["access_token"]


def post_json(path, access_token, payload):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for WeChat API calls") from exc

    response = requests.post(
        wechat_url(path, access_token),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode", 0) not in (0,):
        raise RuntimeError(f"WeChat API error: {data}")
    return data


def upload_material(access_token, file_path, material_type="thumb"):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for WeChat API calls") from exc

    request = build_material_upload_request(access_token, file_path, material_type)
    with Path(file_path).open("rb") as handle:
        response = requests.post(
            request["url"],
            files={request["file_field"]: handle},
            timeout=120,
        )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode", 0) not in (0,):
        raise RuntimeError(f"WeChat material upload error: {data}")
    return data


def upload_inline_image(access_token, file_path):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for WeChat API calls") from exc

    request = build_inline_image_upload_request(access_token, file_path)
    with Path(file_path).open("rb") as handle:
        response = requests.post(
            request["url"],
            files={request["file_field"]: handle},
            timeout=120,
        )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode", 0) not in (0,):
        raise RuntimeError(f"WeChat inline image upload error: {data}")
    return data


def create_draft(access_token, payload):
    return post_json("draft/add", access_token, payload)


def submit_publish(access_token, media_id):
    return post_json("freepublish/submit", access_token, {"media_id": media_id})


def query_publish(access_token, publish_id):
    return post_json("freepublish/get", access_token, {"publish_id": publish_id})


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["upload-material", "upload-inline-image", "draft", "publish", "status"],
    )
    parser.add_argument("--access-token")
    parser.add_argument("--payload")
    parser.add_argument("--file")
    parser.add_argument("--material-type", default="thumb")
    parser.add_argument("--media-id")
    parser.add_argument("--publish-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out")
    return parser.parse_args(argv)


def resolve_access_token(args):
    load_dotenv()
    if args.access_token:
        return args.access_token
    if os.environ.get("WECHAT_ACCESS_TOKEN"):
        return os.environ["WECHAT_ACCESS_TOKEN"]
    app_id = os.environ.get("WECHAT_APP_ID")
    app_secret = os.environ.get("WECHAT_APP_SECRET")
    if app_id and app_secret:
        return get_access_token(app_id, app_secret)
    raise RuntimeError("provide --access-token or WECHAT_ACCESS_TOKEN/WECHAT_APP_ID/WECHAT_APP_SECRET")


def emit(data, out=None):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.action == "upload-material":
        if not args.file:
            raise RuntimeError("--file is required for upload-material")
        if args.dry_run:
            token = args.access_token or "ACCESS_TOKEN"
            emit(build_material_upload_request(token, args.file, args.material_type), args.out)
            return 0
        token = resolve_access_token(args)
        emit(upload_material(token, args.file, args.material_type), args.out)
        return 0

    if args.action == "upload-inline-image":
        if not args.file:
            raise RuntimeError("--file is required for upload-inline-image")
        if args.dry_run:
            token = args.access_token or "ACCESS_TOKEN"
            emit(build_inline_image_upload_request(token, args.file), args.out)
            return 0
        token = resolve_access_token(args)
        emit(upload_inline_image(token, args.file), args.out)
        return 0

    if args.action == "draft":
        if not args.payload:
            raise RuntimeError("--payload is required for draft")
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        if args.dry_run:
            emit({"action": "draft", "path": "draft/add", "payload": payload}, args.out)
            return 0
        token = resolve_access_token(args)
        emit(create_draft(token, payload), args.out)
        return 0

    if args.action == "publish":
        if not args.media_id:
            raise RuntimeError("--media-id is required for publish")
        if args.dry_run:
            emit({"action": "publish", "path": "freepublish/submit", "media_id": args.media_id}, args.out)
            return 0
        token = resolve_access_token(args)
        emit(submit_publish(token, args.media_id), args.out)
        return 0

    if not args.publish_id:
        raise RuntimeError("--publish-id is required for status")
    if args.dry_run:
        emit({"action": "status", "path": "freepublish/get", "publish_id": args.publish_id}, args.out)
        return 0
    token = resolve_access_token(args)
    emit(query_publish(token, args.publish_id), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
