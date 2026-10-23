"""Test de mesure d'empreinte mémoire du backend FastAPI (tests/e2e/test_memory_footprint.py).

Démarre le serveur FastAPI dans un processus OS dédié indépendant (subprocess.Popen)
sans charger le runner pytest ni le worker GPU, et vérifie la contrainte stricte :
Empreinte mémoire RSS < 80 Mo.
"""

import os
import socket
import subprocess
import sys
import time

import httpx
import psutil


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_isolated_backend_memory_footprint():
    port = get_free_port()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    env = os.environ.copy()
    env["PYTHONPATH"] = repo_root

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Attendre que le serveur réponde
        base_url = f"http://127.0.0.1:{port}"
        started = False
        for _ in range(30):
            time.sleep(0.2)
            try:
                resp = httpx.get(f"{base_url}/api/health", timeout=1.0)
                if resp.status_code == 200:
                    started = True
                    break
            except Exception as err:
                _ = str(err)

        assert started, "Le serveur backend FastAPI n'a pas démarré à temps."

        # Mesure de l'empreinte mémoire RSS via psutil
        p = psutil.Process(proc.pid)
        rss_bytes = p.memory_info().rss
        rss_mb = rss_bytes / (1024 * 1024)

        # Journaliser la mesure réelle
        print(f"\n[Empreinte Mémoire Backend] RSS = {rss_mb:.2f} Mo (< 80 Mo max toléré)")

        msg = f"Empreinte mémoire backend ({rss_mb:.2f} Mo) dépasse le seuil de 80 Mo."
        assert rss_mb < 80.0, msg

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
