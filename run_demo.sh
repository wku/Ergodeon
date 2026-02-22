#!/bin/bash
set -e

# Change to the script directory
cd "$(dirname "$0")"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv could not be found. Please install it first."
    echo "Visit https://github.com/astral-sh/uv for installation instructions."
    echo "Or try: pip install uv"
    exit 1
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY is not set. The demo will ask for it."
fi

echo "🚀 Starting OpenRouter Agent Demo with uv..."

# Run the demo using uv
# --active matches behavior of virtualenv activation if needed, but 'uv run' handles it
# We install the project in editable mode implicitly or explicitly
# 'uv run' finds pyproject.toml and creates venv if needed
uv run python -m demo.cli
