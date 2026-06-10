from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_skill_manifest_and_required_topics_exist():
    skill = read("SKILL.md")

    assert "name: xhs-wechat-publisher" in skill
    assert "description:" in skill
    assert "gpt-image-2" in skill
    assert "小红书" in skill
    assert "微信公众号" in skill
    assert "access_token" in skill
    assert "多agent" in skill or "multi-agent" in skill
    assert "反AI味" in skill or "AI味" in skill


def test_required_references_and_scripts_are_present():
    required = [
        "agents/openai.yaml",
        "references/research.md",
        "references/roles.md",
        "references/style-guide.md",
        "references/gui-automation.md",
        "references/publishing.md",
        "scripts/generate_gpt_image2.py",
        "scripts/plan_xhs_assets.py",
        "scripts/review_content.py",
        "scripts/publish_wechat.py",
        "scripts/package_xhs_note.py",
        "scripts/install_skill.py",
    ]

    for path in required:
        assert (ROOT / path).exists(), path


def test_research_records_current_publishing_findings():
    research = read("references/research.md")

    assert "2026-06-09" in research
    assert "gpt-image-2" in research
    assert "1024x1024" in research
    assert "1536x1024" in research
    assert "1024x1536" in research
    assert "微信" in research and "draft/add" in research
    assert "freepublish/submit" in research
    assert "media/uploadimg" in research
    assert "2025" in research and "个人账号" in research
    assert "小红书" in research
    assert "没有找到" in research or "未找到" in research
    assert "官方" in research


def test_skill_forbids_unstable_xhs_autopublish_claims():
    publishing = read("references/publishing.md")

    assert "不承诺" in publishing or "不要承诺" in publishing
    assert "Cookie" in publishing
    assert "人工确认" in publishing
    assert "access_key" in publishing


def test_gui_automation_boundaries_are_explicit():
    skill = read("SKILL.md")
    gui = read("references/gui-automation.md")

    assert "browser-use" in skill
    assert "references/gui-automation.md" in skill
    for keyword in ["Chrome", "Browser", "Computer Use", "人工确认", "最终发布", "不读取"]:
        assert keyword in gui
    assert "停在发布前" in gui
