#!/bin/bash
# PRANAVYU — Start script
# Runs backend (FastAPI) and frontend (Vite) simultaneously

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        PRANAVYU — Air Quality Intelligence       ║"
echo "║          ET AI Hackathon 2026                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Load .env if present
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
  echo "✓ Loaded .env"
fi

# Check Python deps
echo "→ Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, langgraph, langchain_groq" 2>/dev/null || {
  echo "→ Installing Python dependencies..."
  pip install -r requirements.txt --break-system-packages -q
}
echo "✓ Python dependencies OK"

# Check Node deps
if [ ! -d "node_modules" ]; then
  echo "→ Installing Node.js dependencies..."
  npm install --silent
fi
echo "✓ Node.js dependencies OK"

# Build frontend
echo "→ Building frontend..."
npm run build --silent
echo "✓ Frontend built"

# Start backend
echo ""
echo "→ Starting FastAPI backend on http://localhost:8000"
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

# Serve frontend via Vite (dev with proxy) or static build
echo "→ Starting frontend on http://localhost:3000"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  PRANAVYU is running!                            ║"
echo "║  Dashboard: http://localhost:3000                ║"
echo "║  API docs:  http://localhost:8000/docs           ║"
echo "║  Press Ctrl+C to stop                           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'PRANAVYU stopped.'" EXIT INT TERM
wait
