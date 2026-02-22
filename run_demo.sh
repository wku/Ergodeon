#!/bin/bash
set -e

cd "$(dirname "$0")"

if ! command -v uv &> /dev/null; then
    echo "uv could not be found. Please install it first."
    echo "Visit https://github.com/astral-sh/uv for installation instructions."
    echo "Or try: pip install uv"
    exit 1
fi

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY is not set. The demo will ask for it."
fi

echo "🚀 Starting Ergodeon Agent..."

# Передаём все аргументы напрямую в cli.py
# Примеры:
#   ./run_demo.sh                                      # обычный запуск
#   ./run_demo.sh --project ./projects/my-project      # открыть существующий проект
#   ./run_demo.sh --resume  ./projects/my-project      # сразу возобновить прерванный пайплайн
uv run python -m demo.cli "$@"
