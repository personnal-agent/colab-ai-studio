#!/usr/bin/env bash
# ==============================================================================
# Colab AI Studio — Developer Environment & Git Hooks Setup (Linux / macOS / WSL)
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================================================"
echo "  🚀 Colab AI Studio — Setup de l'environnement de développement"
echo "======================================================================"

# 1. Activation des Git Hooks locaux
echo ""
echo "[1/4] Configuration des Git Hooks (.githooks)..."
if command -v git >/dev/null 2>&1; then
    git config core.hooksPath .githooks
    echo "  ✓ core.hooksPath configuré sur '.githooks'"
else
    echo "  ❌ Git n'est pas installé ou introuvable dans le PATH."
    exit 1
fi

# 2. Vérification des fins de ligne (LF)
echo ""
echo "[2/4] Normalisation des fichiers et scripts vers LF..."
if [ -f ".gitattributes" ]; then
    echo "  ✓ .gitattributes est présent."
fi
chmod +x .githooks/* .githooks/_common/* 2>/dev/null || true
echo "  ✓ Permissions d'exécution accordées sur .githooks/*."

# 3. Vérification des dépendances logicielles de base
echo ""
echo "[3/4] Vérification des runtimes (Python & Node.js)..."
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "  ✓ Python 3 détecté : version $PY_VER"
else
    echo "  ⚠️ Python 3 introuvable (requis >= 3.10 pour le backend)."
fi

if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node -v)
    echo "  ✓ Node.js détecté : $NODE_VER"
else
    echo "  ⚠️ Node.js introuvable (requis >= 20 pour le frontend)."
fi

# 4. Vérification de gitleaks (obligatoire pour pre-commit / pre-push)
echo ""
echo "[4/4] Vérification de l'outil de sécurité gitleaks..."
if command -v gitleaks >/dev/null 2>&1; then
    GITLEAKS_VER=$(gitleaks version 2>/dev/null || echo "installé")
    echo "  ✓ gitleaks détecté : $GITLEAKS_VER"
else
    echo "  ⚠️ gitleaks est absent. Il est obligatoire pour committer localement."
    echo "  Pour l'installer sans droits root :"
    echo '    VERSION=8.30.1; OS=$(uname -s | tr "[:upper:]" "[:lower:]"); ARCH=$(uname -m); [ "$ARCH" = "x86_64" ] && ARCH="x64"; cd "$(mktemp -d)" && curl -sSfL -O "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_${OS}_${ARCH}.tar.gz" && tar -xzf "gitleaks_${VERSION}_${OS}_${ARCH}.tar.gz" gitleaks && mkdir -p "$HOME/.local/bin" && install -m 755 gitleaks "$HOME/.local/bin/gitleaks"'
fi

echo ""
echo "======================================================================"
echo "  ✅ Configuration terminée. Les hooks locaux sont opérationnels !"
echo "======================================================================"
