"""Orchestrateur de tâches asynchrones et flux SSE (app/services/task_orchestrator.py).

Gère le cycle de vie des tâches de génération multimédia :
pending -> running -> completed / cancelled / failed.
Diffuse les événements temps réel via SSE et synchronise les médias via MediaFileStore.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel, Field

from app.config import BRAND_KITS_FILE, DATA_DIR, GENERATIONS_FILE, OUTPUTS_DIR, PROJECTS_FILE
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

logger = logging.getLogger(__name__)


class GenerationCreateRequest(BaseModel):
    prompt: str
    negativePrompt: str | None = None
    modelId: str
    modelName: str | None = None
    type: str = "video"
    parameters: GenerationParameters = Field(default_factory=lambda: GenerationParameters(seed=0))
    references: GenerationReferences = Field(default_factory=GenerationReferences)
    brandKitId: str | None = None
    projectId: str | None = None


class TaskOrchestrator:
    """Service d'orchestration asynchrone des générations et diffusion SSE."""

    def __init__(
        self,
        json_store: JSONDocumentStore | None = None,
        media_store: MediaFileStore | None = None,
        worker_gateway: WorkerGateway | None = None,
        brand_compiler: BrandContextCompiler | None = None,
        poll_interval: float = 1.0,
        task_timeout: float = 120.0,
    ) -> None:
        self._json_store = json_store or JSONDocumentStore(DATA_DIR)
        self._media_store = media_store or MediaFileStore(OUTPUTS_DIR)
        self._gateway = worker_gateway or WorkerGateway(self._json_store)
        self._compiler = brand_compiler or BrandContextCompiler()
        self._poll_interval = poll_interval
        self._task_timeout = task_timeout

        self._active_tasks: dict[str, asyncio.Task[None]] = {}
        self._listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._cancel_events: dict[str, asyncio.Event] = {}

    async def submit_generation(self, req: GenerationCreateRequest) -> Generation:
        """Crée une tâche de génération, compile la marque si demandée et lance le worker."""
        kit: BrandKit | None = None
        if req.brandKitId:
            kits = await self._json_store.read_list(BRAND_KITS_FILE.name)
            match = next((k for k in kits if k.get("id") == req.brandKitId), None)
            if match:
                kit = BrandKit.model_validate(match)

        # Compilation du Brand Kit
        compiled = await self._compiler.compile(
            prompt=req.prompt,
            brand_kit=kit,
            user_refs=req.references.imageRefs,
            max_image_refs=4,
        )

        gen_id = f"gen_{uuid.uuid4().hex[:10]}"
        refs = req.references.model_copy()
        if compiled.image_refs:
            refs.imageRefs = compiled.image_refs

        gen = Generation(
            id=gen_id,
            status=TaskStatus.PENDING,
            mediaType=req.type,
            prompt=req.prompt,
            negativePrompt=req.negativePrompt or compiled.negative_prompt,
            compiledPrompt=compiled.prompt,
            modelId=req.modelId,
            modelName=req.modelName or req.modelId,
            parameters=req.parameters,
            references=refs,
            brandKitSnapshot=compiled.snapshot,
            projectId=req.projectId,
            progress=0,
        )

        async with self._json_store.lock_for(GENERATIONS_FILE.name):
            gens = await self._json_store.read_list_unlocked(GENERATIONS_FILE.name)
            gens.insert(0, gen.model_dump())
            await self._json_store.write_list_unlocked(GENERATIONS_FILE.name, gens)

        self._cancel_events[gen_id] = asyncio.Event()
        bg_task = asyncio.create_task(self._run_task(gen_id, req, gen))
        self._active_tasks[gen_id] = bg_task

        return gen

    async def wait_task(self, task_id: str, timeout: float = 10.0) -> None:
        """Attente de fin d'une tâche de fond (utilitaire de synchronisation)."""
        task = self._active_tasks.get(task_id)
        if task:
            with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout)

    async def _emit_event(self, task_id: str, event: dict[str, Any]) -> None:
        """Diffuse un événement à tous les clients abonnés au flux SSE de cette tâche."""
        for queue in list(self._listeners.get(task_id, [])):
            await queue.put(event)

    async def _update_generation(self, gen_id: str, **kwargs: Any) -> Generation | None:
        """Met à jour atomiquement une génération dans generations.json."""
        async with self._json_store.lock_for(GENERATIONS_FILE.name):
            gens = await self._json_store.read_list_unlocked(GENERATIONS_FILE.name)
            for idx, g in enumerate(gens):
                if g.get("id") == gen_id:
                    g.update(kwargs)
                    gens[idx] = g
                    await self._json_store.write_list_unlocked(GENERATIONS_FILE.name, gens)
                    return Generation.model_validate(g)
        return None

    async def _run_task(self, gen_id: str, req: GenerationCreateRequest, gen: Generation) -> None:
        """Cycle de vie asynchrone d'exécution de la tâche."""
        cancel_evt = self._cancel_events.get(gen_id) or asyncio.Event()
        start_time = time.monotonic()

        try:
            # 1. Passage à RUNNING
            await self._update_generation(gen_id, status=TaskStatus.RUNNING.value, progress=5)
            await self._emit_event(gen_id, {"type": "status", "status": "running", "progress": 5})

            # 2. Soumission au worker
            task_spec = {
                "taskId": gen_id,
                "prompt": gen.compiledPrompt or gen.prompt,
                "negativePrompt": gen.negativePrompt,
                "modelId": gen.modelId,
                "type": gen.mediaType,
                "parameters": gen.parameters.model_dump(),
                "references": gen.references.model_dump(),
            }
            await self._gateway.infer(task_spec)

            # 3. Boucle de suivi d'avancement
            while True:
                if cancel_evt.is_set():
                    logger.info("Tâche %s interrompue par annulation utilisateur", gen_id)
                    break

                if (time.monotonic() - start_time) > self._task_timeout:
                    raise TimeoutError(f"Timeout d'exécution dépassé ({self._task_timeout}s)")

                status_resp = await self._gateway.get_task_status(gen_id)
                remote_status = status_resp.get("status")
                progress_pct = status_resp.get("progress", 0)

                if remote_status == "running":
                    await self._update_generation(gen_id, progress=progress_pct)
                    await self._emit_event(
                        gen_id,
                        {
                            "type": "progress",
                            "status": "running",
                            "progress": progress_pct,
                            "step": status_resp.get("step"),
                        },
                    )
                elif remote_status == "completed":
                    # Rapatriement du binaire
                    artifact_uri = status_resp.get("artifactUri") or f"{gen_id}.mp4"
                    media_bytes = await self._gateway.download_file(artifact_uri)

                    # Résolution du projet et sauvegarde
                    project: Project | None = None
                    if gen.projectId:
                        projects = await self._json_store.read_list(PROJECTS_FILE.name)
                        p_dict = next((p for p in projects if p.get("id") == gen.projectId), None)
                        if p_dict:
                            project = Project.model_validate(p_dict)

                    ext = "mp4" if gen.mediaType == "video" else "png"
                    filename = f"{gen_id}.{ext}"
                    dest_file, thumb_file = await self._media_store.save_media(
                        filename, media_bytes, project=project
                    )

                    saved_gen = await self._update_generation(
                        gen_id,
                        status=TaskStatus.COMPLETED.value,
                        filePath=str(dest_file),
                        thumbnailPath=str(thumb_file) if thumb_file else None,
                        progress=100,
                    )
                    await self._emit_event(
                        gen_id,
                        {
                            "type": "completed",
                            "status": "completed",
                            "progress": 100,
                            "filePath": str(dest_file),
                            "generation": (saved_gen.model_dump() if saved_gen else None),
                        },
                    )
                    break
                elif remote_status == "failed":
                    err_msg = status_resp.get("error", "Erreur distante inconnue")
                    await self._update_generation(
                        gen_id, status=TaskStatus.FAILED.value, errorMessage=err_msg
                    )
                    await self._emit_event(
                        gen_id,
                        {"type": "failed", "status": "failed", "error": err_msg},
                    )
                    break

                await asyncio.sleep(self._poll_interval)

        except Exception as e:
            logger.exception("Échec exécution tâche %s : %s", gen_id, e)
            await self._update_generation(
                gen_id, status=TaskStatus.FAILED.value, errorMessage=str(e)
            )
            await self._emit_event(gen_id, {"type": "failed", "status": "failed", "error": str(e)})
        finally:
            self._active_tasks.pop(gen_id, None)

    async def subscribe_task(self, task_id: str) -> AsyncGenerator[str, None]:
        """Générateur SSE pour streamer les événements d'une tâche en temps réel."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners[task_id].append(queue)

        try:
            gens = await self._json_store.read_list(GENERATIONS_FILE.name)
            current = next((g for g in gens if g.get("id") == task_id), None)
            if current:
                cur_status = current.get("status")
                if cur_status == TaskStatus.COMPLETED.value:
                    yield f"event: completed\ndata: {json.dumps(current)}\n\n"
                    return
                if cur_status == TaskStatus.FAILED.value:
                    yield f"event: failed\ndata: {json.dumps(current)}\n\n"
                    return
                if cur_status == TaskStatus.CANCELLED.value:
                    yield f"event: cancelled\ndata: {json.dumps(current)}\n\n"
                    return
                init_payload = {
                    "status": cur_status,
                    "progress": current.get("progress", 0),
                }
                yield f"event: status\ndata: {json.dumps(init_payload)}\n\n"

            while True:
                event = await queue.get()
                ev_type = event.get("type", "message")
                yield f"event: {ev_type}\ndata: {json.dumps(event)}\n\n"
                if ev_type in {"completed", "failed", "cancelled"}:
                    break
        finally:
            if queue in self._listeners.get(task_id, []):
                self._listeners[task_id].remove(queue)

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Annule une tâche de façon idempotente."""
        gens = await self._json_store.read_list(GENERATIONS_FILE.name)
        current = next((g for g in gens if g.get("id") == task_id), None)
        if not current:
            return {"status": "not_found", "taskId": task_id}

        cur_status = current.get("status")
        if cur_status == TaskStatus.COMPLETED.value:
            return {
                "status": TaskStatus.COMPLETED.value,
                "taskId": task_id,
                "detail": "Tâche déjà terminée",
            }
        if cur_status == TaskStatus.CANCELLED.value:
            return {"status": TaskStatus.CANCELLED.value, "taskId": task_id}

        evt = self._cancel_events.get(task_id)
        if evt:
            evt.set()

        await self._gateway.cancel_task(task_id)

        await self._update_generation(
            task_id,
            status=TaskStatus.CANCELLED.value,
            errorMessage="Annulée par l'utilisateur",
        )

        await self._emit_event(
            task_id,
            {
                "type": "cancelled",
                "status": "cancelled",
                "taskId": task_id,
            },
        )

        return {"status": "cancelled", "taskId": task_id}
