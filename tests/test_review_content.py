import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_content.py"


def load_module():
    spec = importlib.util.spec_from_file_location("review_content", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detects_ai_tone_and_translation_smell():
    mod = load_module()
    text = "在这个快节奏的时代，我们将为你赋能。以下是本次版本更新的完整总结。"

    result = mod.review_text(text, role="release-note")

    assert not result["passed"]
    assert any(issue["category"] == "ai_tone" for issue in result["issues"])
    assert any(issue["category"] == "translation_smell" for issue in result["issues"])


def test_detects_spaced_ai_phrase_and_report_like_translation_smell():
    mod = load_module()
    text = "作为一个 AI，我很高兴地宣布，本周我们交付了一个完整的解决方案。"

    result = mod.review_text(text, role="weekly-dev-log")

    assert not result["passed"]
    assert any(issue["category"] == "ai_tone" for issue in result["issues"])
    assert any(issue["category"] == "translation_smell" for issue in result["issues"])


def test_daily_dev_log_requires_concrete_work_detail():
    mod = load_module()
    text = "今天继续优化系统体验，整体效果更好了。"

    result = mod.review_text(text, role="daily-dev-log")

    assert not result["passed"]
    assert any(issue["category"] == "role_fit" for issue in result["issues"])


def test_specific_human_copy_passes():
    mod = load_module()
    text = "今天把封面上传的超时从 30 秒调到 90 秒，又补了失败重试。晚上回看日志，401 基本都收敛到 IP 白名单问题。"

    result = mod.review_text(text, role="daily-dev-log")

    assert result["passed"]
    assert result["issues"] == []


def test_broad_weekly_log_without_evidence_fails_role_fit():
    mod = load_module()
    text = "本周我们持续优化产品体验，提升整体效率，后续会继续复盘。"

    result = mod.review_text(text, role="weekly-dev-log")

    assert not result["passed"]
    assert any(issue["category"] == "role_fit" for issue in result["issues"])


def test_unknown_role_is_rejected():
    mod = load_module()

    try:
        mod.review_text("今天修了一个 401。", role="unknown")
    except ValueError as exc:
        assert "unknown role" in str(exc)
    else:
        raise AssertionError("unknown role should fail")


def test_multi_agent_review_has_three_named_passes_and_blocks_xhs_overclaim():
    mod = load_module()
    text = "我们支持通过小红书 access_key 稳定一键发布笔记，全自动无需人工确认。"

    result = mod.multi_agent_review(text, role="daily-ops", platform="xhs")

    assert not result["passed"]
    assert [review["agent"] for review in result["reviews"]] == [
        "role_editor",
        "platform_editor",
        "publishing_risk_editor",
    ]
    risk_issues = result["reviews"][2]["issues"]
    assert any(issue["category"] == "publishing_risk" for issue in risk_issues)
