"""Tests unitaires de l'automate ModelSwapper (tests/unit/test_model_swapper.py).

Couvre l'intégralité des transitions d'états de 11-etats-model-swapper.svg :
- Initialisation à vide (EnVeilleVRAMLibre)
- Chargement à la demande (ChargementEnCours -> ModeleActif)
- Réutilisation directe sans rechargement si modèle déjà résident
- Éviction préalable complète avant chargement d'un nouveau modèle
- Éviction automatique après délai d'inactivité (gpu_idle)
- Récupération sur saturation CUDA OOM (EnRecuperationSaturation -> EnVeilleVRAMLibre)
- Arrêt propre du worker (Arrete)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.colab_worker.model_swapper import (
    CUDAOutOfMemoryError,
    DefaultCudaBackend,
    ModelSwapper,
    ModelSwapperOOMError,
    ModelSwapperState,
)


class MockTorchCuda:
    """Mock contrôlable de torch.cuda pour environnement de test hôte sans GPU."""

    def __init__(self, is_available: bool = True, memory_mb: float = 16384.0) -> None:
        self._is_available, self._total_memory_mb, self._allocated_mb = is_available, memory_mb, 0.0
        self.empty_cache_called, self.ipc_collect_called = 0, 0

    def is_available(self) -> bool:
        return self._is_available

    def empty_cache(self) -> None:
        self.empty_cache_called += 1
        self._allocated_mb = 0.0

    def ipc_collect(self) -> None:
        self.ipc_collect_called += 1

    def memory_allocated(self, device: int | None = None) -> int:
        return int(self._allocated_mb * 1024 * 1024)

    def get_device_name(self, device: int | None = None) -> str:
        return "NVIDIA Tesla T4"


@pytest.fixture
def mock_cuda() -> MockTorchCuda:
    return MockTorchCuda(is_available=True)


@pytest.fixture
def swapper(mock_cuda: MockTorchCuda) -> ModelSwapper:
    return ModelSwapper(cuda_backend=mock_cuda, idle_timeout_seconds=300.0)


def test_initialization_state(swapper: ModelSwapper) -> None:
    """Vérifie l'état initial EnVeilleVRAMLibre sans modèle résident."""
    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None and swapper.active_pipeline is None
    assert swapper.pipeline_ready is False and swapper.vram_allocated_gb == 0.0


def test_load_model_on_demand(swapper: ModelSwapper) -> None:
    """Vérifie le chargement à la demande d'un modèle et la publication de progression."""
    progress_history: list[float] = []

    def mock_loader(model_id: str) -> dict[str, str]:
        return {"pipeline_name": f"Pipeline_{model_id}"}

    pipeline = swapper.ensure_model(
        "flux-schnell",
        load_fn=mock_loader,
        on_progress=lambda p: progress_history.append(p),
    )

    assert swapper.state == ModelSwapperState.MODELE_ACTIF
    assert swapper.active_model == "flux-schnell"
    assert swapper.pipeline_ready is True
    assert pipeline == {"pipeline_name": "Pipeline_flux-schnell"}
    assert len(progress_history) >= 2
    assert progress_history[0] == 0.0
    assert progress_history[-1] == 1.0


def test_direct_reuse_when_model_already_resident(swapper: ModelSwapper) -> None:
    """Vérifie que la réutilisation du même modèle n'exécute aucun chargement redondant."""
    loader = MagicMock(return_value={"weights": "loaded"})

    # Premier chargement
    p1 = swapper.ensure_model("flux-schnell", load_fn=loader)
    assert loader.call_count == 1

    # Deuxième appel identique
    initial_activity_time = swapper.last_activity_time
    p2 = swapper.ensure_model("flux-schnell", load_fn=loader)
    assert loader.call_count == 1  # Pas de second chargement
    assert p1 == p2
    assert swapper.state == ModelSwapperState.MODELE_ACTIF
    assert swapper.last_activity_time >= initial_activity_time


