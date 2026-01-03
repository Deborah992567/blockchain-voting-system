#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Python virtualenv and installing backend dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Done. Activate the venv with: source .venv/bin/activate"
echo "Run migrations: alembic upgrade head"
echo "Run tests: PYTHONPATH=. pytest -q"
