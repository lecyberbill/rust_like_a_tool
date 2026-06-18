@echo off
REM =============================================================================
REM WFGY-Core V3 — Installateur Windows
REM =============================================================================
title Installation WFGY-Core V3
echo.
echo ============================================================
echo   WFGY-Core V3 — Installation
echo ============================================================
echo.

REM ---- Verifier Python ----
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python n'est pas installe.
    echo         Telechargez-le depuis https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python trouve

REM ---- Verifier Rust (optionnel) ----
where cargo >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Rust/Cargo trouve
) else (
    echo [INFO] Rust non trouve — le binaire sera compile plus tard
    echo        ou telecharge depuis les releases.
)

REM ---- Creer l'environnement virtuel ----
if not exist .venv\ (
    echo.
    echo [1/5] Creation de l'environnement virtuel...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Echec de creation du venv
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree
) else (
    echo [OK] Environnement virtuel existe deja
)

REM ---- Installer les dependances Python ----
echo.
echo [2/5] Installation des dependances Python...
.venv\Scripts\python.exe -m pip install --upgrade pip -q
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Echec d'installation des dependances
    pause
    exit /b 1
)
echo [OK] Dependances Python installees

REM ---- Installer Chromatix Pixel Standard ----
echo.
echo [3/5] Installation de Chromatix Pixel Standard...
if exist ..\chromatix\ (
    echo     Trouve dans le repertoire parent
) else (
    echo     Telechargement depuis GitHub...
    git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git ..\chromatix 2>nul
    if exist ..\chromatix\ (
        echo [OK] Chromatix installe
    ) else (
        echo [WARN] Chromatix non trouve — le vault utilisera un mode degrade
        echo        Clonez-le manuellement: git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git
    )
)

REM ---- Compiler le binaire Rust ----
echo.
echo [4/5] Compilation du moteur Rust...
if exist rust_muscle\target\release\rust_muscle.exe (
    echo [OK] Binaire Rust deja compile (release)
) else if exist rust_muscle\target\debug\rust_muscle.exe (
    echo [OK] Binaire Rust deja compile (debug)
) else (
    where cargo >nul 2>&1
    if %errorlevel% equ 0 (
        cd rust_muscle
        cargo build --release
        cd ..
        if exist rust_muscle\target\release\rust_muscle.exe (
            echo [OK] Binaire Rust compile
        ) else (
            echo [WARN] Echec compilation Rust — utiliser cargo build manuellement
        )
    ) else (
        echo [WARN] Cargo non disponible — saute la compilation Rust
        echo        Compilez le binaire manuellement: cd rust_muscle ^&^& cargo build --release
    )
)

REM ---- Configurer l'environnement ----
echo.
echo [5/5] Configuration...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [INFO] Fichier .env cree depuis .env.example
        echo       Editez-le avec vos parametres avant de lancer le serveur
    )
) else (
    echo [OK] Fichier .env existe deja
)

REM ---- Creer les dossiers necessaires ----
if not exist workspace\output\ mkdir workspace\output\ >nul 2>&1
if not exist brain\vaults\ mkdir brain\vaults\ >nul 2>&1
if not exist brain\logs\ mkdir brain\logs\ >nul 2>&1

echo.
echo ============================================================
echo   Installation terminee !
echo ============================================================
echo.
echo   Pour lancer le serveur :
echo     .venv\Scripts\python.exe brain\orchestrator.py --server
echo.
echo   Ou avec le script de demarrage :
echo     start_etl_server.bat
echo.
echo   Ouvrir le navigateur :
echo     http://localhost:8766
echo.
pause
