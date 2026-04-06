#!/bin/bash

set -euo pipefail

cd /home/ubuntu/Project/app

source /home/ubuntu/Project/venv/bin/activate

TIMESTAMP=$(TZ=America/Los_Angeles date +%Y_%m_%d_%H_%M)
DUMP_FILE="dbfightfire_${TIMESTAMP}_for_local.sql.gz"
ERROR_LOG="mysqldump_errors_${TIMESTAMP}.log"

echo "[INFO] Starting mysqldump..."

if mysqldump \
    --add-drop-table \
    --ignore-table=dbfightfire.synchronization_sync \
    --ignore-table=dbfightfire.synchronization_sync_parameters \
    --ignore-table=dbfightfire.synchronization_sync_parameters_logs \
    --ignore-table=dbfightfire.privser_request_to_privser \
    --ignore-table=dbfightfire.privser_request_from_privser \
    --ignore-table=dbfightfire.django_celery_results_taskresult \
    --ignore-table=dbfightfire.company_employee_change_queue \
    --ignore-table=dbfightfire.company_identificationdocuments \
    -u root -p'dbfightfire213#__DbF!locK' dbfightfire \
    2> "$ERROR_LOG" | gzip > "$DUMP_FILE"; then
    # Filter out password warning and check for real errors
    REAL_ERRORS=$(grep -viE "using a password on the command line interface can be insecure" "$ERROR_LOG" 2>/dev/null || true)
    if [ -s "$ERROR_LOG" ] && [ -n "$REAL_ERRORS" ] && echo "$REAL_ERRORS" | grep -qiE "error|warning|failed|skip"; then
        echo "❗️[WARN] Dump completed with warnings or errors:"
        cat "$ERROR_LOG"
    else
        echo "✅ [DONE] Dump created: $DUMP_FILE"
        rm -f "$ERROR_LOG"
    fi
    
    # Remove dumps older than 30 days (based on date in filename)
    echo "[INFO] Checking for old dumps (older than 30 days)..."
    ALL_DUMPS=$(find . -maxdepth 1 -name "dbfightfire_*_for_local.sql.gz" -type f 2>/dev/null | sort)
    CURRENT_DATE=$(TZ=America/Los_Angeles date +%Y_%m_%d)
    THIRTY_DAYS_AGO=$(TZ=America/Los_Angeles date -d "30 days ago" +%Y_%m_%d)
    REMOVED_COUNT=0
    
    if [ -n "$ALL_DUMPS" ]; then
        while IFS= read -r dump_file; do
            if [ -n "$dump_file" ]; then
                filename=$(basename "$dump_file")
                # Extract date from filename after "dbfightfire_" prefix
                # Format: dbfightfire_YYYY_MM_DD_HH_MM_for_local.sql.gz
                if [[ $filename =~ ^dbfightfire_([0-9]{4}_[0-9]{2}_[0-9]{2})_ ]]; then
                    file_date=${BASH_REMATCH[1]}
                    # Compare dates (YYYY_MM_DD format allows string comparison)
                    if [ "$file_date" \< "$THIRTY_DAYS_AGO" ]; then
                        echo "[INFO] Removing old dump: $filename (date: $file_date)"
                        rm -f "$dump_file"
                        REMOVED_COUNT=$((REMOVED_COUNT + 1))
                    fi
                fi
            fi
        done <<< "$ALL_DUMPS"
        
        if [ "$REMOVED_COUNT" -gt 0 ]; then
            echo "✅ [DONE] Removed $REMOVED_COUNT old dump(s)"
        else
            echo "[INFO] No dumps older than 30 days found"
        fi
    else
        echo "[INFO] No dump files found"
    fi
else
    echo "❌ [FAIL] mysqldump failed!"
    if [ -f "$ERROR_LOG" ]; then
        cat "$ERROR_LOG"
    fi
    exit 1
fi
