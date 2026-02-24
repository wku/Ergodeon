#!/bin/bash
set -e

cd "$(dirname "$0")"

if ! command -v uv &> /dev/null; then
    echo "uv не найден. Установите: pip install uv"
    exit 1
fi

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY не задан в .env"
fi

MODE="${1:-dev}"

if [ "$MODE" = "--prod" ] || [ "$MODE" = "prod" ]; then
    # Prod: собираем Svelte, запускаем только питон
    echo "📦 Сборка Svelte клиента..."
    cd web
    if ! command -v npm &> /dev/null; then
        echo "npm не найден. Установите Node.js."
        exit 1
    fi
    npm install --silent
    npm run build
    cd ..
    echo "🚀 Запускаю сервер (prod)..."
    PYTHONPATH=src uv run uvicorn openrouter_agent.server.app:app \
        --host 0.0.0.0 \
        --port "${PORT:-8000}"
else
    # Dev: питон + Svelte dev server параллельно
    echo "🚀 Запускаю dev режим..."
    echo "   Сервер:  http://localhost:8000"
    echo "   Клиент:  http://localhost:5173"
    echo ""

    # Запускаем питон в фоне
    PYTHONPATH=src uv run uvicorn openrouter_agent.server.app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload &
    SERVER_PID=$!

    # Устанавливаем зависимости и запускаем Svelte dev
    cd web
    if ! command -v npm &> /dev/null; then
        echo "npm не найден. Установите Node.js."
        kill $SERVER_PID 2>/dev/null
        exit 1
    fi
    npm install --silent
    npm run dev &
    CLIENT_PID=$!
    cd ..

    echo "Для остановки нажмите Ctrl+C"

    # Ловим Ctrl+C и завершаем оба процесса
    trap "echo ''; echo 'Останавливаю...'; kill $SERVER_PID $CLIENT_PID 2>/dev/null; exit 0" INT TERM

    # Ждём завершения любого из процессов
    wait $SERVER_PID $CLIENT_PID
fi


#uv add python-socketio websockets pyyaml