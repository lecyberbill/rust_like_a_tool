#!/bin/bash
# Backup des donnees persistantes de WFGY-Core
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/wfgy_backup_$DATE.tar.gz"

echo "[BACKUP] Saving to $BACKUP_FILE..."

docker stop wfgy-etl 2>/dev/null

tar -czf "$BACKUP_FILE" \
    workspace/output \
    brain/vaults \
    brain/logs \
    brain/users.db \
    brain/workspaces.json \
    brain/run_history.json \
    brain/audit_trail.json \
    brain/notif_config.json \
    brain/history_recipes \
    2>/dev/null

docker start wfgy-etl 2>/dev/null

echo "[BACKUP] Done: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
