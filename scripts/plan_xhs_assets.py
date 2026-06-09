#!/usr/bin/env python3
"""Plan 1-5 小红书 image cards from a manuscript."""

import argparse
import json
import re
import sys
from pathlib import Path


ROLES = {
    "daily-dev-log": {
        "label": "每日开发日志",
        "tone": "真实开发记录，具体到接口、错误码、截图或决策。",
    },
    "weekly-dev-log": {
        "label": "每周开发日志",
        "tone": "阶段性复盘，有进展、有取舍、有遗留问题。",
    },
    "release-note": {
        "label": "版本更新",
        "tone": "清楚克制，先讲用户能感知到的变化。",
    },
    "daily-ops": {
        "label": "日常运营",
        "tone": "运营复盘，讲动作、反馈和下一步。",
    },
    "product-diary": {
        "label": "产品日记",
        "tone": "围绕用户场景和产品取舍。",
    },
}


STYLE_PRESETS = {
    "notion-lab": {
        "name": "notion-lab",
        "description": "Notion 风格知识卡 + 产品实验室质感，白底、网格、模块化信息块",
        "material": "磨砂玻璃小组件、轻微纸张颗粒、柔和微阴影、细线图标",
    },
    "study-notes": {
        "name": "study-notes",
        "description": "小红书学习笔记风格，高亮笔、便签、步骤编号、重点圈注",
        "material": "纸张肌理、荧光标注、胶带贴纸、手写箭头",
    },
    "sketch-notes": {
        "name": "sketch-notes",
        "description": "开发者草图笔记风格，线框图、流程箭头、代码片段、真实日志",
        "material": "细线草图、终端窗口、局部涂鸦、手写感注释",
    },
}


LAYOUT_PRESETS = {
    "hero-dashboard": {
        "name": "hero-dashboard",
        "description": "上方大标题，中部真实界面/设备渲染，下方三枚状态指标",
        "density": "中高信息密度，首屏 3 秒内能读懂主题",
    },
    "flow-map": {
        "name": "flow-map",
        "description": "电脑 -> HTTP 地址 -> 手机的流程地图，节点有小状态灯",
        "density": "中等信息密度，重点突出路径和动作",
    },
    "checklist-debug": {
        "name": "checklist-debug",
        "description": "检查清单 + 请求日志 + 局部标注，适合排查过程",
        "density": "高信息密度，但分区清晰，不要挤满",
    },
}


PALETTES = {
    "macaron-tech": {
        "name": "macaron-tech",
        "description": "奶油白、雾蓝、薄荷绿、少量珊瑚橙，科技但不冷",
    },
    "warm-paper": {
        "name": "warm-paper",
        "description": "暖白纸张、浅杏、墨黑、荧光黄标注，笔记感更强",
    },
    "clean-neon": {
        "name": "clean-neon",
        "description": "白底、深墨蓝、亮蓝、荧光绿状态点，适合日志和链路检查",
    },
}


def split_points(text):
    points = []
    for line in text.splitlines():
        cleaned = line.strip(" -•\t")
        if not cleaned:
            continue
        parts = re.split(
            r"(?<=[。！？!?；;：:])|(?=新增|修复|注意|幕后|结果|问题|调整|数据|下一步)",
            cleaned,
        )
        for part in parts:
            point = part.strip(" -•\t；;。 ")
            if point:
                points.append(point)
    if not points:
        points = [text.strip()]
    return merge_heading_points(points)


def merge_heading_points(points):
    merged = []
    pending = ""
    for point in points:
        if re.fullmatch(r"[\u4e00-\u9fa5A-Za-z0-9 ._-]{2,12}[：:]", point):
            pending = f"{pending}{point}"
            continue
        if pending:
            merged.append(f"{pending}{point}")
            pending = ""
        else:
            merged.append(point)
    if pending:
        merged.append(pending)
    return merged


def strip_sentence_end(text):
    return text.rstrip("。！？!?；;，,、 ")


def extract_action_title(point):
    if "两个高频动作" in point and "链路" in point:
        return "两个高频动作，一条链路"
    match = re.search(r"(传书[、和与/ ]+复制剪贴板|复制剪贴板[、和与/ ]+传书)", point)
    if match:
        return "传书 + 复制剪贴板"
    match = re.search(r"(HTTP|局域网|Wi-?Fi).{0,8}(传书|剪贴板|连接)", point, re.IGNORECASE)
    if match:
        return strip_sentence_end(match.group(0))
    return ""


def trim_title(point, limit):
    action_title = extract_action_title(point)
    if action_title:
        return action_title
    return strip_sentence_end(point[:limit])


def estimate_count(text, role):
    points = split_points(text)
    punctuation_parts = len(re.findall(r"[。！？!?；;：:]", text))
    length_score = len(text) // 90
    signal_words = len(re.findall(r"新增|修复|调整|注意|数据|复盘|步骤|问题|结果|迁移|上线", text))

    score = max(len(points), punctuation_parts, length_score + signal_words)
    if role in {"release-note", "weekly-dev-log"}:
        score += 1

    if score <= 2:
        return 1
    if score <= 3:
        return 2
    if score <= 5:
        return 3
    if score <= 8:
        return 4
    return 5


