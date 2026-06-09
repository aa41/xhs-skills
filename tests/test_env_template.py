from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_image_env_template_documents_all_generator_variables():
    template = (ROOT / ".env.example").read_text(encoding="utf-8")

    required = [
        "OPENAI_API_KEY=",
        "OPENAI_BASE_URL=",
        "OPENAI_IMAGE_MODEL=",
        "OPENAI_IMAGE_QUALITY=",
        "OPENAI_IMAGE_BACKGROUND=",
        "OPENAI_IMAGE_TIMEOUT=",
        "OPENAI_IMAGE_RETRIES=",
        "OPENAI_EXTRA_HEADERS=",
    ]
    for key in required:
        assert key in template

    assert "sk-" not in template
    assert "真实 key" in template


def test_gitignore_excludes_real_env_file():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in gitignore
    assert "!.env.example" in gitignore
