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
    CONFIGURED=$(git config --get core.hooksPath 2>/dev/null || true)
    if [ "$CONFIGURED" != ".githooks" ]; then
        echo "  ❌ Échec de la configuration de core.hooksPath (obtenu: '$CONFIGURED')."
        exit 1
    fi
    echo "  ✓ core.hooksPath configuré sur '$CONFIGURED'"
else
    echo "  ❌ Git n'est pas installé ou introuvable dans le PATH."
    exit 1
fi

# 2. Vérification des fins de ligne (LF)
echo ""
echo "[2/4] Normalisation des fichiers et scripts vers LF..."
if [ -f ".gitattributes" ]; then
    echo "  ✓ .gitattributes est présent."
else
    echo "  ⚠️ .gitattributes est absent."
fi

CRLF_COUNT=0
if [ -d ".githooks" ]; then
    while IFS= read -r -d '' file; do
        if grep -q $'\r' "$file" 2>/dev/null; then
            CRLF_COUNT=$((CRLF_COUNT + 1))
            tr -d '\r' < "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
        fi
    done < <(find .githooks -type f -print0)
fi

if [ "$CRLF_COUNT" -gt 0 ]; then
    echo "  ✓ $CRLF_COUNT fichier(s) sous .githooks normalisé(s) vers LF."
else
    echo "  ✓ Tous les fichiers sous .githooks sont déjà au format LF."
fi

chmod +x .githooks/* .githooks/_common/* 2>/dev/null || true
echo "  ✓ Permissions d'exécution accordées sur .githooks/*."

# 3. Vérification des dépendances logicielles de base
echo ""
echo "[3/4] Vérification des runtimes (Python >= 3.10 & Node.js >= 20)..."
RUNTIME_FAILED=0

PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
elif command -v python.exe >/dev/null 2>&1; then
    PY_BIN="python.exe"
fi

if [ -n "$PY_BIN" ]; then
    PY_OK=$("$PY_BIN" -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)' 2>/dev/null || echo "0")
    PY_VER=$("$PY_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")' 2>/dev/null || echo "inconnue")
    if [ "$PY_OK" = "1" ]; then
        echo "  ✓ Python détecté ($PY_BIN) : version $PY_VER (>= 3.10 valide)"
    else
        echo "  ❌ Python version $PY_VER non supportée (requis >= 3.10 pour le backend)."
        RUNTIME_FAILED=1
    fi
else
    echo "  ❌ Python introuvable dans le PATH (requis >= 3.10 pour le backend)."
    RUNTIME_FAILED=1
fi

NODE_BIN=""
if command -v node >/dev/null 2>&1; then
    NODE_BIN="node"
elif command -v nodejs >/dev/null 2>&1; then
    NODE_BIN="nodejs"
elif command -v node.exe >/dev/null 2>&1; then
    NODE_BIN="node.exe"
fi

if [ -n "$NODE_BIN" ]; then
    NODE_RAW=$("$NODE_BIN" -v 2>/dev/null | tr -d 'v' || echo "0")
    NODE_MAJOR=$(echo "$NODE_RAW" | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 20 ] 2>/dev/null; then
        echo "  ✓ Node.js détecté ($NODE_BIN) : version v$NODE_RAW (>= 20 valide)"
    else
        echo "  ❌ Node.js version v$NODE_RAW non supportée (requis >= 20 pour le frontend)."
        RUNTIME_FAILED=1
    fi
else
    echo "  ❌ Node.js introuvable dans le PATH (requis >= 20 pour le frontend)."
    RUNTIME_FAILED=1
fi

if [ "$RUNTIME_FAILED" -ne 0 ]; then
    echo "  ❌ Un ou plusieurs runtimes requis sont manquants ou obsolètes."
    exit 1
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
