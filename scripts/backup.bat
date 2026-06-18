@echo off
REM Backup des donnees persistantes de WFGY-Core
set BACKUP_DIR=backups
set DATE=%DATE:~6,4%%DATE:~3,2%%DATE:~0,2%
mkdir %BACKUP_DIR% 2>nul
set BACKUP_FILE=%BACKUP_DIR%\wfgy_backup_%DATE%.zip

echo [BACKUP] Sauvegarde dans %BACKUP_FILE%...

REM Arreter le conteneur si Docker
docker stop wfgy-etl 2>nul

REM Sauvegarder les fichiers critiques
powershell -Command "Compress-Archive -Path 'workspace\output', 'brain\vaults', 'brain\logs', 'brain\users.db', 'brain\workspaces.json', 'brain\run_history.json', 'brain\audit_trail.json', 'brain\notif_config.json', 'brain\history_recipes' -DestinationPath '%BACKUP_FILE%' -Force"

REM Redemarrer le conteneur si Docker
docker start wfgy-etl 2>nul

echo [BACKUP] Termine: %BACKUP_FILE%
echo [BACKUP] Taille: 
dir %BACKUP_FILE%
