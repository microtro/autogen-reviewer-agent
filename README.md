# 🤖 Reviewer Agent

A local **AutoGen-powered code reviewer** that automatically analyzes every
git commit in your repos — checking the diff, linting, and formatting.

## How it works

```
git commit → post-commit hook → reviewer agent
                                    ├─ collects git diff
                                    ├─ runs ruff lint
                                    ├─ runs ruff format --check
                                    └─ sends everything to an LLM
                                       via AutoGen for a structured review
```

## Quick start

### 1. Install dependencies

```bash
cd reviewer_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Install the git hook into your repos

```bash
# Single repo
python install_hooks.py /path/to/my/repo

# All repos under a directory
python install_hooks.py --scan ~/projects

# Remove hooks
python install_hooks.py --uninstall /path/to/my/repo
```

### 4. Commit and see the review

```bash
cd /path/to/my/repo
git add . && git commit -m "my changes"
# The reviewer agent runs automatically and prints its review
```

## Manual usage

You can also run the reviewer manually on any repo:

```bash
python -m reviewer /path/to/any/repo
```

## Configuration

All settings live in `.env` (copy from `.env.example`):

| Variable              | Default       | Description                        |
|-----------------------|---------------|------------------------------------|
| `OPENAI_API_KEY`      | —             | Your OpenAI API key                |
| `REVIEWER_MODEL`      | `gpt-4o-mini` | Model to use                       |
| `MAX_TOKENS`          | `4096`        | Max tokens for the review response |
| `SEVERITY_THRESHOLD`  | `info`        | Minimum severity to report         |
| `RUFF_BIN`            | `.venv/bin/ruff` | Path to ruff binary             |

## Project structure

```
reviewer_agent/
├── reviewer/
│   ├── __init__.py
│   ├── __main__.py        # python -m reviewer entry point
│   ├── agent.py           # AutoGen agent orchestration
│   ├── config.py          # Environment/config loading
│   ├── diff_collector.py  # Git diff extraction
│   └── lint_runner.py     # Ruff lint & format checks
├── hooks/
│   └── post-commit.template
├── install_hooks.py       # Hook installer/uninstaller
├── requirements.txt
├── pyproject.toml         # Ruff configuration
├── .env.example
└── README.md
```
