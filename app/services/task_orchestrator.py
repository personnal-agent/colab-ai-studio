"""Orchestrateur de tâches asynchrones et flux SSE (app/services/task_orchestrator.py).

Gère le cycle de vie complet des générations multimédia (06-sequence-generation.svg) :
- Soumission asynchrone avec compilation optionnelle Brand Kit.
- Inférence déportée via WorkerGateway.
- Suivi de progression et diffusion Server-Sent Events (SSE).
- Rapatriement local via MediaFileStore et isolation de stockage.
- Annulation idempotente propageant l'arrêt au worker.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import (
    BrandKit,
    Generation,
    GenerationParameters,
    GenerationReferences,
    Project,
    TaskStatus,
)
from app.services.brand_compiler import BrandContextCompiler
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore
from app.storage.media_store import MediaFileStore


class GenerationPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mediaType: str = "video"
    prompt: str
    negativePrompt: str | None = None
    modelId: str
    modelName: str
    parameters: GenerationParameters
    references: GenerationReferences = Field(default_factory=GenerationReferences)
    projectId: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TaskOrchestrator:
    def __init__(
        self,
        json_store: JSONDocumentStore,
        media_store: MediaFileStore,
        gateway: WorkerGateway,
        brand_compiler: BrandContextCompiler,
        poll_interval: float = 0.5,
        timeout: float = 120.0,
    ) -> None:
        self.json_store = json_store
        self.media_store = media_store
        self.gateway = gateway
        self.brand_compiler = brand_compiler
        self.poll_interval = poll_interval
        self.timeout = timeout

        self._active_worker_tasks: dict[str, str] = {}  # gen_id -> worker_task_id
        self._listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def submit_generation(self, payload: GenerationPayload) -> Generation:
        timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        gen_id = f"gen_{timestamp_slug}_{uuid.uuid4().hex[:4]}"

        compiled_prompt = payload.prompt
        negative_prompt = payload.negativePrompt
        snapshot = None

        # 1. Compilation de marque si un Brand Kit est spécifié
        if payload.references.brandKitId:
            kits = await self.json_store.read_list("brand_kits.json")
            for k in kits:
                if k.get("id") == payload.references.brandKitId:
                    kit_obj = BrandKit.model_validate(k)
                    compiled_res = await self.brand_compiler.compile(
                        prompt=payload.prompt,
                        kit=kit_obj,
                        user_refs=payload.references.imageRefs,
                    )
                    compiled_prompt = compiled_res.compiled_prompt
                    negative_prompt = compiled_res.negative_prompt
                    snapshot = compiled_res.snapshot
                    break

        gen = Generation(
            id=gen_id,
            status=TaskStatus.PENDING,
            mediaType=payload.mediaType,
            prompt=payload.prompt,
            negativePrompt=negative_prompt,
            compiledPrompt=compiled_prompt,
            modelId=payload.modelId,
            modelName=payload.modelName,
            parameters=payload.parameters,
            references=payload.references,
            brandKitSnapshot=snapshot,
            projectId=payload.projectId,
            createdAt=_utc_now_iso(),
        )

        async with self.json_store.lock_for("generations.json"):
            items = await self.json_store.read_list("generations.json")
            items.append(gen.model_dump())
            await self.json_store.write_list("generations.json", items)

        # Lancement en tâche de fond du cycle de vie
        asyncio.create_task(self._run_task_lifecycle(gen))
        return gen

    async def _broadcast(self, gen_id: str, event_data: dict[str, Any]) -> None:
        async with self._lock:
            queues = self._listeners.get(gen_id, [])
            for q in queues:
                await q.put(event_data)

    async def _update_generation(self, gen_id: str, updates: dict[str, Any]) -> None:
        async with self.json_store.lock_for("generations.json"):
            items = await self.json_store.read_list("generations.json")
            for item in items:
                if item.get("id") == gen_id:
                    item.update(updates)
                    break
            await self.json_store.write_list("generations.json", items)

    async def _run_task_lifecycle(self, gen: Generation) -> None:
        gen_id = gen.id
        client = self.gateway._get_client()

        try:
            _mode, base_url = await self.gateway.get_active_worker_url()
        except Exception as e:
            await self._update_generation(
                gen_id, {"status": TaskStatus.FAILED.value, "errorMessage": str(e)}
            )
            await self._broadcast(
                gen_id, {"taskId": gen_id, "status": TaskStatus.FAILED.value, "error": str(e)}
            )
            return

        infer_payload = {
            "modelId": gen.modelId,
            "prompt": gen.compiledPrompt or gen.prompt,
            "negativePrompt": gen.negativePrompt,
            "parameters": gen.parameters.to_payload_dict(),
            "references": gen.references.model_dump(),
        }

        try:
            res = await client.post(f"{base_url}/infer", json=infer_payload)
            res.raise_for_status()
            worker_data = res.json()
            worker_task_id = worker_data.get("taskId")
            if not worker_task_id:
                raise ValueError("Worker n'a pas retourné de taskId valide")

            self._active_worker_tasks[gen_id] = worker_task_id
            await self._update_generation(
                gen_id, {"status": TaskStatus.RUNNING.value, "progress": 10}
            )
            await self._broadcast(
                gen_id, {"taskId": gen_id, "status": TaskStatus.RUNNING.value, "progress": 10}
            )

            # Polling de l'état du worker
            start_time = asyncio.get_event_loop().time()
            while True:
                # Vérification si annulée localement
                items = await self.json_store.read_list("generations.json")
                cur_item = next((it for it in items if it.get("id") == gen_id), None)
                if cur_item and cur_item.get("status") == TaskStatus.CANCELLED.value:
                    await client.post(f"{base_url}/tasks/{worker_task_id}/cancel")
                    return

                if (asyncio.get_event_loop().time() - start_time) > self.timeout:
                    await self._update_generation(
                        gen_id,
                        {
                            "status": TaskStatus.FAILED.value,
                            "errorMessage": "Délai d'inférence dépassé (Timeout)",
                        },
                    )
                    await self._broadcast(
                        gen_id,
                        {
                            "taskId": gen_id,
                            "status": TaskStatus.FAILED.value,
                            "error": "Timeout d'inférence",
                        },
                    )
                    return

                status_res = await client.get(f"{base_url}/tasks/{worker_task_id}/status")
                if status_res.status_code == 200:
                    status_data = status_res.json()
                    worker_status = status_data.get("status")
                    progress = status_data.get("progress", 50)

                    await self._broadcast(
                        gen_id,
                        {
                            "taskId": gen_id,
                            "status": worker_status,
                            "progress": progress,
                        },
                    )

                    if worker_status == "completed":
                        # Rapatriement du binaire
                        output_filename = status_data.get("outputFilename") or f"{gen_id}.mp4"
                        file_res = await client.get(f"{base_url}/files/{output_filename}")
                        file_res.raise_for_status()

                        # Récupération du projet s'il existe
                        target_project: Project | None = None
                        if gen.projectId:
                            projects = await self.json_store.read_list("projects.json")
                            for p in projects:
                                if p.get("id") == gen.projectId:
                                    target_project = Project.model_validate(p)
                                    break

                        saved_path, thumb_path = await self.media_store.save_media(
                            filename=output_filename,
                            content=file_res.content,
                            project=target_project,
                        )

                        await self._update_generation(
                            gen_id,
                            {
                                "status": TaskStatus.COMPLETED.value,
                                "progress": 100,
                                "filePath": saved_path,
                                "thumbnailPath": thumb_path,
                            },
                        )
                        await self._broadcast(
                            gen_id,
                            {
                                "taskId": gen_id,
                                "status": TaskStatus.COMPLETED.value,
                                "progress": 100,
                                "filePath": saved_path,
                            },
                        )
                        return

                    if worker_status in {"failed", "cancelled"}:
                        await self._update_generation(
                            gen_id,
                            {
                                "status": worker_status,
                                "errorMessage": status_data.get("error", "Erreur worker"),
                            },
                        )
                        return

                await asyncio.sleep(self.poll_interval)

        except Exception as exc:
            await self._update_generation(
                gen_id,
                {"status": TaskStatus.FAILED.value, "errorMessage": str(exc)},
            )
            await self._broadcast(
                gen_id,
                {"taskId": gen_id, "status": TaskStatus.FAILED.value, "error": str(exc)},
            )

    async def cancel_generation(self, gen_id: str) -> Generation:
        items = await self.json_store.read_list("generations.json")
        target_item = next((it for it in items if it.get("id") == gen_id), None)
        if not target_item:
            msg = f"Génération {gen_id} introuvable"
            raise ValueError(msg)

        # Idempotence : si déjà annulée ou terminée
        if target_item.get("status") == TaskStatus.CANCELLED.value:
            return Generation.model_validate(target_item)

        await self._update_generation(
            gen_id,
            {"status": TaskStatus.CANCELLED.value, "progress": 0},
        )
        await self._broadcast(
            gen_id,
            {"taskId": gen_id, "status": TaskStatus.CANCELLED.value, "progress": 0},
        )

        worker_task_id = self._active_worker_tasks.get(gen_id)
        if worker_task_id:
            with contextlib.suppress(Exception):
                _, base_url = await self.gateway.get_active_worker_url()
                client = self.gateway._get_client()
                await client.post(f"{base_url}/tasks/{worker_task_id}/cancel")

        updated_items = await self.json_store.read_list("generations.json")
        refreshed = next(it for it in updated_items if it.get("id") == gen_id)
        return Generation.model_validate(refreshed)

    async def register_listener(self, gen_id: str) -> asyncio.Queue[dict[str, Any]]:
        async with self._lock:
            if gen_id not in self._listeners:
                self._listeners[gen_id] = []
            q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
            self._listeners[gen_id].append(q)
            return q

    async def unregister_listener(self, gen_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            if gen_id in self._listeners:
                with contextlib.suppress(ValueError):
                    self._listeners[gen_id].remove(queue)
                if not self._listeners[gen_id]:
                    del self._listeners[gen_id]