def make_card(index, count, role, point):
    clean_point = strip_sentence_end(point)
    if index == 0:
        card_type = "cover"
        title = trim_title(clean_point, 32)
    elif index == count - 1 and count > 2:
        card_type = "summary"
        title = extract_action_title(clean_point) or "这次留下的判断"
    else:
        card_type = "detail"
        title = trim_title(clean_point, 28)

    style_preset = select_style(role, card_type, clean_point)
    layout_preset = select_layout(card_type, clean_point)
    palette = select_palette(card_type, clean_point)
    render_effect = render_brief(card_type, style_preset, layout_preset, palette)

    prompt = build_render_prompt(
        index=index,
        count=count,
        role=role,
        title=title,
        clean_point=clean_point,
        card_type=card_type,
        style_preset=style_preset,
        layout_preset=layout_preset,
        palette=palette,
        render_effect=render_effect,
    )

    return {
        "index": index + 1,
        "type": card_type,
        "title": title,
        "source_point": clean_point,
        "aspect": "portrait",
        "api_size": "1024x1536",
        "style_preset": style_preset,
        "layout_preset": layout_preset,
        "palette": palette,
        "render_effect": render_effect,
        "render_prompt": prompt,
    }


def select_style(role, card_type, point):
    if card_type == "cover":
        return STYLE_PRESETS["notion-lab"]
    if re.search(r"日志|请求|端口|HTTP|连接|失败|状态", point, re.IGNORECASE):
        return STYLE_PRESETS["sketch-notes"]
    if role in {"daily-dev-log", "weekly-dev-log"}:
        return STYLE_PRESETS["study-notes"]
    return STYLE_PRESETS["notion-lab"]


def select_layout(card_type, point):
    if card_type == "cover":
        return LAYOUT_PRESETS["hero-dashboard"]
    if re.search(r"连接|链路|HTTP|传书|剪贴板|流程|地址", point, re.IGNORECASE):
        return LAYOUT_PRESETS["flow-map"]
    return LAYOUT_PRESETS["checklist-debug"]


def select_palette(card_type, point):
    if re.search(r"日志|HTTP|请求|连接|状态", point, re.IGNORECASE):
        return PALETTES["clean-neon"]
    if card_type == "summary":
        return PALETTES["warm-paper"]
    return PALETTES["macaron-tech"]


def render_brief(card_type, style_preset, layout_preset, palette):
    return (
        f"{style_preset['description']}；{layout_preset['description']}；"
        f"调色={palette['description']}；材质={style_preset['material']}；"
        "层次清楚，微阴影，局部标注，真实界面与日志细节。"
    )


def build_render_prompt(
    index,
    count,
    role,
    title,
    clean_point,
    card_type,
    style_preset,
    layout_preset,
    palette,
    render_effect,
):
    return "\n".join(
        [
            "小红书竖版图文卡片，1024x1536，高完成度商业插画 + 真实产品界面混合风格。",
            f"角色：{ROLES[role]['label']}；卡片：{index + 1}/{count}；类型：{card_type}。",
            f"主标题：{title}",
            f"内容线索：{clean_point}",
            f"风格预设：{style_preset['name']} - {style_preset['description']}",
            f"版式预设：{layout_preset['name']} - {layout_preset['description']}",
            f"信息密度：{layout_preset['density']}。",
            f"调色板：{palette['name']} - {palette['description']}。",
            f"材质与质感：{style_preset['material']}；真实界面截图感、细腻微阴影、轻颗粒、边缘高光。",
            f"画面层次：标题层 / 主视觉层 / 数据或日志层 / 局部标注层 / 留白呼吸区。",
            "必须包含：局部标注、状态点、真实界面或日志块、至少一个和内容相关的小细节。",
            f"渲染重点：{render_effect}",
            "禁止：不要官方logo，不要伪造小红书品牌标识，不要空泛渐变背景，不要企业PPT感，不要大段乱码文字，不要过度简单图标堆砌。",
            "中文排版要稳，主标题清晰可读，细节文字可以少量但要像真实产品记录。",
        ]
    )


def plan_assets(text, role="daily-dev-log"):
    if role not in ROLES:
        raise ValueError(f"unknown role: {role}")

    points = split_points(text)
    count = estimate_count(text, role)
    while len(points) < count:
        points.append(points[-1])

    cards = [make_card(index, count, role, points[index]) for index in range(count)]
    return {
        "role": ROLES[role],
        "card_count": count,
        "cards": cards,
    }


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--text")
    parser.add_argument("--file")
    parser.add_argument("--role", default="daily-dev-log", choices=sorted(ROLES))
    parser.add_argument("--out")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    result = plan_assets(text, args.role)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
