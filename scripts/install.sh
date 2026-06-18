#!/bin/bash
# =============================================================================
# WFGY-Core V3 — Installateur Linux/macOS
# =============================================================================
set -e

echo ""
echo "============================================================"
echo "  WFGY-Core V3 — Installation"
echo "============================================================"
echo ""

# ---- Check Python ----
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 n'est pas installe."
    echo "        apt install python3 python3-venv python3-pip"
    exit 1
fi
echo "[OK] Python3 trouve: $(python3 --version)"

# ---- Create venv ----
if [ ! -d ".venv" ]; then
    echo ""
    echo "[1/5] Creation de l'environnement virtuel..."
    python3 -m venv .venv
    echo "[OK] Environnement virtuel cree"
else
    echo "[OK] Environnement virtuel existe deja"
fi

# ---- Install Python dependencies ----
echo ""
echo "[2/5] Installation des dependances Python..."
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r requirements.txt -q
echo "[OK] Dependances Python installees"

# ---- Install Chromatix ----
echo ""
echo "[3/5] Installation de Chromatix Pixel Standard..."
if [ -d "../chromatix" ]; then
    echo "    Trouve dans le repertoire parent"
elif [ -d "chromatix" ]; then
    echo "    Trouve dans le repertoire courant"
else
    echo "    Telechargement depuis GitHub..."
    git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git ../chromatix 2>/dev/null || true
    if [ -d "../chromatix" ]; then
        echo "[OK] Chromatix installe"
    else
        echo "[WARN] Chromatix non trouve — le vault utilisera un mode degrade"
        echo "       Clonez: git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git"
    fi
fi

# ---- Build Rust binary ----
echo ""
echo "[4/5] Compilation du moteur Rust..."
if [ -f "rust_muscle/target/release/rust_muscle" ]; then
    echo "[OK] Binaire Rust deja compile (release)"
elif [ -f "rust_muscle/target/debug/rust_muscle" ]; then
    echo "[OK] Binaire Rust deja compile (debug)"
else
    if command -v cargo &>/dev/null; then
        cd rust_muscle
        cargo build --release
        cd ..
        echo "[OK] Binaire Rust compile"
    else
        echo "[WARN] Cargo non disponible — saute la compilation Rust"
        echo "       Compilez: cd rust_muscle && cargo build --release"
    fi
fi

# ---- Configure environment ----
echo ""
echo "[5/5] Configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "[INFO] Fichier .env cree depuis .env.example"
        echo "       Editez-le avec vos parametres"
    fi
else
    echo "[OK] Fichier .env existe deja"
fi

# ---- Create required directories ----
mkdir -p workspace/output brain/vaults brain/logs

echo ""
echo "============================================================"
echo "  Installation terminee !"
echo "============================================================"
echo ""
echo "  Pour lancer le serveur :"
echo "    .venv/bin/python brain/orchestrator.py --server"
echo ""
echo "  Ouvrir le navigateur :"
echo "    http://localhost:8766"
echo ""
