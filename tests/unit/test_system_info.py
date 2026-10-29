"""Tests unitaires pour la sonde de métriques matérielles hôte (app/services/system_info.py)."""

from __future__ import annotations

from app.services.system_info import get_host_system_metrics


def test_get_host_system_metrics_structure():
    metrics = get_host_system_metrics()

    assert isinstance(metrics, dict)
    assert "cpu" in metrics
    assert "threads" in metrics
    assert "ram" in metrics
    assert "ramAvailableGb" in metrics

    assert isinstance(metrics["cpu"], str) and len(metrics["cpu"]) > 0
    assert isinstance(metrics["threads"], int) and metrics["threads"] > 0
    assert isinstance(metrics["ram"], str) and "Go" in metrics["ram"]
    assert isinstance(metrics["ramAvailableGb"], (int, float)) and metrics["ramAvailableGb"] >= 0


def test_get_host_system_metrics_caching():
    m1 = get_host_system_metrics()
    m2 = get_host_system_metrics()

    # Les données matérielles statiques doivent rester stables et cohérentes
    assert m1["cpu"] == m2["cpu"]
    assert m1["threads"] == m2["threads"]
    assert m1["ram"] == m2["ram"]
