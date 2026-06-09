#!/usr/bin/env python3
"""Generate GPT Image 2 assets for XHS/WeChat publishing workflows."""

import argparse
import base64
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API_SIZES = {
    "square": "1024x1024",
    "portrait": "1024x1536",
    "landscape": "1536x1024",
}

RESOLUTION_SCALE = {
    "1k": 1,
    "2k": 2,
    "4k": 4,
}


class ImageSettings:
    def __init__(
        self,
        prompt,
        model,
        endpoint,
        api_key,
        api_size,
        target_size,
        quality,
        output_format,
        background,
        timeout,
        retries,
        extra_headers,
    ):
        self.prompt = prompt
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_size = api_size
        self.target_size = target_size
        self.quality = quality
        self.output_format = output_format
        self.background = background
        self.timeout = timeout
        self.retries = retries
        self.extra_headers = extra_headers


def load_dotenv(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_size(size):
    width, height = size.split("x", 1)
    return int(width), int(height)


def normalize_base_url(base_url):
    if not base_url:
        return "https://api.openai.com/v1"
    return base_url.rstrip("/")


def resolve_settings(
    prompt,
    aspect="portrait",
    resolution="1k",
    output_format="png",
    quality=None,
    background=None,
    timeout=None,
    retries=None,
):
    load_dotenv()

    if aspect not in API_SIZES:
        raise ValueError(f"unsupported aspect: {aspect}")
    if resolution not in RESOLUTION_SCALE:
        raise ValueError(f"unsupported resolution: {resolution}")

    model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
    base_url = normalize_base_url(os.environ.get("OPENAI_BASE_URL"))
    api_size = API_SIZES[aspect]
    width, height = parse_size(api_size)
    scale = RESOLUTION_SCALE[resolution]

    headers_json = os.environ.get("OPENAI_EXTRA_HEADERS", "{}")
    try:
        extra_headers = json.loads(headers_json)
    except json.JSONDecodeError as exc:
        raise ValueError("OPENAI_EXTRA_HEADERS must be valid JSON") from exc

    return ImageSettings(
        prompt=prompt,
        model=model,
        endpoint=f"{base_url}/images/generations",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        api_size=api_size,
        target_size=(width * scale, height * scale),
        quality=quality or os.environ.get("OPENAI_IMAGE_QUALITY", "high"),
        output_format=output_format,
        background=background or os.environ.get("OPENAI_IMAGE_BACKGROUND", "opaque"),
        timeout=int(timeout if timeout is not None else os.environ.get("OPENAI_IMAGE_TIMEOUT", "120")),
        retries=int(retries if retries is not None else os.environ.get("OPENAI_IMAGE_RETRIES", "2")),
        extra_headers=extra_headers,
    )


def build_payload(settings):
    payload = {
        "model": settings.model,
        "prompt": settings.prompt,
        "n": 1,
        "size": settings.api_size,
        "quality": settings.quality,
        "output_format": settings.output_format,
        "background": settings.background,
    }
    return {key: value for key, value in payload.items() if value is not None}


def post_json_stdlib(url, headers, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            try:
                text = response.read().decode("utf-8")
            except http.client.IncompleteRead as exc:
                text = exc.partial.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code}: {text[:500]}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid or incomplete JSON response: {text[:500]}") from exc


def get_bytes_stdlib(url, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code}: {text[:500]}") from exc


def request_image(settings):
    try:
        import requests
    except ImportError:
        requests = None

    if not settings.api_key:
        raise RuntimeError("OPENAI_API_KEY is required unless --dry-run is used")

    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    headers.update(settings.extra_headers)
    payload = build_payload(settings)

    last_error = None
    for attempt in range(settings.retries + 1):
        try:
            if requests is not None:
                response = requests.post(
                    settings.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=settings.timeout,
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"{response.status_code}: {response.text[:500]}")
                return response.json()
            return post_json_stdlib(settings.endpoint, headers, payload, settings.timeout)
        except Exception as exc:
            last_error = exc
            if attempt < settings.retries:
                time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"image request failed: {last_error}")


def extract_image_bytes(response_json):
    data = response_json.get("data") or []
    if not data:
        raise RuntimeError("image response did not include data")

    first = data[0]
    if "b64_json" in first:
        return base64.b64decode(first["b64_json"])
    if "url" in first:
        try:
            import requests
        except ImportError:
            requests = None
        if requests is None:
            return get_bytes_stdlib(first["url"], timeout=120)
        image_response = requests.get(first["url"], timeout=120)
        image_response.raise_for_status()
        return image_response.content

    raise RuntimeError("image response did not include b64_json or url")


def maybe_upscale(image_path, target_size):
    try:
        from PIL import Image
    except ImportError:
        return False

    with Image.open(image_path) as image:
        if image.size == target_size:
            return False
        resized = image.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(image_path)
    return True


def write_dry_run(settings, dry_run_output):
    data = {
        "endpoint": settings.endpoint,
        "target_size": settings.target_size,
        "timeout": settings.timeout,
        "retries": settings.retries,
        "payload": build_payload(settings),
    }
    output = Path(dry_run_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_prompt(args):
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise ValueError("provide --prompt or --prompt-file")


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--aspect", choices=sorted(API_SIZES), default="portrait")
    parser.add_argument("--resolution", choices=sorted(RESOLUTION_SCALE), default="1k")
    parser.add_argument("--format", dest="output_format", default="png")
    parser.add_argument("--quality", default=None)
    parser.add_argument("--background", default=None)
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--retries", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dry-run-output", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    prompt = read_prompt(args)
    settings = resolve_settings(
        prompt=prompt,
        aspect=args.aspect,
        resolution=args.resolution,
        output_format=args.output_format,
        quality=args.quality,
        background=args.background,
        timeout=args.timeout,
        retries=args.retries,
    )

    if args.dry_run:
        dry_run_output = args.dry_run_output or f"{args.out}.request.json"
        write_dry_run(settings, dry_run_output)
        print(f"dry-run request written to {dry_run_output}")
        return 0

    response_json = request_image(settings)
    image_bytes = extract_image_bytes(response_json)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    upscaled = maybe_upscale(out_path, settings.target_size)
    suffix = " and upscaled" if upscaled else ""
    print(f"image written to {out_path}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
