#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import os, socket, time, sys
h=os.environ.get("DB_HOST","db"); p=int(os.environ.get("DB_PORT","3306"))
for i in range(200):
    try:
        with socket.create_connection((h,p), 1):
            print(f"DB {h}:{p} is up")
            break
    except OSError:
        time.sleep(1)
else:
    sys.exit("DB not reachable")
PY

python manage.py migrate --noinput

# CHANGED: skip collectstatic in DEBUG
if [ "${DEBUG:-False}" != "True" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
