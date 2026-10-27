#!/usr/bin/env bash

echo "=========================================================="
echo "      COLAB AI STUDIO - ARRET DES SERVICES"
echo "=========================================================="

echo "Arret des services Colab AI Studio..."
systemctl --user stop colab-frontend colab-backend colab-worker 2>/dev/null || true

# Liberation stricte des ports reseau
fuser -k 5173/tcp 8000/tcp 8190/tcp 2>/dev/null || true

# Nettoyage processus orphelins eventuels
pkill -f "vite --host 127.0.0.1" 2>/dev/null || true
pkill -f "run_local_worker.py" 2>/dev/null || true
pkill -f "uvicorn app.main:app" 2>/dev/null || true

echo "  -> Services arretes avec succes."
echo "  -> Ports 5173, 8000, 8190 et memoire VRAM liberes."
echo "=========================================================="
