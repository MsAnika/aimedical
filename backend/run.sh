#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------
# 3️⃣  Gunicorn + Uvicorn workers
# ------------------------------------------------------------------
# Usage: bash run.sh   (from the backend folder)
# ------------------------------------------------------------------

WORKERS=${GUNICORN_WORKERS:-4}
PORT=${APP_PORT:-8000}

exec gunicorn -w $WORKERS -k uvicorn.app app.main:app --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --keep-alive 5 \
    --log-file -