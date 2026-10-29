"""Service de sonde des métriques matérielles réelles de l'hôte (CPU, Threads, RAM)."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from contextlib import suppress
from typing import Any

import psutil

logger = logging.getLogger(__name__)

_STATIC_CACHE: dict[str, Any] | None = None


def _probe_cpu_model() -> tuple[str, str]:
    """Extrait le modèle CPU depuis /proc/cpuinfo (Linux/WSL) ou platform.processor()."""
    try:
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        raw = line.split(":", 1)[1].strip()
                        cleaned = (
                            raw.replace("(R)", "")
                            .replace("(TM)", "")
                            .replace("13th Gen ", "")
                            .strip()
                        )
                        return cleaned, raw
    except OSError as err:
        logger.debug("Impossible de lire /proc/cpuinfo: %s", err)

    fallback_raw = platform.processor() or "CPU Hôte"
    fallback_clean = fallback_raw
    return fallback_clean, fallback_raw


def _probe_host_ram() -> str:
    """Détecte la RAM physique totale de l'hôte (Windows hôte via PowerShell sur WSL, ou psutil)."""
    # 1. Tentative d'interrogation de l'hôte physique Windows via PowerShell sur WSL
    ps_cmd = "[Math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)"
    try:
        out = subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            timeout=1.0,
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="ignore").strip()
        val = float(out.replace(",", "."))
        if val > 0:
            return f"{val} Go"
    except (subprocess.SubprocessError, OSError, ValueError) as err:
        logger.debug("Échec de détection RAM hôte Windows PowerShell: %s", err)

    # 2. Repli sur psutil (RAM allouée au système / conteneur Linux)
    try:
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        return f"{ram_gb} Go"
    except OSError as err:
        logger.debug("Échec de lecture RAM via psutil: %s", err)

    return "64 Go"


def get_host_system_metrics() -> dict[str, Any]:
    """Retourne les métriques matérielles actuelles de la machine avec cache statique."""
    global _STATIC_CACHE
    if _STATIC_CACHE is None:
        cpu_clean, cpu_raw = _probe_cpu_model()
        threads = os.cpu_count() or 32
        physical_cores = None
        with suppress(Exception):
            physical_cores = psutil.cpu_count(logical=False)
        ram_total = _probe_host_ram()

        _STATIC_CACHE = {
            "cpu": cpu_clean,
            "cpuRaw": cpu_raw,
            "threads": threads,
            "physicalCores": physical_cores,
            "ram": ram_total,
        }

    # Calcul dynamique de la mémoire disponible instantanée
    available_gb = 0.0
    with suppress(Exception):
        available_gb = round(psutil.virtual_memory().available / (1024**3), 1)

    return {
        **_STATIC_CACHE,
        "ramAvailableGb": available_gb,
    }
