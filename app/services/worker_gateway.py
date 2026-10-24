"""Passerelle de communication unifiée vers le worker actif (app/services/worker_gateway.py).

Gère la bascule dynamique à chaud entre Colab et Local Runner selon Issue #2 et SPECIFICATION.md.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import CONFIG_FILE, DATA_DIR
from app.models.domain import ExecutionMode, StudioConfig
from app.storage.json_store import JSONDocumentStore

logger = logging.getLogger(__name__)


class WorkerGatewayError(Exception):
    """Erreur générique de la passerelle de worker."""


class WorkerNotConfiguredError(WorkerGatewayError):
    """Levée quand le worker actif n'a pas d'URL configurée valide."""


class WorkerUnavailableError(WorkerGatewayError):
    """Levée quand le worker actif ne répond pas ou est hors ligne."""


class WorkerGateway:
    """Passerelle asynchrone unifiée vers le worker de calcul (Colab ou Local)."""

    def __init__(
        self,
        json_store: JSONDocumentStore | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._json_store = json_store or JSONDocumentStore(DATA_DIR)
        self._custom_client = http_client is not None
        self._http_client = http_client or httpx.AsyncClient(timeout=10.0)

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Accès contrôlé au client HTTP asynchrone."""
        return self._http_client

    async def aclose(self) -> None:
        """Ferme les ressources réseau associées si créées en interne."""
        if not self._custom_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_active_worker_url(self) -> tuple[str, str]:
        """Résout dynamiquement le mode actif et l'URL de base du worker."""
        cfg_dict = await self._json_store.read_dict(
            CONFIG_FILE.name, default=StudioConfig().model_dump()
        )
        cfg = StudioConfig.model_validate(cfg_dict)

        if cfg.executionMode == ExecutionMode.COLAB:
            if not cfg.colab.is_connected():
                raise WorkerNotConfiguredError(
                    "Worker Colab non configuré (tunnelUrl manquant ou invalide)"
                )
            return "colab", cfg.colab.tunnelUrl.rstrip("/")

        if cfg.executionMode == ExecutionMode.LOCAL:
            url = cfg.local.workerUrl.strip() if cfg.local.workerUrl else ""
            if not url:
                raise WorkerNotConfiguredError("Worker Local non configuré (workerUrl manquant)")
            return "local", url.rstrip("/")

        raise WorkerNotConfiguredError(f"Mode d'exécution inconnu : {cfg.executionMode}")

    async def health(self) -> dict[str, Any]:
        """Contrôle la santé et la latence du worker actif sans bloquer."""
        try:
            mode, base_url = await self.get_active_worker_url()
        except WorkerNotConfiguredError as e:
            return {
                "executionMode": "unconfigured",
                "worker": {
                    "reachable": False,
                    "latencyMs": None,
                    "gpu": None,
                    "vramFreeMb": None,
                    "error": str(e),
                },
            }

        t0 = time.perf_counter()
        try:
            resp = await self._http_client.get(f"{base_url}/health", timeout=3.0)
            resp.raise_for_status()
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
            data = resp.json() if resp.content else {}
            return {
                "executionMode": mode,
                "worker": {
                    "reachable": True,
                    "latencyMs": latency_ms,
                    "gpu": data.get("gpu"),
                    "vramFreeMb": data.get("vramFreeMb"),
                    "error": None,
                },
            }
        except Exception as e:
            logger.debug("Échec du health check worker sur %s : %s", base_url, e)
            return {
                "executionMode": mode,
                "worker": {
                    "reachable": False,
                    "latencyMs": None,
                    "gpu": None,
                    "vramFreeMb": None,
                    "error": str(e),
                },
            }

    async def list_models(self) -> list[dict[str, Any]]:
        """Interroge le catalogue des modèles du worker actif."""
        mode, base_url = await self.get_active_worker_url()
        try:
            resp = await self._http_client.get(f"{base_url}/models", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return data.get("models", [])
        except httpx.HTTPError as e:
            logger.warning("Erreur communication modèles avec %s (%s): %s", mode, base_url, e)
            raise WorkerUnavailableError(f"Worker {mode} inaccessible sur {base_url} : {e}") from e

    async def switch_model(self, model_id: str) -> dict[str, Any]:
        """Bascule le modèle actif en VRAM sur le worker distant ou local."""
        mode, base_url = await self.get_active_worker_url()
        try:
            resp = await self._http_client.post(
                f"{base_url}/models/switch",
                json={"modelId": model_id},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Erreur switch_model sur %s (%s): %s", mode, base_url, e)
            raise WorkerUnavailableError(f"Échec de bascule modèle sur {mode} : {e}") from e

    async def infer(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """Soumet une tâche d'inférence au worker."""
        mode, base_url = await self.get_active_worker_url()
        try:
            resp = await self._http_client.post(
                f"{base_url}/infer",
                json=task_spec,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise WorkerUnavailableError(f"Échec soumission inférence sur {mode} : {e}") from e

    async def get_task_status(self, task_id: str, base_url: str | None = None) -> dict[str, Any]:
        """Récupère l'avancement d'une tâche auprès du worker."""
        if not base_url:
            mode, base_url = await self.get_active_worker_url()
        else:
            mode = "assigned_worker"
        try:
            resp = await self._http_client.get(
                f"{base_url}/tasks/{task_id}/status",
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise WorkerUnavailableError(f"Échec suivi tâche {task_id} sur {mode} : {e}") from e

    async def cancel_task(self, task_id: str, base_url: str | None = None) -> dict[str, Any]:
        """Notifie le worker d'interrompre immédiatement la tâche."""
        if not base_url:
            mode, base_url = await self.get_active_worker_url()
        else:
            mode = "assigned_worker"
        try:
            resp = await self._http_client.post(
                f"{base_url}/tasks/{task_id}/cancel",
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Échec notification annulation tâche %s vers %s : %s", task_id, mode, e)
            return {"status": "cancelled", "remoteError": str(e)}

    async def download_file(self, file_path_or_url: str, base_url: str | None = None) -> bytes:
        """Télécharge un artéfact binaire produit par le worker avec protection anti-SSRF."""
        if not base_url:
            _, base_url = await self.get_active_worker_url()

        parsed_base = httpx.URL(base_url)
        if file_path_or_url.startswith(("http://", "https://")):
            parsed_target = httpx.URL(file_path_or_url)
            if (
                parsed_target.scheme != parsed_base.scheme
                or parsed_target.host != parsed_base.host
                or parsed_target.port != parsed_base.port
            ):
                msg = (
                    f"Accès refusé : l'artéfact {file_path_or_url} n'appartient pas au worker "
                    f"({parsed_base.scheme}://{parsed_base.host})"
                )
                raise ValueError(msg)
            url = str(parsed_target)
        else:
            clean_path = file_path_or_url.lstrip("/")
            if ".." in clean_path:
                raise ValueError("Chemin d'artéfact interdit (path traversal détecté)")
            url = f"{base_url}/files/{clean_path}"

        try:
            resp = await self._http_client.get(url, timeout=60.0)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPError as e:
            raise WorkerUnavailableError(f"Échec téléchargement artéfact {url} : {e}") from e
