"""Collect git diff and changed-file metadata for the most recent commit."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommitInfo:
    sha: str
    message: str
    diff: str
    changed_files: list[str]


def get_latest_commit_info(repo_path: str) -> CommitInfo:
    """Return diff + metadata for the HEAD commit in *repo_path*."""

    def _run(cmd: list[str]) -> str:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()

    sha = _run(["git", "rev-parse", "HEAD"])
    message = _run(["git", "log", "-1", "--pretty=%B"])
    diff = _run(["git", "diff", "HEAD~1", "HEAD"])
    changed_files_raw = _run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
    )
    changed_files = [f for f in changed_files_raw.splitlines() if f]

    # Fallback for the very first commit (no HEAD~1)
    if not diff:
        diff = _run(["git", "diff", "--cached", "HEAD"])
    if not diff:
        diff = _run(["git", "show", "--stat", "HEAD"])

    return CommitInfo(
        sha=sha,
        message=message,
        diff=diff,
        changed_files=changed_files,
    )
