"""Automate ModelSwapper pour la gestion de VRAM GPU (app/colab_worker/model_swapper.py).

Implémente la machine à états de 11-etats-model-swapper.svg pour GPU Tesla T4 (16 Go) :
- EnVeilleVRAMLibre
- ChargementEnCours
- ModeleActif
- EvictionVRAMEnCours
- EnRecuperationSaturation
"""

from __future__ import annotations

import asyncio
import gc
import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger("colab_worker.model_swapper")


class ModelSwapperState(str, Enum):
    EN_VEILLE_VRAM_LIBRE = "EnVeilleVRAMLibre"
    CHARGEMENT_EN_COURS = "ChargementEnCours"
    MODELE_ACTIF = "ModeleActif"
    EVICTION_VRAM_EN_COURS = "EvictionVRAMEnCours"
    EN_RECUPERATION_SATURATION = "EnRecuperationSaturation"


class CudaOutOfMemoryError(Exception):
    """Exception levée en cas de dépassement de capacité VRAM."""


class DefaultCudaManager:
    """Gestionnaire CUDA réel utilisant torch.cuda si disponible."""

    def __init__(self) -> None:
        try:
            import importlib

            torch = importlib.import_module("torch")
            self._torch = torch
            cuda_mod = getattr(torch, "cuda", None)
            self._has_cuda = bool(cuda_mod is not None and cuda_mod.is_available())
        except ImportError:
            self._torch = None
            self._has_cuda = False

    def empty_cache(self) -> None:
        if self._has_cuda and self._torch:
            self._torch.cuda.empty_cache()

    def ipc_collect(self) -> None:
        if self._has_cuda and self._torch:
            self._torch.cuda.ipc_collect()

    def gc_collect(self) -> None:
        gc.collect()


class ModelSwapper:
    """Automate de permutation à chaud de modèles lourds en VRAM."""

    def __init__(
        self,
        cuda_manager: Any = None,
        loader_factory: Callable[[str], Any] | None = None,
        idle_timeout_seconds: float = 300.0,
    ) -> None:
        self.cuda_manager = cuda_manager or DefaultCudaManager()
        self.loader_factory = loader_factory or self._default_loader
        self.idle_timeout_seconds = idle_timeout_seconds

        self.state: ModelSwapperState = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
        self.active_model: str | None = None
        self.vram_allocated_gb: float = 0.0
        self.pipeline_ready: bool = False

        self._pipeline: Any = None
        self._lock = asyncio.Lock()
        self._idle_task: asyncio.Task[None] | None = None

    def _default_loader(self, model_id: str) -> dict[str, Any]:
        """Chargeur par défaut simulant une pipeline prête."""
        return {"model_id": model_id, "ready": True}

    def _cancel_idle_timer(self) -> None:
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
        self._idle_task = None

    def _arm_idle_timer(self) -> None:
        self._cancel_idle_timer()

        async def _idle_evict() -> None:
            try:
                await asyncio.sleep(self.idle_timeout_seconds)
                async with self._lock:
                    if self.state == ModelSwapperState.MODELE_ACTIF:
                        logger.info("Inactivité GPU dépassée : démarrage de l'éviction VRAM.")
                        self._evict_sync()
                        self.state = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
            except asyncio.CancelledError:
                pass

        self._idle_task = asyncio.create_task(_idle_evict())

    def _evict_sync(self) -> None:
        """Séquence stricte d'éviction mémoire CUDA."""
        self.state = ModelSwapperState.EVICTION_VRAM_EN_COURS
        self._pipeline = None
        self.active_model = None
        self.pipeline_ready = False
        self.vram_allocated_gb = 0.0

        self.cuda_manager.gc_collect()
        self.cuda_manager.empty_cache()
        self.cuda_manager.ipc_collect()

    def _emergency_purge(self) -> None:
        """Purge d'urgence en cas de saturation OOM."""
        self.state = ModelSwapperState.EN_RECUPERATION_SATURATION
        logger.error("CUDA Out of Memory détecté : purge d'urgence de la VRAM.")
        self._evict_sync()
        self.state = ModelSwapperState.EN_VEILLE_VRAM_LIBRE

    async def acquire_model(
        self,
        model_id: str,
        on_progress: Callable[[int], None] | None = None,
    ) -> Any:
        """Acquiert le modèle demandé, réutilise si déjà actif ou permute à chaud."""
        async with self._lock:
            self._cancel_idle_timer()

            # 1. Cache hit : modèle déjà résident en VRAM
            if self.state == ModelSwapperState.MODELE_ACTIF and self.active_model == model_id:
                if on_progress:
                    on_progress(100)
                self._arm_idle_timer()
                return self._pipeline

            # 2. Éviction si un autre modèle est résident
            if self.active_model is not None and self.active_model != model_id:
                logger.info(f"Éviction du modèle {self.active_model} pour charger {model_id}")
                self._evict_sync()

            # 3. Chargement du nouveau modèle
            self.state = ModelSwapperState.CHARGEMENT_EN_COURS
            if on_progress:
                on_progress(0)

            try:
                # Simulation ou appel réel du loader
                if asyncio.iscoroutinefunction(self.loader_factory):
                    pipeline = await self.loader_factory(model_id)
                else:
                    pipeline = self.loader_factory(model_id)

                self._pipeline = pipeline
                self.active_model = model_id
                self.pipeline_ready = True
                self.state = ModelSwapperState.MODELE_ACTIF

                if on_progress:
                    on_progress(100)

                self._arm_idle_timer()
                return self._pipeline

            except Exception as e:
                # Détection d'une exception CUDA OOM
                is_oom = isinstance(e, CudaOutOfMemoryError) or "out of memory" in str(e).lower()
                if is_oom:
                    self._emergency_purge()
                    raise CudaOutOfMemoryError(str(e)) from e
                self._evict_sync()
                self.state = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
                raise

    def notify_inference_completed(self) -> None:
        """Notifie que l'inférence est terminée pour réarmer le timer d'inactivité."""
        if self.state == ModelSwapperState.MODELE_ACTIF:
            self._arm_idle_timer()

    def get_status(self) -> dict[str, Any]:
        """Retourne le diagnostic mémoire et l'état courant."""
        return {
            "state": self.state.value,
            "activeModel": self.active_model,
            "pipelineReady": self.pipeline_ready,
            "vramAllocatedGb": self.vram_allocated_gb,
        }
