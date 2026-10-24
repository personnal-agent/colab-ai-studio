"""Orchestrateur de tâches asynchrones et flux SSE (app/services/task_orchestrator.py)."""

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

from app.config import (
    BRAND_KITS_FILE,
    CONFIG_FILE,
    DATA_DIR,
    GENERATIONS_FILE,
    OUTPUTS_DIR,
    PROJECTS_FILE,
)
from app.models.domain import (
    BrandKit,
    Generation,
    GenerationParameters,
    GenerationReferences,
    Project,
    StudioConfig,
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
        self.coordination_lock: asyncio.Lock = asyncio.Lock()

        self._active_tasks: dict[str, asyncio.Task[None]] = {}
        self._listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._cancel_events: dict[str, asyncio.Event] = {}

    async def get_task(self, task_id: str) -> Generation | None:
        """Récupère une génération par son identifiant."""
        gens = await self._json_store.read_list(GENERATIONS_FILE.name)
        match = next((g for g in gens if g.get("id") == task_id), None)
        return Generation.model_validate(match) if match else None

    async def submit_generation(self, req: GenerationCreateRequest) -> Generation:
        """Crée une tâche de génération, compile la marque si demandée et lance le worker."""
        async with self.coordination_lock:
            cfg_dict = await self._json_store.read_dict(
                CONFIG_FILE.name, default=StudioConfig().model_dump()
            )
            cfg = StudioConfig.model_validate(cfg_dict)

            worker_url = None
            if hasattr(self._gateway, "get_active_worker_url"):
                try:
                    _, worker_url = await self._gateway.get_active_worker_url()
                except Exception:
                    worker_url = None
            else:
                worker_url = getattr(self._gateway, "base_url", "http://127.0.0.1:8190")

            kit: BrandKit | None = None
            if req.brandKitId:
                kits = await self._json_store.read_list(BRAND_KITS_FILE.name)
                match = next((k for k in kits if k.get("id") == req.brandKitId), None)
                if match:
                    kit = BrandKit.model_validate(match)

            max_image_refs = 4
            if req.type == "text":
                max_image_refs = 0
            else:
                found_in_catalog = False
                try:
                    models = await self._gateway.list_models()
                    m_info = next((m for m in models if m.get("id") == req.modelId), None)
                    if m_info:
                        found_in_catalog = True
                        if m_info.get("type") == "text":
                            max_image_refs = 0
                        else:
                            caps = m_info.get("capabilities", {})
                            max_image_refs = (
                                caps.get("maxImageRefs", 4)
                                if caps.get("supportsImageRef", True)
                                else 0
                            )
                except Exception as e:
                    logger.debug("Échec détection capacités modèle %s : %s", req.modelId, e)

                if not found_in_catalog and (
                    "text" in req.modelId.lower() or "llm" in req.modelId.lower()
                ):
                    max_image_refs = 0

            # Compilation du Brand Kit avec llm_config
            compiled = await self._compiler.compile(
                prompt=req.prompt,
                brand_kit=kit,
                user_refs=req.references.imageRefs,
                max_image_refs=max_image_refs,
                llm_config=cfg.compilerLlm,
            )

            gen_id = f"gen_{uuid.uuid4().hex[:10]}"
            refs = req.references.model_copy()
            # Remplacement systématique de refs.imageRefs par le résultat compilé (même vide)
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
                workerUrl=worker_url,
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

    async def _update_generation(
        self, gen_id: str, allow_from_terminal: bool = False, **kwargs: Any
    ) -> Generation | None:
        """Met à jour atomiquement une génération en sanctuarisant les états terminaux."""
        async with self._json_store.lock_for(GENERATIONS_FILE.name):
            gens = await self._json_store.read_list_unlocked(GENERATIONS_FILE.name)
            for idx, g in enumerate(gens):
                if g.get("id") == gen_id:
                    old_status = g.get("status")
                    terminal_statuses = {
                        TaskStatus.COMPLETED.value,
                        TaskStatus.CANCELLED.value,
                        TaskStatus.FAILED.value,
                    }
                    if not allow_from_terminal and old_status in terminal_statuses:
                        logger.warning(
                            "Tâche %s déjà dans l'état terminal '%s'. Rejet écrasement vers '%s'.",
                            gen_id,
                            old_status,
                            kwargs.get("status"),
                        )
                        return Generation.model_validate(g)

                    g.update(kwargs)
                    gens[idx] = g
                    await self._json_store.write_list_unlocked(GENERATIONS_FILE.name, gens)
                    return Generation.model_validate(g)
        return None

    async def _run_task(self, gen_id: str, req: GenerationCreateRequest, gen: Generation) -> None:
        """Cycle de vie asynchrone d'exécution de la tâche."""
        cancel_evt = self._cancel_events.get(gen_id) or asyncio.Event()
        start_time = time.monotonic()
        target_worker_url = gen.workerUrl

        try:
            # 1. Passage à RUNNING
            await self._update_generation(gen_id, status=TaskStatus.RUNNING.value, progress=5)
            await self._emit_event(gen_id, {"type": "running", "status": "running", "progress": 5})

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
                    with contextlib.suppress(Exception):
                        await self._gateway.cancel_task(gen_id, base_url=target_worker_url)
                    raise TimeoutError(f"Timeout d'exécution dépassé ({self._task_timeout}s)")

                status_resp = await self._gateway.get_task_status(
                    gen_id, base_url=target_worker_url
                )
                remote_status = status_resp.get("status")
                progress_pct = status_resp.get("progress", 0)

                if remote_status == "running":
                    await self._update_generation(gen_id, progress=progress_pct)
                    await self._emit_event(
                        gen_id,
                        {
                            "type": "running",
                            "status": "running",
                            "progress": progress_pct,
                            "step": status_resp.get("step"),
                        },
                    )
                elif remote_status == "cancelled":
                    up = await self._update_generation(
                        gen_id,
                        status=TaskStatus.CANCELLED.value,
                        errorMessage="Annulée sur le worker distant",
                    )
                    if up and up.status == TaskStatus.CANCELLED:
                        await self._emit_event(
                            gen_id, {"type": "cancelled", "status": "cancelled", "taskId": gen_id}
                        )
                    break
                elif remote_status == "completed":
                    if cancel_evt.is_set():
                        up = await self._update_generation(
                            gen_id,
                            status=TaskStatus.CANCELLED.value,
                            errorMessage="Annulée par l'utilisateur",
                        )
                        if up and up.status == TaskStatus.CANCELLED:
                            await self._emit_event(
                                gen_id,
                                {"type": "cancelled", "status": "cancelled", "taskId": gen_id},
                            )
                        break

                    # Rapatriement du binaire
                    artifact_uri = status_resp.get("artifactUri") or f"{gen_id}.mp4"
                    media_bytes = await self._gateway.download_file(
                        artifact_uri, base_url=target_worker_url
                    )

                    if cancel_evt.is_set():
                        await self._update_generation(
                            gen_id,
                            status=TaskStatus.CANCELLED.value,
                            errorMessage="Annulée par l'utilisateur",
                        )
                        await self._emit_event(
                            gen_id,
                            {"type": "cancelled", "status": "cancelled", "taskId": gen_id},
                        )
                        break

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

                    if cancel_evt.is_set():
                        dest_file.unlink(missing_ok=True)
                        if thumb_file:
                            thumb_file.unlink(missing_ok=True)
                        await self._update_generation(
                            gen_id,
                            status=TaskStatus.CANCELLED.value,
                            errorMessage="Annulée par l'utilisateur",
                        )
                        await self._emit_event(
                            gen_id,
                            {"type": "cancelled", "status": "cancelled", "taskId": gen_id},
                        )
                        break

                    saved_gen = await self._update_generation(
                        gen_id,
                        status=TaskStatus.COMPLETED.value,
                        filePath=str(dest_file),
                        thumbnailPath=str(thumb_file) if thumb_file else None,
                        progress=100,
                    )
                    # Si l'annulation a gagné entre-temps sous le verrou
                    if saved_gen and saved_gen.status == TaskStatus.CANCELLED:
                        dest_file.unlink(missing_ok=True)
                        if thumb_file:
                            thumb_file.unlink(missing_ok=True)
                        break

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
                    with contextlib.suppress(Exception):
                        await self._gateway.cancel_task(gen_id, base_url=target_worker_url)
                    up = await self._update_generation(
                        gen_id, status=TaskStatus.FAILED.value, errorMessage=err_msg
                    )
                    if up and up.status == TaskStatus.FAILED:
                        await self._emit_event(
                            gen_id, {"type": "failed", "status": "failed", "error": err_msg}
                        )
                    break

                await asyncio.sleep(self._poll_interval)

        except Exception as e:
            if not cancel_evt.is_set():
                logger.exception("Échec exécution tâche %s : %s", gen_id, e)
                with contextlib.suppress(Exception):
                    await self._gateway.cancel_task(gen_id, base_url=target_worker_url)
                up = await self._update_generation(
                    gen_id, status=TaskStatus.FAILED.value, errorMessage=str(e)
                )
                if up and up.status == TaskStatus.FAILED:
                    await self._emit_event(
                        gen_id, {"type": "failed", "status": "failed", "error": str(e)}
                    )
        finally:
            self._active_tasks.pop(gen_id, None)
            if not self._listeners.get(gen_id):
                self._cancel_events.pop(gen_id, None)

    async def subscribe_task(
        self, task_id: str, keepalive_timeout: float = 15.0
    ) -> AsyncGenerator[str, None]:
        """Générateur SSE pour streamer les événements d'une tâche avec keep-alive."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners[task_id].append(queue)

        def _sse_event(g: dict[str, Any]) -> str:
            st = g.get("status")
            p = {
                "type": st,
                "status": st,
                "progress": g.get("progress", 0),
                "filePath": g.get("filePath"),
                "error": g.get("errorMessage"),
                "generation": g,
            }
            return f"event: {st}\ndata: {json.dumps(p)}\n\n"

        try:
            gens = await self._json_store.read_list(GENERATIONS_FILE.name)
            current = next((g for g in gens if g.get("id") == task_id), None)
            if current:
                cur_status = current.get("status")
                yield _sse_event(current)
                if cur_status in {
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value,
                }:
                    return

            while True:
                # Dépiler d'abord tous les événements disponibles dans la file
                while not queue.empty():
                    event = queue.get_nowait()
                    ev_type = event.get("type", "message")
                    yield f"event: {ev_type}\ndata: {json.dumps(event)}\n\n"
                    if ev_type in {"completed", "failed", "cancelled"}:
                        return

                # Si la tâche n'est plus active en arrière-plan, vérifier l'état persistant final
                if task_id not in self._active_tasks:
                    gens = await self._json_store.read_list(GENERATIONS_FILE.name)
                    latest = next((g for g in gens if g.get("id") == task_id), None)
                    if latest and latest.get("status") in {
                        TaskStatus.COMPLETED.value,
                        TaskStatus.FAILED.value,
                        TaskStatus.CANCELLED.value,
                    }:
                        yield _sse_event(latest)
                    return

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=keepalive_timeout)
                    ev_type = event.get("type", "message")
                    yield f"event: {ev_type}\ndata: {json.dumps(event)}\n\n"
                    if ev_type in {"completed", "failed", "cancelled"}:
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if task_id in self._listeners:
                if queue in self._listeners[task_id]:
                    self._listeners[task_id].remove(queue)
                if not self._listeners[task_id]:
                    self._listeners.pop(task_id, None)
                    if task_id not in self._active_tasks:
                        self._cancel_events.pop(task_id, None)

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Annule une tâche de façon idempotente et atomique."""
        evt = self._cancel_events.get(task_id)
        if evt:
            evt.set()

        worker_url = None
        async with self._json_store.lock_for(GENERATIONS_FILE.name):
            gens = await self._json_store.read_list_unlocked(GENERATIONS_FILE.name)
            target = next((g for g in gens if g.get("id") == task_id), None)
            if not target:
                return {"status": "not_found", "taskId": task_id}

            cur_status = target.get("status")
            if cur_status in {
                TaskStatus.COMPLETED.value,
                TaskStatus.CANCELLED.value,
                TaskStatus.FAILED.value,
            }:
                return {
                    "status": cur_status,
                    "taskId": task_id,
                    "detail": f"Tâche déjà dans l'état terminal '{cur_status}'",
                }

            worker_url = target.get("workerUrl")
            target["status"] = TaskStatus.CANCELLED.value
            target["errorMessage"] = "Annulée par l'utilisateur"
            await self._json_store.write_list_unlocked(GENERATIONS_FILE.name, gens)

        # Notification au worker en dehors du verrou
        if worker_url:
            await self._gateway.cancel_task(task_id, base_url=worker_url)
        else:
            await self._gateway.cancel_task(task_id)

        await self._emit_event(
            task_id,
            {
                "type": "cancelled",
                "status": "cancelled",
                "taskId": task_id,
            },
        )

        return {"status": "cancelled", "taskId": task_id}

    async def aclose(self) -> None:
        """Ferme proprement l'orchestrateur, annule les tâches actives et ferme la passerelle."""
        for _tid, task in list(self._active_tasks.items()):
            task.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)
        self._active_tasks.clear()
        self._listeners.clear()
        self._cancel_events.clear()
        await self._gateway.aclose()
