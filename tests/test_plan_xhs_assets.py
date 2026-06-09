import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plan_xhs_assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("plan_xhs_assets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_short_daily_copy_generates_one_or_two_cards():
    mod = load_module()
    text = "今天把登录失败的重试逻辑补好了，顺手修了两个空状态文案。"

    plan = mod.plan_assets(text, role="daily-dev-log")

    assert 1 <= len(plan["cards"]) <= 2
    assert plan["role"]["label"] == "每日开发日志"
    assert "小红书" in plan["cards"][0]["render_prompt"]
    assert "。。" not in plan["cards"][0]["render_prompt"]


def test_xhs_card_prompts_include_rich_visual_direction():
    mod = load_module()
    text = "今天把 HTTP 局域网连接跑通了，支持传书和复制剪贴板。调试时补了连接状态、请求日志和失败提示。"

    plan = mod.plan_assets(text, role="daily-dev-log")
    card = plan["cards"][0]
    prompt = card["render_prompt"]

    assert card["style_preset"]["name"] in {"notion-lab", "study-notes", "sketch-notes"}
    assert card["layout_preset"]["name"] in {"hero-dashboard", "flow-map", "checklist-debug"}
    assert card["palette"]["name"] in {"macaron-tech", "warm-paper", "clean-neon"}
    for keyword in [
        "信息密度",
        "材质",
        "层次",
        "微阴影",
        "真实界面",
        "局部标注",
        "禁止",
        "不要官方logo",
    ]:
        assert keyword in prompt


def test_daily_http_update_uses_action_based_titles():
    mod = load_module()
    text = "\n\n".join(
        [
            "今天把局域网里的 HTTP 连接跑顺了。",
            "这次不是做一个“看起来很完整”的大功能，主要是把两个高频动作放到同一条链路里：传书、复制剪贴板。",
            "之前调试的时候最别扭的是，手机和电脑明明在同一个 Wi-Fi 下，还要绕一圈。",
        ]
    )

    plan = mod.plan_assets(text, role="daily-dev-log")
    titles = [card["title"] for card in plan["cards"]]

    assert any("传书" in title and "剪贴板" in title for title in titles)
    assert all(not title.endswith("高频") for title in titles)


def test_complex_release_copy_caps_at_five_cards():
    mod = load_module()
    text = "\n".join(
        [
            "版本更新：1.8.0",
            "新增：批量导入、失败重试、草稿预览、图片压缩、评论开关。",
            "修复：移动端换行、封面上传、token刷新、发布状态轮询。",
            "注意：旧版本配置字段废弃，需要迁移。",
            "幕后：这次主要把发布链路从人工拼接改成了可复用模块。",
        ]
    )

    plan = mod.plan_assets(text, role="release-note")

    assert len(plan["cards"]) == 5
    assert plan["cards"][0]["type"] == "cover"
    assert any(card["type"] == "detail" for card in plan["cards"])
    assert all("render_effect" in card for card in plan["cards"])
    assert len({card["source_point"] for card in plan["cards"]}) == 5


def test_unknown_role_is_rejected():
    mod = load_module()

    try:
        mod.plan_assets("hello", role="unknown")
    except ValueError as exc:
        assert "unknown role" in str(exc)
    else:
        raise AssertionError("unknown role should fail")


def test_one_paragraph_release_note_is_split_into_distinct_card_beats():
    mod = load_module()
    text = "版本更新：新增批量导入、失败重试和草稿预览；修复移动端换行、封面上传和 token 刷新；注意旧版本配置字段废弃，需要迁移；幕后这次把发布链路从人工拼接改成可复用模块。"

    plan = mod.plan_assets(text, role="release-note")

    assert len(plan["cards"]) >= 4
    assert len({card["source_point"] for card in plan["cards"]}) == len(plan["cards"])
    assert plan["cards"][0]["type"] == "cover"
    assert plan["cards"][0]["source_point"] != "版本更新："
    assert "新增批量导入" in plan["cards"][0]["source_point"]
    assert plan["cards"][-1]["type"] == "summary"
