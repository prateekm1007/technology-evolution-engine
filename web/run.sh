#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH="$(cd .. && pwd):$PYTHONPATH"
python -m uvicorn backend.main:app --reload --port 8000
