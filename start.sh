#!/usr/bin/env bash
# Sets up (if needed) and runs the whole app as a single process.
# Usage: ./start.sh

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Backend: setting up virtual environment =="
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

echo "== Frontend: installing dependencies =="
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "== Frontend: building =="
npm run build

echo "== Starting server on http://localhost:5000 =="
cd "$ROOT/backend"
python run.py
