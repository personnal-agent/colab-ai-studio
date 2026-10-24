"""Automate ModelSwapper et protocole d'éviction VRAM GPU (app/colab_worker/model_swapper.py).

Conforme à 11-etats-model-swapper.svg et SPECIFICATION.md §5.1 :
- Gestion rigoureuse de la VRAM GPU T4 16 Go : un seul modèle lourd résident à la fois.
- Éviction complète séquentielle (del, gc.collect, empty_cache, ipc_collect).
- Réutilisation directe à chaud sans réallocation si le modèle requis est résident.
- Transition autonome EnRecuperationSaturation sur CUDA OOM avec purge et retour en veille.
- Éviction automatique sur inactivité (idle timeout).
"""

from __future__ import annotations

import gc
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    torch: Any = None
    TORCH_AVAILABLE = False


class CUDAOutOfMemoryError(RuntimeError):
    """Exception levée en cas de saturation de la mémoire VRAM GPU."""


class ModelSwapperError(Exception):
    """Exception racine pour les erreurs du ModelSwapper."""


class ModelSwapperOOMError(ModelSwapperError):
    """Levée quand une allocation échoue par manque de VRAM."""


class ModelSwapperState(str, Enum):
    """États canoniques définis dans 11-etats-model-swapper.svg."""

    EN_VEILLE_VRAM_LIBRE = "EnVeilleVRAMLibre"
    CHARGEMENT_EN_COURS = "ChargementEnCours"
    MODELE_ACTIF = "ModeleActif"
    EVICTION_VRAM_EN_COURS = "EvictionVRAMEnCours"
    EN_RECUPERATION_SATURATION = "EnRecuperationSaturation"
    ARRETE = "Arrete"


class DefaultCudaBackend:
    """Interface d'interaction réelle avec torch.cuda ou repli propre sans crash."""

    def is_available(self) -> bool:
        return bool(TORCH_AVAILABLE and torch and torch.cuda.is_available())

    def empty_cache(self) -> None:
        if self.is_available() and torch:
            torch.cuda.empty_cache()

    def ipc_collect(self) -> None:
        if self.is_available() and torch and hasattr(torch.cuda, "ipc_collect"):
            torch.cuda.ipc_collect()

    def memory_allocated(self, device: int | None = None) -> int:
        if self.is_available() and torch:
            return torch.cuda.memory_allocated(device)
        return 0

    def get_device_name(self, device: int | None = None) -> str:
        if self.is_available() and torch:
            return torch.cuda.get_device_name(device)
        return "CPU / Host (GPU non détecté)"


