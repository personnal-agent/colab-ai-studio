"""Service de sonde des métriques matérielles réelles de l'hôte (CPU, Threads, RAM, GPU/VRAM)."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import time
from contextlib import suppress
from typing import Any

import psutil

logger = logging.getLogger(__name__)

_STATIC_CACHE: dict[str, Any] | None = None
_GPU_CACHE: dict[str, Any] | None = None
_GPU_CACHE_TIMESTAMP: float = 0.0
_GPU_CACHE_TTL_SECONDS: float = 2.0


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


def _probe_gpu_metrics(bypass_cache: bool = False) -> dict[str, Any] | None:
    """Interroge nvidia-smi pour les métriques GPU & VRAM temps réel (avec cache court)."""
    global _GPU_CACHE, _GPU_CACHE_TIMESTAMP
    now = time.time()
    if (
        not bypass_cache
        and _GPU_CACHE is not None
        and (now - _GPU_CACHE_TIMESTAMP) < _GPU_CACHE_TTL_SECONDS
    ):
        return _GPU_CACHE

    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            timeout=1.0,
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="ignore").strip()

        lines = [line.strip() for line in out.splitlines() if line.strip()]
        if not lines:
            return None

        parts = [p.strip() for p in lines[0].split(",")]
        if len(parts) >= 6:
            name = parts[0]
            total_mb = int(parts[1])
            used_mb = int(parts[2])
            free_mb = int(parts[3])
            temp_c = int(parts[4])
            util_pct = int(parts[5])

            short_name = (
                name.replace("NVIDIA ", "")
                .replace(" Generation", "")
                .replace(" Laptop GPU", "")
                .strip()
            )
            total_gb = round(total_mb / 1024, 1)
            free_gb = round(free_mb / 1024, 1)
            used_gb = round(used_mb / 1024, 1)

            metrics = {
                "name": name,
                "shortName": short_name,
                "vramTotalMb": total_mb,
                "vramUsedMb": used_mb,
                "vramFreeMb": free_mb,
                "vramTotalGb": total_gb,
                "vramUsedGb": used_gb,
                "vramFreeGb": free_gb,
                "temperatureC": temp_c,
                "utilizationPct": util_pct,
                "label": f"{short_name} · {free_gb} Go VRAM",
            }
            _GPU_CACHE = metrics
            _GPU_CACHE_TIMESTAMP = now
            return metrics
    except (subprocess.SubprocessError, OSError, ValueError) as err:
        logger.debug("Échec de la sonde GPU via nvidia-smi: %s", err)

    return None


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

    gpu_metrics = _probe_gpu_metrics()

    return {
        **_STATIC_CACHE,
        "ramAvailableGb": available_gb,
        "gpu": gpu_metrics,
    }

