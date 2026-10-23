"""Adaptateur d'inférence ComfyUI pour le worker local (app/local_worker/backends/comfyui.py).

Gère :
- L'injection de paramètres utilisateur dans les gabarits de workflow ComfyUI.
- La soumission de prompts POST /prompt.
- L'interrogation de progression et d'achèvement GET /history/{prompt_id}.
- L'interruption immédiate POST /interrupt.
- La récupération des binaires générés GET /view.
"""

from __future__ import annotations

import copy
from typing import Any

import httpx


class ComfyUIBackend:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        client: httpx.AsyncClient | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client
        self.timeout = timeout

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=self.timeout)

    def inject_parameters(
        self,
        workflow_template: dict[str, Any],
        bindings: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        workflow = copy.deepcopy(workflow_template)
        for param_key, target_path in bindings.items():
            if param_key in params and isinstance(target_path, list) and len(target_path) >= 2:
                current: Any = workflow
                # Traverse tous les éléments sauf le dernier
                for node_id in target_path[:-1]:
                    if isinstance(current, dict) and str(node_id) in current:
                        current = current[str(node_id)]
                    else:
                        current = None
                        break
                if current is not None and isinstance(current, dict):
                    last_key = str(target_path[-1])
                    current[last_key] = params[param_key]
        return workflow

    async def queue_prompt(self, workflow_prompt: dict[str, Any]) -> str:
        client = self._get_client()
        try:
            res = await client.post(f"{self.base_url}/prompt", json={"prompt": workflow_prompt})
            res.raise_for_status()
            data = res.json()
            return str(data.get("prompt_id"))
        finally:
            if self._client is None:
                await client.aclose()

    async def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        client = self._get_client()
        try:
            res = await client.get(f"{self.base_url}/history/{prompt_id}")
            if res.status_code == 200:
                history_data = res.json()
                if isinstance(history_data, dict) and prompt_id in history_data:
                    val = history_data[prompt_id]
                    return val if isinstance(val, dict) else None
            return None
        finally:
            if self._client is None:
                await client.aclose()

    async def interrupt(self) -> bool:
        client = self._get_client()
        try:
            res = await client.post(f"{self.base_url}/interrupt")
            return res.status_code == 200
        except Exception:
            return False
        finally:
            if self._client is None:
                await client.aclose()
