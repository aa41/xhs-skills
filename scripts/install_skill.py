#!/usr/bin/env python3
"""Install this skill for Codex and/or Claude Code.

Existing target directories are preserved unless --force is passed.
"""

import argparse
import shutil
from pathlib import Path


DEFAULT_CODEX_DIR = Path.home() / ".agents" / "skills" / "xhs-wechat-publisher"
DEFAULT_CLAUDE_DIR = Path.home() / ".claude" / "skills" / "xhs-wechat-publisher"


def copy_skill(source, target, force=False):
    source = Path(source).resolve()
    target = Path(target).expanduser().resolve()
    if target.exists():
        if not force:
            raise FileExistsError(f"{target} already exists; pass --force to overwrite")
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "tests")
    shutil.copytree(source, target, ignore=ignore)
    return target


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["codex", "claude", "both"], default="both")
    parser.add_argument("--codex-dir", default=str(DEFAULT_CODEX_DIR))
    parser.add_argument("--claude-dir", default=str(DEFAULT_CLAUDE_DIR))
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    source = Path(__file__).resolve().parents[1]
    installed = []
    if args.target in {"codex", "both"}:
        installed.append(("codex", copy_skill(source, args.codex_dir, args.force)))
    if args.target in {"claude", "both"}:
        installed.append(("claude", copy_skill(source, args.claude_dir, args.force)))

    for name, path in installed:
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
