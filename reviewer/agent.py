"""AutoGen-based code reviewer agent.

Orchestrates an AssistantAgent that receives the git diff plus
linting/formatting output and produces a structured review.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .config import (
    GITHUB_MODELS_BASE_URL,
    GITHUB_TOKEN,
    LLM_PROVIDER,
    MAX_TOKENS,
    OPENAI_API_KEY,
    REVIEWER_MODEL,
)
from .diff_collector import CommitInfo, get_latest_commit_info
from .lint_runner import run_ruff_check, run_ruff_format_check

SYSTEM_PROMPT = """\
You are an expert code reviewer.  You receive:

1. A **git diff** of the latest commit.
2. **Linting results** from ruff.
3. **Formatting results** from ruff format --check.

Your job is to produce a concise, actionable review covering:

- **Summary** - one-paragraph overview of the change.
- **Issues** - a numbered list of problems (bugs, security, logic errors)
  with severity (error / warning / info) and the relevant file + line.
- **Lint & Format** - highlight the most important lint/format violations
  and suggest fixes.
- **Suggestions** - optional improvements (readability, performance, naming).
- **Verdict** - one of: LGTM, Needs Minor Fixes, or Needs Major Rework.

Keep the review concise. Do NOT repeat the diff verbatim.
"""

# GitHub Models has a 16K token input limit.  1 token ~ 4 chars.
# Reserve room for system prompt (~300 tokens) + response (MAX_TOKENS).
_INPUT_CHAR_BUDGET = (16_000 - 500 - MAX_TOKENS) * 4  # ~46 000 chars


def _truncate(text: str, budget: int) -> str:
    """Truncate *text* to *budget* chars, appending a notice if cut."""
    if len(text) <= budget:
        return text
    return text[:budget] + "\n\n... [truncated to fit token limit]"


def _build_review_message(commit: CommitInfo, lint: str, fmt: str) -> str:
    # Allocate char budget: 70 % diff, 15 % lint, 15 % format
    diff_budget = int(_INPUT_CHAR_BUDGET * 0.70)
    lint_budget = int(_INPUT_CHAR_BUDGET * 0.15)
    fmt_budget = int(_INPUT_CHAR_BUDGET * 0.15)

    return f"""\
## Commit `{commit.sha[:10]}` — {commit.message}

### Changed files
{chr(10).join("- " + f for f in commit.changed_files)}

### Git diff
```diff
{_truncate(commit.diff, diff_budget)}
```

### Ruff lint output
```
{_truncate(lint, lint_budget)}
```

### Ruff format check
```
{_truncate(fmt, fmt_budget)}
```

Please review this commit.
"""


def _build_model_client() -> OpenAIChatCompletionClient:
    """Create the model client based on LLM_PROVIDER."""
    if LLM_PROVIDER == "github":
        if not GITHUB_TOKEN:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. "
                "Add a GitHub PAT to .env (needs Copilot access)."
            )
        return OpenAIChatCompletionClient(
            model=REVIEWER_MODEL,
            api_key=GITHUB_TOKEN,
            base_url=GITHUB_MODELS_BASE_URL,
            max_tokens=MAX_TOKENS,
        )

    # Default: OpenAI
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-..."):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return OpenAIChatCompletionClient(
        model=REVIEWER_MODEL,
        api_key=OPENAI_API_KEY,
        max_tokens=MAX_TOKENS,
    )


async def run_review(repo_path: str) -> str:
    """Run the full review pipeline and return the review text."""
    try:
        model_client = _build_model_client()
    except RuntimeError as exc:
        return f"ERROR: {exc}"

    # 1. Gather data
    commit = get_latest_commit_info(repo_path)
    lint_output = run_ruff_check(repo_path, commit.changed_files)
    fmt_output = run_ruff_format_check(repo_path, commit.changed_files)

    # 3. Create the reviewer agent
    reviewer = AssistantAgent(
        name="CodeReviewer",
        model_client=model_client,
        system_message=SYSTEM_PROMPT,
    )

    # 4. Run inside a single-turn RoundRobin team (agent → stop)
    termination = MaxMessageTermination(max_messages=2)
    team = RoundRobinGroupChat(
        participants=[reviewer],
        termination_condition=termination,
    )

    user_message = _build_review_message(commit, lint_output, fmt_output)
    result = await team.run(task=user_message)

    # Extract the reviewer's last message
    review_text = ""
    for msg in reversed(result.messages):
        if msg.source == "CodeReviewer":
            review_text = msg.content
            break

    await model_client.close()
    return review_text or "No review generated."


def main() -> None:
    """CLI entry-point: ``python -m reviewer.agent <repo_path>``."""
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    repo_path = str(Path(repo_path).resolve())
    print(f"🔍 Reviewing latest commit in {repo_path} …\n")
    review = asyncio.run(run_review(repo_path))
    print(review)


if __name__ == "__main__":
    main()
