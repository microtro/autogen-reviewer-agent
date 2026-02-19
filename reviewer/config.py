"""Configuration for the reviewer agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# LLM provider: "azure" (Azure AI Foundry), "github" (GitHub Models), or "openai"
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "azure")

# For provider="github": your GitHub PAT (with Copilot access)
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

# For provider="openai": your OpenAI API key
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# For provider="azure": Azure AI Foundry / Azure OpenAI settings
AZURE_ENDPOINT: str = os.getenv("AZURE_ENDPOINT", "")
AZURE_API_KEY: str = os.getenv("AZURE_API_KEY", "")
AZURE_API_VERSION: str = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
# "key" = use AZURE_API_KEY, "cli" = use Azure CLI / DefaultAzureCredential
AZURE_AUTH_METHOD: str = os.getenv("AZURE_AUTH_METHOD", "cli")

REVIEWER_MODEL: str = os.getenv("REVIEWER_MODEL", "gpt-5")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
SEVERITY_THRESHOLD: str = os.getenv("SEVERITY_THRESHOLD", "info")

# GitHub Models endpoint (OpenAI-compatible)
GITHUB_MODELS_BASE_URL: str = os.getenv(
    "GITHUB_MODELS_BASE_URL",
    "https://models.inference.ai.azure.com",
)

# Absolute path to the ruff binary shipped inside the venv
RUFF_BIN: str = os.getenv(
    "RUFF_BIN",
    str(_PROJECT_ROOT / ".venv" / "bin" / "ruff"),
)
