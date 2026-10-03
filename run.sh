#!/usr/bin/env bash
# run.sh — One-command startup for Re:Learn
# Usage: bash run.sh

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo ""
echo "  🎓 Re:Learn — Adaptive Misconception Diagnosis System"
echo "  ─────────────────────────────────────────────────────"
echo ""

# Activate venv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "  ✅ Virtual env activated"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "  ✅ Virtual env activated"
else
    echo "  ⚠  No virtual env found — using system Python"
fi

# Install dependencies
echo "  📦 Installing dependencies…"
pip install -r requirements.txt -q

# Create necessary directories
mkdir -p backend/data ml/artifacts

# Start FastAPI server
echo ""
echo "  🚀 Starting FastAPI server at http://127.0.0.1:8000"
echo "  📖 Docs:    http://127.0.0.1:8000/docs"
echo "  🌐 App:     http://127.0.0.1:8000/"
echo ""

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
