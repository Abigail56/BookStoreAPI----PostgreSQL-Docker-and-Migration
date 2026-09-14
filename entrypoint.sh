#!/usr/bin/env sh
set -e

echo "Waiting for database to accept connections..."
python - <<'PYEOF'
import os
import sys
import time

import psycopg

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")

for attempt in range(1, 31):
    try:
        conn = psycopg.connect(url)
        conn.close()
        print("Database is up.")
        sys.exit(0)
    except psycopg.OperationalError as exc:
        print(f"  attempt {attempt}/30: {exc}".strip())
        time.sleep(1)

print("Database never became available.", file=sys.stderr)
sys.exit(1)
PYEOF

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
