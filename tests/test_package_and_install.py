import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    script = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_xhs_note_creates_manual_publish_bundle(tmp_path):
    mod = load_script("package_xhs_note.py")
    caption = tmp_path / "caption.md"
    caption.write_text("今天把发布链路的草稿状态补齐了。", encoding="utf-8")
    image = tmp_path / "cover.png"
    image.write_bytes(b"image")
    out = tmp_path / "bundle"

    metadata = mod.package_note(
        title="发布链路补完记录",
        caption=caption.read_text(encoding="utf-8"),
        tags=["开发日志", "小红书运营"],
        images=[str(image)],
        out_dir=out,
    )

    assert metadata["automation"] == "manual-confirmation"
    assert (out / "title.txt").read_text(encoding="utf-8").strip() == "发布链路补完记录"
    assert "#开发日志" in (out / "tags.txt").read_text(encoding="utf-8")
    assert (out / "images" / "01.png").read_bytes() == b"image"
    assert "人工确认" in (out / "publish-checklist.md").read_text(encoding="utf-8")


def test_install_skill_can_copy_to_codex_and_claude_targets(tmp_path):
    mod = load_script("install_skill.py")
    codex_target = tmp_path / "codex" / "xhs-wechat-publisher"
    claude_target = tmp_path / "claude" / "xhs-wechat-publisher"

    exit_code = mod.main(
        [
            "--target",
            "both",
            "--codex-dir",
            str(codex_target),
            "--claude-dir",
            str(claude_target),
        ]
    )

    assert exit_code == 0
    assert (codex_target / "SKILL.md").exists()
    assert (claude_target / "SKILL.md").exists()
    assert not (codex_target / "tests").exists()


def test_install_skill_refuses_to_overwrite_without_force(tmp_path):
    mod = load_script("install_skill.py")
    target = tmp_path / "codex" / "xhs-wechat-publisher"
    target.mkdir(parents=True)
    (target / "custom.txt").write_text("keep me", encoding="utf-8")

    try:
        mod.main(["--target", "codex", "--codex-dir", str(target)])
    except FileExistsError as exc:
        assert "--force" in str(exc)
    else:
        raise AssertionError("existing target should require --force")

    assert (target / "custom.txt").exists()