class ModelSwapper:
    """Automate d'état pilotant la permutation de modèles en VRAM GPU."""

    def __init__(
        self,
        cuda_backend: Any | None = None,
        idle_timeout_seconds: float = 300.0,
    ) -> None:
        self.cuda_backend = cuda_backend or DefaultCudaBackend()
        self.idle_timeout_seconds = idle_timeout_seconds

        self.state: ModelSwapperState = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
        self.active_model: str | None = None
        self.active_pipeline: Any | None = None
        self.pipeline_ready: bool = False
        self.vram_allocated_gb: float = 0.0
        self.last_activity_time: float = time.time()

    def initialize(self) -> None:
        """Réinitialise l'automate dans l'état initial EnVeilleVRAMLibre."""
        self.state = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
        self.active_model = None
        self.active_pipeline = None
        self.pipeline_ready = False
        self.vram_allocated_gb = 0.0
        self.last_activity_time = time.time()

    def evict_vram(self) -> None:
        """Protocole strict d'éviction mémoire VRAM."""
        self.state = ModelSwapperState.EVICTION_VRAM_EN_COURS
        logger.info("Début d'éviction mémoire VRAM pour le modèle : %s", self.active_model)

        if self.active_pipeline is not None:
            del self.active_pipeline
            self.active_pipeline = None

        self.active_model = None
        self.pipeline_ready = False
        self.vram_allocated_gb = 0.0

        # Purge complète du ramasse-miettes et des caches CUDA
        gc.collect()
        self.cuda_backend.empty_cache()
        self.cuda_backend.ipc_collect()

        self.state = ModelSwapperState.EN_VEILLE_VRAM_LIBRE
        logger.info("Éviction VRAM terminée. Automate en veille (EnVeilleVRAMLibre).")

    def ensure_model(
        self,
        model_id: str,
        load_fn: Callable[[str], Any] | None = None,
        on_progress: Callable[[float], None] | None = None,
    ) -> Any:
        """Garantit qu'un modèle donné est chargé et prêt en VRAM.

        - Si le modèle requis est déjà résident, réutilisation immédiate.
        - Sinon, éviction complète préalable puis chargement.
        - Récupération robuste en cas de CUDA OOM.
        """
        now = time.time()

        # 1. Vérification de réutilisation directe
        if (
            self.active_model == model_id
            and self.pipeline_ready
            and self.active_pipeline is not None
        ):
            self.last_activity_time = now
            if on_progress:
                on_progress(1.0)
            return self.active_pipeline

        # 2. Si un autre modèle est déjà résident, éviction préalable
        if self.active_model is not None or self.active_pipeline is not None:
            self.evict_vram()

        # 3. Transition vers ChargementEnCours
        self.state = ModelSwapperState.CHARGEMENT_EN_COURS
        if on_progress:
            on_progress(0.0)

        loader = load_fn or (lambda mid: {"model_id": mid, "loaded_at": time.time()})

        try:
            if on_progress:
                on_progress(0.5)

            pipeline = loader(model_id)

            self.active_model = model_id
            self.active_pipeline = pipeline
            self.pipeline_ready = True
            self.last_activity_time = time.time()
            self.vram_allocated_gb = round(
                self.cuda_backend.memory_allocated() / (1024**3), 2
            )
            self.state = ModelSwapperState.MODELE_ACTIF

            if on_progress:
                on_progress(1.0)

            return pipeline

        except (CUDAOutOfMemoryError, MemoryError) as oom_err:
            logger.error("CUDA OOM détecté lors du chargement de %s : %s", model_id, oom_err)
            self.state = ModelSwapperState.EN_RECUPERATION_SATURATION
            self.evict_vram()
            raise ModelSwapperOOMError(f"Saturation VRAM CUDA : {oom_err}") from oom_err
        except Exception as err:
            if "out of memory" in str(err).lower() or "cuda oom" in str(err).lower():
                logger.error("CUDA OOM détecté lors du chargement de %s : %s", model_id, err)
                self.state = ModelSwapperState.EN_RECUPERATION_SATURATION
                self.evict_vram()
                raise ModelSwapperOOMError(f"Saturation VRAM CUDA : {err}") from err
            self.evict_vram()
            raise

    def check_idle_timeout(self, now: float | None = None) -> bool:
        """Vérifie si le modèle actif a dépassé le délai d'inactivité et libère la VRAM."""
        current_time = now if now is not None else time.time()
        if self.state == ModelSwapperState.MODELE_ACTIF:
            idle_duration = current_time - self.last_activity_time
            if idle_duration >= self.idle_timeout_seconds:
                logger.info(
                    "Délai d'inactivité atteint (%.1fs >= %.1fs). Éviction VRAM.",
                    idle_duration,
                    self.idle_timeout_seconds,
                )
                self.evict_vram()
                return True
        return False

    def stop(self) -> None:
        """Arrête le swapper et libère toutes les ressources."""
        self.evict_vram()
        self.state = ModelSwapperState.ARRETE

    def get_telemetry(self) -> dict[str, Any]:
        """Génère un dictionnaire de télémétrie conforme pour les endpoints de diagnostic."""
        free_mb = 16384.0 - (self.vram_allocated_gb * 1024.0)
        return {
            "state": self.state.value,
            "activeModel": self.active_model,
            "pipelineReady": self.pipeline_ready,
            "vramAllocatedGb": self.vram_allocated_gb,
            "vramFreeMb": max(0.0, free_mb),
            "gpu": self.cuda_backend.get_device_name(),
        }
