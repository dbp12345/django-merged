#!/bin/bash

set -euo pipefail

cd /home/ubuntu/Project/app
source /home/ubuntu/Project/venv/bin/activate

DUMP_DIR="/home/ubuntu/Project/app/undump"
cd "$DUMP_DIR"

# Ищем последний sql или sql.gz файл
DUMP_FILE=$(ls -1t *.sql *.sql.gz 2>/dev/null | head -n 1 || true)

if [[ -z "$DUMP_FILE" ]]; then
    echo "❌ [FAIL] No .sql or .sql.gz file found in $DUMP_DIR"
    exit 1
fi

echo "[INFO] Using dump file: $DUMP_FILE"

# Отключаем ключи
mysql -u root -p'dbfightfire213#__DbF!locK' dbfightfire -e "
SET FOREIGN_KEY_CHECKS=0;
SET UNIQUE_CHECKS=0;
SET AUTOCOMMIT=0;
"

# Распаковываем или просто подаём файл
if [[ "$DUMP_FILE" == *.gz ]]; then
    gunzip -c "$DUMP_FILE" | mysql -u root -p'dbfightfire213#__DbF!locK' dbfightfire
else
    cat "$DUMP_FILE" | mysql -u root -p'dbfightfire213#__DbF!locK' dbfightfire
fi

# Включаем ключи
mysql -u root -p'dbfightfire213#__DbF!locK' dbfightfire -e "
SET FOREIGN_KEY_CHECKS=1;
SET UNIQUE_CHECKS=1;
COMMIT;
"

echo "✅ [DONE] Restore completed from $DUMP_FILE"
read -p "Press Enter to close..."