#!/usr/bin/env bash
# Start ZKONER development stack
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting ZKONER v0.1..."

# Start backend
echo "📡 Starting backend (port 8000)..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
uvicorn main:app --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "🌐 Starting frontend (port 3000)..."
cd "$PROJECT_DIR/frontend"
npx next dev --port 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ ZKONER is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
