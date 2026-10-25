"""Test de validation d'empreinte mémoire locale du backend (< 80 Mo RAM RSS)."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import httpx
import psutil
import pytest

from app.config import REPO_ROOT


def _get_free_port() -> int:
    """Trouve dynamiquement un port TCP disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_isolated_backend_memory_footprint(tmp_path) -> None:
    """Mesure le RSS exclusif du processus backend FastAPI isolé (< 80 Mo RAM)."""
    port = _get_free_port()
    env = os.environ.copy()
    env["COLAB_STUDIO_ROOT"] = str(tmp_path)
    env["COLAB_STUDIO_DATA_DIR"] = str(tmp_path / "data")
    env["COLAB_STUDIO_OUTPUTS_DIR"] = str(tmp_path / "outputs")
    env["PYTHONPATH"] = str(REPO_ROOT)

    cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--port", str(port), "--host", "127.0.0.1",
    ]
    proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        base_url = f"http://127.0.0.1:{port}"
        started = False
        for _ in range(60):
            try:
                if httpx.get(f"{base_url}/api/health", timeout=1.0).status_code == 200:
                    started = True
                    break
            except (httpx.HTTPError, OSError):
                pass
            time.sleep(0.1)

        if not started:
            stdout, stderr = proc.communicate(timeout=2.0)
            pytest.fail(
                f"Le serveur backend n'a pas répondu sur {base_url} dans le délai imparti.\n"
                f"STDOUT: {stdout.decode(errors='ignore')}\n"
                f"STDERR: {stderr.decode(errors='ignore')}"
            )

        rss_mb = psutil.Process(proc.pid).memory_info().rss / (1024 * 1024)
        assert rss_mb < 80.0, f"Backend RSS ({rss_mb:.2f} Mo) >= 80 Mo."
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
