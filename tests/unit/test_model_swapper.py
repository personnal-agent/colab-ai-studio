"""Tests unitaires de l'automate ModelSwapper (tests/unit/test_model_swapper.py).

Valide l'ensemble des états et transitions de 11-etats-model-swapper.svg :
1. EnVeilleVRAMLibre (initialisation à vide)
2. ChargementEnCours & transition vers ModeleActif
3. Réutilisation à chaud sans rechargement (cache hit)
4. Éviction mémoire complète (del, gc.collect, empty_cache, ipc_collect) lors d'un switch
5. Éviction automatique après inactivité (gpu_idle)
6. EnRecuperationSaturation lors d'un CUDA OutOfMemoryError
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.colab_worker.model_swapper import (
    CudaOutOfMemoryError,
    ModelSwapper,
    ModelSwapperState,
)


class MockCudaManager:
    """Mock simulant les appels bas niveau torch.cuda."""

    def __init__(self):
        self.empty_cache_called = 0
        self.ipc_collect_called = 0
        self.gc_collect_called = 0
        self.allocated_gb = 0.0

    def empty_cache(self):
        self.empty_cache_called += 1
        self.allocated_gb = 0.0

    def ipc_collect(self):
        self.ipc_collect_called += 1

    def gc_collect(self):
        self.gc_collect_called += 1


@pytest.mark.asyncio
async def test_initial_state_en_veille():
    cuda = MockCudaManager()
    swapper = ModelSwapper(cuda_manager=cuda, idle_timeout_seconds=0.1)

    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None
    assert swapper.vram_allocated_gb == 0.0
    assert swapper.pipeline_ready is False


@pytest.mark.asyncio
async def test_load_and_activate_model():
    cuda = MockCudaManager()
    swapper = ModelSwapper(cuda_manager=cuda)

    progress_events = []

    def on_progress(p: int):
        progress_events.append(p)

    pipeline = await swapper.acquire_model("minimax-h3", on_progress=on_progress)

    assert swapper.state == ModelSwapperState.MODELE_ACTIF
    assert swapper.active_model == "minimax-h3"
    assert swapper.pipeline_ready is True
    assert pipeline is not None
    assert 0 in progress_events
    assert 100 in progress_events


@pytest.mark.asyncio
async def test_reuse_active_model_without_reloading():
    cuda = MockCudaManager()
    load_counter = MagicMock()

    swapper = ModelSwapper(cuda_manager=cuda, loader_factory=load_counter)

    # Premier chargement
    await swapper.acquire_model("minimax-h3")
    assert load_counter.call_count == 1

    # Deuxième acquisition du même modèle -> réutilisation directe
    await swapper.acquire_model("minimax-h3")
    assert load_counter.call_count == 1
    assert swapper.state == ModelSwapperState.MODELE_ACTIF


@pytest.mark.asyncio
async def test_switch_model_triggers_full_eviction():
    cuda = MockCudaManager()
    swapper = ModelSwapper(cuda_manager=cuda)

    await swapper.acquire_model("model-a")
    assert swapper.active_model == "model-a"

    # Permutation vers model-b -> éviction complète
    await swapper.acquire_model("model-b")

    assert swapper.active_model == "model-b"
    assert cuda.empty_cache_called >= 1
    assert cuda.ipc_collect_called >= 1
    assert cuda.gc_collect_called >= 1


@pytest.mark.asyncio
async def test_idle_timeout_triggers_eviction():
    cuda = MockCudaManager()
    # Délai très court pour le test
    swapper = ModelSwapper(cuda_manager=cuda, idle_timeout_seconds=0.05)

    await swapper.acquire_model("model-a")
    assert swapper.active_model == "model-a"

    # Signaler que l'inférence est terminée (gpu_idle = True)
    swapper.notify_inference_completed()

    # Attendre que le timer d'inactivité déclenche l'éviction
    await asyncio.sleep(0.1)

    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None
    assert cuda.empty_cache_called >= 1


@pytest.mark.asyncio
async def test_out_of_memory_recovery():
    cuda = MockCudaManager()

    def failing_loader(model_id: str):
        raise CudaOutOfMemoryError("CUDA out of memory. Tried to allocate 12.00 GiB")

    swapper = ModelSwapper(cuda_manager=cuda, loader_factory=failing_loader)

    with pytest.raises(CudaOutOfMemoryError):
        await swapper.acquire_model("heavy-model")

    # Après échec et purge d'urgence, swapper doit être revenu EnVeilleVRAMLibre
    assert swapper.state == ModelSwapperState.EN_VEILLE_VRAM_LIBRE
    assert swapper.active_model is None
    assert cuda.empty_cache_called >= 1
    assert cuda.gc_collect_called >= 1
