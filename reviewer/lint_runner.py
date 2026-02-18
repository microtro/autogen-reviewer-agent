"""Run ruff linting and formatting checks on changed files."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config import RUFF_BIN


def run_ruff_check(repo_path: str, files: list[str]) -> str:
    """Run ``ruff check`` on the given *files* inside *repo_path*.

    Returns the combined stdout/stderr output.
    """
    target_files = _filter_python_files(repo_path, files)
    if not target_files:
        return "No Python files changed — linting skipped."

    return _invoke_ruff(["check", "--output-format=concise"], repo_path, target_files)


def run_ruff_format_check(repo_path: str, files: list[str]) -> str:
    """Run ``ruff format --check`` and report formatting drift."""
    target_files = _filter_python_files(repo_path, files)
    if not target_files:
        return "No Python files changed — format check skipped."

    return _invoke_ruff(["format", "--check", "--diff"], repo_path, target_files)


# ── helpers ──────────────────────────────────────────────────────────────────


def _filter_python_files(repo_path: str, files: list[str]) -> list[str]:
    """Keep only existing *.py files."""
    root = Path(repo_path)
    return [
        f
        for f in files
        if f.endswith(".py") and (root / f).exists()
    ]


def _invoke_ruff(extra_args: list[str], repo_path: str, files: list[str]) -> str:
    try:
        result = subprocess.run(
            [RUFF_BIN, *extra_args, *files],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return output if output else "All checks passed ✓"
    except FileNotFoundError:
        return f"ruff not found at {RUFF_BIN}. Install it or set RUFF_BIN in .env."
    except subprocess.TimeoutExpired:
        return "ruff timed out after 60 s."
