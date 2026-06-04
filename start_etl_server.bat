@echo off
chcp 65001 >nul
title WFGY ETL Server Launcher

echo ===================================================
echo   DEMARRAGE DU SERVEUR D'ORCHESTRATION WFGY CORE V3
echo ===================================================

if exist .venv goto activate

echo [INFO] Creation de l'environnement virtuel (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [INFO] Echec de la commande 'python'. Tentative avec 'py'...
    py -m venv .venv
)

if not exist .venv (
    echo [ERREUR] Impossible de trouver ou creer le dossier .venv.
    pause
    exit /b 1
)

:activate
echo [INFO] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo [INFO] Installation des dependances...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [INFO] Lancement du serveur WebSocket sur le port 8765...
python brain/orchestrator.py --server

if %errorlevel% neq 0 (
    echo [ERREUR] Le serveur s'est arrete avec une erreur.
)
pause
