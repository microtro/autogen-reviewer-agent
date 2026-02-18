#!/usr/bin/env python3
"""Install (or uninstall) the reviewer post-commit hook into one or more repos.

Usage
-----
    # Install into a single repo:
    python install_hooks.py /path/to/my/repo

    # Install into several repos:
    python install_hooks.py /path/to/repo1 /path/to/repo2

    # Install into every repo under a directory:
    python install_hooks.py --scan ~/projects

    # Uninstall:
    python install_hooks.py --uninstall /path/to/my/repo
"""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path

HOOK_NAME = "post-commit"
MARKER = "# REVIEWER_AGENT_HOOK"

PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATE = PROJECT_ROOT / "hooks" / "post-commit.template"
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"


def find_repos(scan_dir: Path) -> list[Path]:
    """Discover git repos one level deep under *scan_dir*."""
    repos: list[Path] = []
    for child in sorted(scan_dir.iterdir()):
        if child.is_dir() and (child / ".git").exists():
            repos.append(child)
    return repos


def install_hook(repo: Path) -> None:
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / HOOK_NAME

    # Don't clobber an existing non-reviewer hook
    if hook_path.exists():
        content = hook_path.read_text()
        if MARKER in content:
            print(f"  ↻ Hook already installed in {repo}")
            return
        # Append to the existing hook
        print(f"  ⊕ Appending reviewer hook to existing {HOOK_NAME} in {repo}")
        with hook_path.open("a") as fh:
            fh.write("\n" + _rendered_hook() + "\n")
    else:
        print(f"  ✓ Installing {HOOK_NAME} hook in {repo}")
        hook_path.write_text("#!/usr/bin/env bash\n" + MARKER + "\n" + _rendered_hook() + "\n")

    # Make executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def uninstall_hook(repo: Path) -> None:
    hook_path = repo / ".git" / "hooks" / HOOK_NAME
    if not hook_path.exists():
        print(f"  - No {HOOK_NAME} hook in {repo}")
        return
    content = hook_path.read_text()
    if MARKER not in content:
        print(f"  - Hook in {repo} was not installed by reviewer_agent, skipping")
        return
    hook_path.unlink()
    print(f"  ✗ Removed {HOOK_NAME} hook from {repo}")


def _rendered_hook() -> str:
    template = TEMPLATE.read_text()
    return (
        template
        .replace("{{REVIEWER_AGENT_DIR}}", str(PROJECT_ROOT))
        .replace("{{PYTHON}}", str(PYTHON_BIN))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Install reviewer agent git hooks.")
    parser.add_argument("repos", nargs="*", help="Paths to git repositories")
    parser.add_argument("--scan", type=Path, help="Scan a directory for git repos")
    parser.add_argument("--uninstall", action="store_true", help="Remove the hooks")
    args = parser.parse_args()

    repos: list[Path] = []
    if args.scan:
        repos.extend(find_repos(args.scan))
    for r in args.repos:
        repos.append(Path(r).resolve())

    if not repos:
        print("No repos specified. Use --scan <dir> or pass repo paths.", file=sys.stderr)
        sys.exit(1)

    action = uninstall_hook if args.uninstall else install_hook
    for repo in repos:
        if not (repo / ".git").exists():
            print(f"  ⚠ Skipping {repo} (not a git repo)")
            continue
        action(repo)

    print("\nDone.")


if __name__ == "__main__":
    main()
