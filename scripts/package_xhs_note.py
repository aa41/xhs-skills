#!/usr/bin/env python3
"""Create a manual-ready 小红书 publishing package."""

import argparse
import json
import shutil
import sys
from pathlib import Path


def parse_tags(raw_tags):
    tags = []
    for item in raw_tags:
        for tag in item.replace(",", " ").split():
            cleaned = tag.strip().lstrip("#")
            if cleaned:
                tags.append(cleaned)
    return tags


def package_note(title, caption, tags, images, out_dir):
    out_path = Path(out_dir)
    images_dir = out_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for index, image in enumerate(images, start=1):
        source = Path(image)
        suffix = source.suffix or ".png"
        target = images_dir / f"{index:02d}{suffix}"
        if source.exists():
            shutil.copy2(source, target)
        else:
            target.write_text(f"missing image placeholder: {source}\n", encoding="utf-8")
        copied.append(str(target.relative_to(out_path)))

    tag_text = "\n".join(f"#{tag}" for tag in tags)
    (out_path / "title.txt").write_text(title.strip() + "\n", encoding="utf-8")
    (out_path / "caption.md").write_text(caption.strip() + "\n", encoding="utf-8")
    (out_path / "tags.txt").write_text(tag_text + "\n", encoding="utf-8")
    (out_path / "publish-checklist.md").write_text(
        "\n".join(
            [
                "# 小红书发布清单",
                "",
                "- 登录小红书账号，确认当前账号身份。",
                "- 按 `images/` 编号顺序上传图片。",
                "- 粘贴 `title.txt`、`caption.md` 和 `tags.txt`。",
                "- 检查首图裁切、错别字、标签数量和敏感表述。",
                "- 人工确认后发布；不要依赖 Cookie 自动化直接点击发布。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    metadata = {
        "platform": "xhs",
        "title": title,
        "tags": tags,
        "images": copied,
        "automation": "manual-confirmation",
    }
    (out_path / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metadata


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--caption-file", required=True)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--out", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    caption = Path(args.caption_file).read_text(encoding="utf-8")
    metadata = package_note(
        title=args.title,
        caption=caption,
        tags=parse_tags(args.tag),
        images=args.image,
        out_dir=args.out,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