def test_eviction_before_loading_new_model(
    swapper: ModelSwapper, mock_cuda: MockTorchCuda
) -> None:
    """Vérifie le protocole strict d'éviction VRAM lors de la bascule vers un nouveau modèle."""
    loader = MagicMock(side_effect=lambda mid: {"model": mid})

    # Charger Modèle A
    swapper.ensure_model("flux-schnell", load_fn=loader)
    assert swapper.active_model == "flux-schnell"

    # Permutation vers Modèle B
    prev_empty_cache = mock_cuda.empty_cache_called
    swapper.ensure_model("wan-2.1-t2v", load_fn=loader)

    assert mock_cuda.empty_cache_called > prev_empty_cache
    assert mock_cuda.ipc_collect_called >= 1
    assert swapper.active_model == "wan-2.1-t2v"
    assert swapper.state == ModelSwapperState.MODELE_ACTIF
    assert loader.call_count == 2


def test_idle_timeout_auto_eviction(swapper: ModelSwapper, mock_cuda: MockTorchCuda) -> None:
    """Vérifie l'éviction automatique après expiration du délai d'inactivité (gpu_idle)."""
    swapper.ensure_model("flux-schnell", load_fn=lambda _: {"data": 123})
    assert swapper.state == ModelSwapperState.MODELE_ACTIF

    # Pas encore expiré (100s < 300s)
    swapper.check_idle_timeout(now=swapper.last_activity_time + 100.0)
    assert swapper.state == ModelSwapperState.MODELE_ACTIF
    assert swapper.active_model == "flux-schnell"

    # Expiré (301s >= 300s)
    evicted = swapper.check_idle_timeout(now=swapper.last_activity_time + 301.0)
    assert evicted is True
    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None and swapper.active_pipeline is None
    assert swapper.pipeline_ready is False and mock_cuda.empty_cache_called >= 1


def test_out_of_memory_error_recovery(swapper: ModelSwapper, mock_cuda: MockTorchCuda) -> None:
    """Vérifie la transition EnRecuperationSaturation et la purge mémoire sur CUDA OOM."""

    def crashing_loader(model_id: str):
        raise CUDAOutOfMemoryError("CUDA out of memory. Tried to allocate 4.00 GiB")

    with pytest.raises(ModelSwapperOOMError) as exc_info:
        swapper.ensure_model("large-video-model", load_fn=crashing_loader)

    assert "CUDA out of memory" in str(exc_info.value)
    # Après OOM, l'automate a forcé la purge et est revenu en veille saine
    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None
    assert swapper.pipeline_ready is False
    assert mock_cuda.empty_cache_called >= 1


def test_stop_worker(swapper: ModelSwapper, mock_cuda: MockTorchCuda) -> None:
    """Vérifie l'arrêt complet du worker et la libération mémoire."""
    swapper.ensure_model("flux-schnell", load_fn=lambda _: {"pipeline": True})
    assert swapper.active_model == "flux-schnell"

    swapper.stop()
    assert swapper.state == ModelSwapperState.ARRETE and swapper.active_model is None
    assert swapper.active_pipeline is None and swapper.pipeline_ready is False
    assert mock_cuda.empty_cache_called >= 1


def test_telemetry(swapper: ModelSwapper) -> None:
    """Vérifie la génération de télémétrie complète pour les diagnostics /health."""
    telemetry = swapper.get_telemetry()
    assert telemetry["state"] == "EnVeilleVRAMLibre" and telemetry["activeModel"] is None
    assert telemetry["pipelineReady"] is False and telemetry["gpu"] == "NVIDIA Tesla T4"
    assert isinstance(telemetry["vramFreeMb"], (int, float))


def test_default_cuda_backend_execution() -> None:
    """Vérifie que DefaultCudaBackend s'exécute sans erreur même sans GPU (Thread #3)."""
    backend = DefaultCudaBackend()
    assert isinstance(backend.is_available(), bool)
    # L'appel à empty_cache et ipc_collect ne doit lever ni AttributeError ni exception
    backend.empty_cache()
    backend.ipc_collect()
    assert isinstance(backend.memory_allocated(), int)
    assert isinstance(backend.get_device_name(), str)

