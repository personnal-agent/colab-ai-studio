"""Tests unitaires pour la sonde de métriques matérielles hôte (app/services/system_info.py)."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from app.services.system_info import _probe_gpu_metrics, get_host_system_metrics


def test_get_host_system_metrics_structure():
    metrics = get_host_system_metrics()

    assert isinstance(metrics, dict)
    assert "cpu" in metrics
    assert "threads" in metrics
    assert "ram" in metrics
    assert "ramAvailableGb" in metrics
    assert "gpu" in metrics

    assert isinstance(metrics["cpu"], str) and len(metrics["cpu"]) > 0
    assert isinstance(metrics["threads"], int) and metrics["threads"] > 0
    assert isinstance(metrics["ram"], str) and "Go" in metrics["ram"]
    assert isinstance(metrics["ramAvailableGb"], (int, float)) and metrics["ramAvailableGb"] >= 0

    if metrics["gpu"] is not None:
        gpu = metrics["gpu"]
        assert isinstance(gpu, dict)
        assert "name" in gpu
        assert "shortName" in gpu
        assert "vramTotalMb" in gpu
        assert "vramFreeMb" in gpu
        assert "label" in gpu


def test_get_host_system_metrics_caching():
    m1 = get_host_system_metrics()
    m2 = get_host_system_metrics()

    # Les données matérielles statiques doivent rester stables et cohérentes
    assert m1["cpu"] == m2["cpu"]
    assert m1["threads"] == m2["threads"]
    assert m1["ram"] == m2["ram"]


def test_probe_gpu_metrics_with_mocked_nvidia_smi():
    mock_csv = (
        b"NVIDIA RTX 5000 Ada Generation Laptop GPU, 15352, 2048, 13304, 55, 12\n"
    )
    with patch("subprocess.check_output", return_value=mock_csv):
        gpu = _probe_gpu_metrics(bypass_cache=True)

        assert gpu is not None
        assert gpu["shortName"] == "RTX 5000 Ada"
        assert gpu["vramTotalMb"] == 15352
        assert gpu["vramUsedMb"] == 2048
        assert gpu["vramFreeMb"] == 13304
        assert gpu["temperatureC"] == 55
        assert gpu["utilizationPct"] == 12
        assert gpu["vramTotalGb"] == 15.0
        assert gpu["vramFreeGb"] == 13.0
        assert "RTX 5000 Ada" in gpu["label"]
        assert "13.0 Go" in gpu["label"]


def test_probe_gpu_metrics_fallback_on_error():
    err = subprocess.SubprocessError("nvidia-smi not found")
    with patch("subprocess.check_output", side_effect=err):
        gpu = _probe_gpu_metrics(bypass_cache=True)
        # Doit gérer l'erreur gracieusement sans lever d'exception
        assert gpu is None or "error" in gpu

