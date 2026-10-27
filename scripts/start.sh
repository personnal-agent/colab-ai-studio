#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "      COLAB AI STUDIO - DEMARRAGE DES SERVICES"
echo "=========================================================="

# 1. ComfyUI
echo "[1/4] Verification de ComfyUI (port 8188)..."
systemctl --user is-active comfyui >/dev/null 2>&1 || systemctl --user start comfyui || true

# 2. Demarrage des 3 services studio via systemd
echo "[2/4] Demarrage du Worker Local GPU (port 8190)..."
echo "[3/4] Demarrage du Backend FastAPI (port 8000)..."
echo "[4/4] Demarrage du Frontend Web (port 5173)..."
systemctl --user start colab-worker colab-backend colab-frontend

# 3. Synchronisation et attente
echo "Synchronisation et attente de la disponibilite des services..."
for i in {1..20}; do
    if curl -s http://127.0.0.1:5173 >/dev/null 2>&1 && curl -s http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
        echo "  -> Tous les services sont prets !"
        break
    fi
    sleep 0.5
done

echo "=========================================================="
echo "  STUDIO PRET SUR : http://localhost:5173"
echo "=========================================================="
