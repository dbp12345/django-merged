#!/bin/bash

set -euo pipefail

cd /home/ubuntu/Project/app

source /home/ubuntu/Project/venv/bin/activate

TIMESTAMP=$(TZ=America/Los_Angeles date +%Y_%m_%d_%H_%M)
DUMP_FILE="dbfightfire_${TIMESTAMP}.sql.gz"
ERROR_LOG="mysqldump_errors_${TIMESTAMP}.log"

echo "[INFO] Starting mysqldump..."

if mysqldump --add-drop-table -u root -p'dbfightfire213#__DbF!locK' dbfightfire 2> "$ERROR_LOG" | gzip > "$DUMP_FILE"; then
    if grep -qiE "error|warning|failed|skip" "$ERROR_LOG"; then
        echo "❗️[WARN] Dump completed with warnings or errors:"
        cat "$ERROR_LOG"
    else
        echo "✅ [DONE] Dump created: $DUMP_FILE"
        rm -f "$ERROR_LOG"
    fi
else
    echo "❌ [FAIL] mysqldump failed!"
    cat "$ERROR_LOG"
    exit 1
fi
