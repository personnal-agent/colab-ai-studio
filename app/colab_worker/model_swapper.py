"""Automate ModelSwapper et protocole d'éviction VRAM GPU (app/colab_worker/model_swapper.py).

Conforme à 11-etats-model-swapper.svg et SPECIFICATION.md §5.1 :
- Gestion rigoureuse de la VRAM GPU T4 16 Go : un seul modèle lourd résident à la fois.
- Éviction complète séquentielle (del, gc.collect, empty_cache, ipc_collect).
- Réutilisation directe à chaud sans réallocation si le modèle requis est résident.
- Transition autonome EnRecuperationSaturation sur CUDA OOM avec purge et retour en veille.
- Éviction automatique sur inactivité (idle timeout).
"""

from __future__ import annotations

import contextlib
import gc
import logging
import shutil
import subprocess
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

    def _query_nvidia_smi(self) -> tuple[str, float] | None:
        """Tente de détecter le GPU et la VRAM via nvidia-smi si torch.cuda n'est pas dispo."""
        wsl_local_smi = "/home/instructeur/.local/lib/wsl/nvidia-smi"
        smi_bin = (
            wsl_local_smi
            if shutil.which(wsl_local_smi) or shutil.os.path.exists(wsl_local_smi)
            else (shutil.which("nvidia-smi") or "/usr/lib/wsl/lib/nvidia-smi")
        )
        with contextlib.suppress(Exception):
            env = shutil.os.environ.copy()
            env["LD_LIBRARY_PATH"] = (
                f"/home/instructeur/.local/lib/wsl:{env.get('LD_LIBRARY_PATH', '')}"
            )
            out = subprocess.check_output(
                [smi_bin, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                text=True,
                timeout=2,
                env=env,
            ).strip()
            if out:
                parts = [p.strip() for p in out.split(",")]
                name = parts[0]
                total_mb = float(parts[1]) if len(parts) > 1 else 16384.0
                return name, total_mb
        return None

    def is_available(self) -> bool:
        if bool(TORCH_AVAILABLE and torch and torch.cuda.is_available()):
            return True
        return self._query_nvidia_smi() is not None

    def empty_cache(self) -> None:
        if bool(TORCH_AVAILABLE and torch and torch.cuda.is_available()):
            torch.cuda.empty_cache()

    def ipc_collect(self) -> None:
        has_ipc = hasattr(torch.cuda, "ipc_collect") if TORCH_AVAILABLE and torch else False
        if bool(TORCH_AVAILABLE and torch and torch.cuda.is_available()) and has_ipc:
            torch.cuda.ipc_collect()

    def memory_allocated(self, device: int | None = None) -> int:
        has_cuda = bool(TORCH_AVAILABLE and torch and torch.cuda.is_available())
        return torch.cuda.memory_allocated(device) if has_cuda else 0

    def get_device_name(self, device: int | None = None) -> str:
        if bool(TORCH_AVAILABLE and torch and torch.cuda.is_available()):
            return torch.cuda.get_device_name(device)
        smi = self._query_nvidia_smi()
        if smi:
            return smi[0]
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
            self.vram_allocated_gb = round(self.cuda_backend.memory_allocated() / (1024**3), 2)
            self.state = ModelSwapperState.MODELE_ACTIF

            if on_progress:
                on_progress(1.0)

            return pipeline

        except Exception as err:
            is_oom = isinstance(err, (CUDAOutOfMemoryError, MemoryError)) or any(
                k in str(err).lower() for k in ("out of memory", "cuda oom")
            )
            if is_oom:
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
        total_mb = 16384.0
        if hasattr(self.cuda_backend, "_query_nvidia_smi"):
            smi = self.cuda_backend._query_nvidia_smi()
            if smi:
                total_mb = smi[1]
        free_mb = total_mb - (self.vram_allocated_gb * 1024.0)
        return {
            "state": self.state.value,
            "activeModel": self.active_model,
            "pipelineReady": self.pipeline_ready,
            "vramAllocatedGb": self.vram_allocated_gb,
            "vramFreeMb": max(0.0, free_mb),
            "gpu": self.cuda_backend.get_device_name(),
        }
