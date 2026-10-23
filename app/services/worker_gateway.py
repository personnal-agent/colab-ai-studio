"""Passerelle unifiée d'accès au worker actif (app/services/worker_gateway.py).

Garantit le contrat unique de worker pour Colab AI Studio :
- Sélection dynamique à chaud du worker actif selon config.json (colab vs local).
- Diagnostics de santé avec mesure de latence et remontée VRAM.
- Relais des appels modèles, inférence et gestion des tâches distantes.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import CONFIG_FILE
from app.models.domain import ExecutionMode, StudioConfig
from app.storage.json_store import JSONDocumentStore


class WorkerGatewayError(Exception):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class WorkerGateway:
    def __init__(
        self,
        store: JSONDocumentStore,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.store = store
        self._client = client
        self.timeout = timeout

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=self.timeout)

    async def get_active_worker_url(self) -> tuple[ExecutionMode, str]:
        raw_config = await self.store.read_dict(
            CONFIG_FILE.name, default=StudioConfig().model_dump()
        )
        config = StudioConfig.model_validate(raw_config)

        if config.executionMode == ExecutionMode.COLAB:
            tunnel_url = config.colab.tunnelUrl.strip()
            if not tunnel_url or tunnel_url.startswith("https://xxxx"):
                msg = (
                    "Worker Colab non configuré : URL de tunnel publique "
                    "manquante ou invalide dans config.json."
                )
                raise WorkerGatewayError(msg, status_code=503)
            return ExecutionMode.COLAB, tunnel_url.rstrip("/")

        # Mode Local
        local_url = config.local.workerUrl.strip()
        if not local_url:
            msg = "Worker local non configuré : workerUrl manquante dans config.json."
            raise WorkerGatewayError(msg, status_code=503)
        return ExecutionMode.LOCAL, local_url.rstrip("/")

    async def check_worker_health(self) -> dict[str, Any]:
        try:
            mode, base_url = await self.get_active_worker_url()
        except WorkerGatewayError as e:
            return {
                "reachable": False,
                "executionMode": "unconfigured",
                "error": str(e),
            }

        client = self._get_client()
        start = time.perf_counter()
        health_url = f"{base_url}/health"
        try:
            res = await client.get(health_url)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            if res.status_code == 200:
                payload = res.json()
                return {
                    "reachable": True,
                    "executionMode": mode.value,
                    "latencyMs": elapsed_ms,
                    "gpu": payload.get("gpu"),
                    "vramFreeMb": payload.get("vramFreeMb"),
                    "workerStatus": payload.get("status", "ok"),
                }
            return {
                "reachable": False,
                "executionMode": mode.value,
                "latencyMs": elapsed_ms,
                "error": f"Statut HTTP inattendu {res.status_code} depuis {health_url}",
            }
        except httpx.RequestError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "reachable": False,
                "executionMode": mode.value,
                "latencyMs": elapsed_ms,
                "error": f"Worker {mode.value} injoignable sur {base_url} ({exc})",
            }
        finally:
            if self._client is None:
                await client.aclose()

    async def list_models(self) -> list[dict[str, Any]]:
        mode, base_url = await self.get_active_worker_url()
        client = self._get_client()
        try:
            res = await client.get(f"{base_url}/models")
            if res.status_code != 200:
                msg = (
                    f"Erreur {res.status_code} lors de la récupération des modèles "
                    f"depuis {base_url}"
                )
                raise WorkerGatewayError(msg, status_code=res.status_code)
            data = res.json()
            return data if isinstance(data, list) else []
        except httpx.RequestError as exc:
            msg = f"Worker {mode.value} injoignable sur {base_url} : {exc}"
            raise WorkerGatewayError(msg, status_code=503) from exc
        finally:
            if self._client is None:
                await client.aclose()

    async def switch_model(self, model_id: str) -> dict[str, Any]:
        mode, base_url = await self.get_active_worker_url()
        client = self._get_client()
        try:
            res = await client.post(f"{base_url}/models/switch", json={"modelId": model_id})
            if res.status_code != 200:
                msg = f"Erreur {res.status_code} lors du changement de modèle sur {base_url}"
                raise WorkerGatewayError(msg, status_code=res.status_code)
            return res.json()
        except httpx.RequestError as exc:
            msg = f"Worker {mode.value} injoignable sur {base_url} : {exc}"
            raise WorkerGatewayError(msg, status_code=503) from exc
        finally:
            if self._client is None:
                await client.aclose()
