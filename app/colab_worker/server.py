"""Serveur FastAPI du Worker Google Colab (app/colab_worker/server.py).

Expose l'ensemble des routes d'inférence, de contrôle et de streaming SSE
consommées par le backend local Colab AI Studio :
- GET /health
- GET /models
- POST /models/switch
- POST /infer
- GET /tasks/{task_id}/status
- POST /tasks/{task_id}/cancel
- POST /v1/chat/completions
- POST /v1/chat/cancel
- GET /files/{filename}
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import struct
import tempfile
import time
import uuid
import zlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.colab_worker.model_swapper import ModelSwapper

logger = logging.getLogger(__name__)

def _model_spec(
    mid: str, name: str, mtype: str, ratios: list[str], res: list[str],
    dur: list[str], neg: bool = False, seed: bool = False,
    img_ref: bool = False, max_refs: int = 0,
) -> dict[str, Any]:
    return {
        "id": mid, "name": name, "type": mtype,
        "capabilities": {
            "aspectRatios": ratios, "resolutions": res, "durations": dur,
            "supportsNegativePrompt": neg, "supportsSeed": seed,
            "supportsImageRef": img_ref, "maxImageRefs": max_refs,
        },
    }


AVAILABLE_MODELS: list[dict[str, Any]] = [
    _model_spec(
        "flux-schnell", "FLUX.1 [schnell]", "image",
        ["1:1", "16:9", "9:16", "4:3", "3:4"], ["1024x1024", "768x768", "512x512"],
        ["1s"], False, True, True, 1,
    ),
    _model_spec(
        "wan-2.1-t2v", "Wan 2.1 Video", "video",
        ["16:9", "9:16", "1:1"], ["720p", "480p"], ["5s", "10s"], True, True, True, 2,
    ),
    _model_spec(
        "cogvideox-5b", "CogVideoX-5B", "video", ["16:9"], ["720p"], ["6s"],
        neg=True, seed=True,
    ),
    _model_spec(
        "wav2lip", "Wav2Lip Lip Sync", "lipsync",
        ["16:9", "9:16", "1:1"], ["720p"], ["5s", "10s", "15s"],
    ),
    _model_spec(
        "realesrgan-x4", "Real-ESRGAN Upscaler", "upscale",
        ["16:9", "9:16", "1:1"], ["1080p", "4K"], ["5s"],
    ),
    _model_spec("llama-3-8b-instruct", "Llama 3 8B Instruct", "text", [], [], []),
]


def make_valid_png(
    width: int = 64, height: int = 64, color: tuple[int, int, int] = (30, 41, 59)
) -> bytes:
    """Génère un flux d'octets PNG valide et conforme à la spécification ISO/IEC 15948."""
    png_sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc
    row = b"\x00" + bytes(color) * width
    raw_data = row * height
    idat_content = zlib.compress(raw_data)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + idat_content))
    idat = struct.pack(">I", len(idat_content)) + b"IDAT" + idat_content + idat_crc
    iend_crc = struct.pack(">I", zlib.crc32(b"IEND"))
    iend = struct.pack(">I", 0) + b"IEND" + iend_crc
    return png_sig + ihdr + idat + iend


def make_valid_mp4() -> bytes:
    """Génère un conteneur MP4 valide avec en-têtes ftyp, moov et mvhd."""
    ftyp = struct.pack(">I", 28) + b"ftypisom\x00\x00\x02\x00isomiso2mp41"
    mvhd = (
        struct.pack(">I", 108) + b"mvhd" + b"\x00" * 12
        + struct.pack(">II", 1000, 1000) + b"\x00" * 80
    )
    moov = struct.pack(">I", 8 + len(mvhd)) + b"moov" + mvhd
    mdat = struct.pack(">I", 72) + b"mdat" + b"\x00" * 64
    return ftyp + moov + mdat


class SwitchModelRequest(BaseModel):
    modelId: str


class InferRequest(BaseModel):
    taskId: str | None = None
    modelId: str
    prompt: str = ""
    negativePrompt: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    references: dict[str, Any] = Field(default_factory=dict)
    steps: int = 5

    @field_validator("taskId")
    @classmethod
    def validate_task_id(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "taskId doit contenir uniquement des caractères alphanumériques, "
                "tirets ou underscores"
            )
        return v


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "llama-3-8b-instruct"
    messages: list[ChatMessage]
    stream: bool = True
    requestId: str | None = None


class ChatCancelRequest(BaseModel):
    requestId: str


def create_worker_app(
    model_swapper: ModelSwapper | None = None,
    storage_dir: Path | None = None,
    worker_secret: str | None = None,
    idle_check_interval: float = 1.0,
    model_loaders: dict[str, Any] | None = None,
    simulation_mode: bool | None = None,
) -> FastAPI:
    """Fabrique d'application FastAPI pour le worker Google Colab."""
    swapper = model_swapper or ModelSwapper()
    output_dir = storage_dir or (Path(tempfile.gettempdir()) / "colab_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    secret = worker_secret or os.environ.get("COLAB_STUDIO_SECRET")
    loaders = model_loaders or {}
    sim_mode = (
        simulation_mode
        if simulation_mode is not None
        else (os.environ.get("COLAB_STUDIO_SIMULATION", "1" if not loaders else "0") == "1")
    )

    tasks: dict[str, dict[str, Any]] = {}
    cancel_events: dict[str, asyncio.Event] = {}
    active_chat_cancels: set[str] = set()
    gpu_lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop_event = asyncio.Event()

        async def _idle_checker():
            while not stop_event.is_set():
                try:
                    await asyncio.sleep(idle_check_interval)
                    busy = any(t.get("status") == "running" for t in tasks.values())
                    if not busy and not gpu_lock.locked():
                        swapper.check_idle_timeout()
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.debug(
                        "Erreur lors de la vérification d'inactivité du worker : %s", exc
                    )

        checker_task = asyncio.create_task(_idle_checker())
        try:
            yield
        finally:
            stop_event.set()
            checker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await checker_task

    app = FastAPI(title="Colab AI Studio Worker", version="1.0.0", lifespan=lifespan)

    origins = [
        f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 8000, 8190)
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if secret:
            auth = request.headers.get("authorization", "")
            x_sec = request.headers.get("x-colab-secret", "")
            q_sec = request.query_params.get("secret", "")
            bearer = auth[7:].strip() if auth.startswith("Bearer ") else ""
            if secret not in (x_sec, bearer, q_sec):
                return JSONResponse(status_code=401, content={"detail": "Non autorisé"})
        return await call_next(request)

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {"status": "ok", **swapper.get_telemetry()}

    @app.get("/models")
    async def list_models() -> list[dict[str, Any]]:
        return AVAILABLE_MODELS

    def _prepare_pipeline_kwargs(p: InferRequest) -> dict[str, Any]:
        raw = dict(p.parameters)
        ratio = raw.pop("aspectRatio", "1:1")
        raw.pop("duration", None)
        res = raw.pop("resolution", None)
        tbl: dict[str, dict[str, tuple[int, int]]] = {
            "16:9": {
                "512x512": (512, 288), "768x768": (768, 432), "1024x1024": (1024, 576),
                "480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080), "4K": (3840, 2160),
            },
            "9:16": {
                "512x512": (288, 512), "768x768": (432, 768), "1024x1024": (576, 1024),
                "480p": (480, 854), "720p": (720, 1280), "1080p": (1080, 1920), "4K": (2160, 3840),
            },
            "4:3": {"512x512": (512, 384), "768x768": (768, 576), "1024x1024": (1024, 768)},
            "3:4": {"512x512": (384, 512), "768x768": (576, 768), "1024x1024": (768, 1024)},
            "1:1": {
                "512x512": (512, 512), "768x768": (768, 768), "1024x1024": (1024, 1024),
                "480p": (480, 480), "720p": (720, 720), "1080p": (1080, 1080),
            },
        }
        fb = {"16:9": (1024, 576), "9:16": (576, 1024), "4:3": (1024, 768), "3:4": (768, 1024)}
        wh = tbl.get(ratio, {}).get(res) or fb.get(ratio, (1024, 1024))
        kw = {"width": wh[0], "height": wh[1], **raw}
        if p.prompt:
            kw["prompt"] = p.prompt
        if p.negativePrompt:
            kw["negative_prompt"] = p.negativePrompt
        return kw

    @app.post("/models/switch")
    async def switch_model(payload: SwitchModelRequest) -> dict[str, Any]:
        async with gpu_lock:
            swapper.ensure_model(payload.modelId, load_fn=loaders.get(payload.modelId))
        return {"status": "ok", "activeModel": payload.modelId}

    async def _execute_inference_task(task_id: str, payload: InferRequest) -> None:
        cancel_event = cancel_events[task_id]
        tasks[task_id]["status"] = "running"
        total_steps = max(1, payload.steps)

        try:
            async with gpu_lock:
                loader = loaders.get(payload.modelId)
                pipeline = swapper.ensure_model(payload.modelId, load_fn=loader)

                is_video = any(
                    m["id"] == payload.modelId and m["type"] in {"video", "lipsync"}
                    for m in AVAILABLE_MODELS
                )
                ext = ".mp4" if is_video else ".png"
                filename = f"{task_id}{ext}"
                file_path = (output_dir / filename).resolve()
                if not file_path.is_relative_to(output_dir.resolve()):
                    raise ValueError("Tentative d'écriture hors du répertoire de sortie sécurisé")

                if not sim_mode:
                    if not callable(pipeline):
                        msg = f"Modèle {payload.modelId} indisponible en mode réel"
                        raise ValueError(msg)
                    tasks[task_id]["step"] = 1
                    tasks[task_id]["progress"] = 50

                    def _run_real_infer():
                        kw = _prepare_pipeline_kwargs(payload)
                        if hasattr(pipeline, "callback_on_step_end"):
                            def _cb(p, s, t, cb_kw):
                                if cancel_event.is_set():
                                    p._interrupt = True
                                return cb_kw
                            kw["callback_on_step_end"] = _cb

                        out = pipeline(**kw)
                        if cancel_event.is_set():
                            return
                        if hasattr(out, "images") and out.images:
                            out.images[0].save(file_path)
                        elif hasattr(out, "frames") and out.frames:
                            from diffusers.utils import export_to_video
                            vid = out.frames[0] if isinstance(out.frames[0], list) else out.frames
                            export_to_video(vid, output_video_path=str(file_path), fps=8)
                        elif hasattr(out, "save"):
                            out.save(file_path)
                        elif isinstance(out, bytes):
                            file_path.write_bytes(out)
                        if not file_path.exists():
                            raise RuntimeError(f"Aucun fichier produit pour {payload.taskId}")

                    await asyncio.to_thread(_run_real_infer)
                else:
                    for step in range(1, total_steps + 1):
                        if cancel_event.is_set():
                            tasks[task_id]["status"] = "cancelled"
                            tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
                            return
                        await asyncio.sleep(0.04)
                        tasks[task_id]["step"] = step
                        tasks[task_id]["totalSteps"] = total_steps
                        tasks[task_id]["progress"] = int(round(step / total_steps * 100))

                    valid_bytes = make_valid_png() if ext == ".png" else make_valid_mp4()
                    file_path.write_bytes(valid_bytes)

            if cancel_event.is_set():
                tasks[task_id]["status"] = "cancelled"
                tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
                return

            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 100
            tasks[task_id]["artifactUri"] = filename
            tasks[task_id]["outputUrl"] = f"/files/{filename}"

        except Exception as exc:
            if "out of memory" in str(exc).lower():
                swapper.evict_vram()
            logger.exception("Erreur durant l'inférence tâche %s : %s", task_id, exc)
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(exc)
            tasks[task_id]["errorMessage"] = str(exc)

    @app.post("/infer")
    async def infer(payload: InferRequest) -> dict[str, Any]:
        task_id = payload.taskId or f"task_{uuid.uuid4().hex[:12]}"
        cancel_event = asyncio.Event()
        cancel_events[task_id] = cancel_event

        tasks[task_id] = {
            "taskId": task_id,
            "status": "pending",
            "progress": 0,
            "step": 0,
            "totalSteps": payload.steps,
            "outputUrl": None,
            "artifactUri": None,
            "error": None,
            "errorMessage": None,
            "createdAt": time.time(),
        }

        asyncio.create_task(_execute_inference_task(task_id, payload))
        return {"taskId": task_id, "status": "pending"}

    @app.get("/tasks/{task_id}/status")
    async def get_task_status(task_id: str) -> dict[str, Any]:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Tâche introuvable")
        return tasks[task_id]

    @app.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, Any]:
        if task_id in cancel_events:
            cancel_events[task_id].set()
        if task_id in tasks:
            tasks[task_id]["status"] = "cancelled"
            tasks[task_id]["errorMessage"] = "Annulée par l'utilisateur"
        return {"status": "cancelled", "taskId": task_id}

    @app.get("/files/{filename}")
    async def download_file(filename: str) -> FileResponse:
        clean_name = filename.strip().lstrip("/")
        if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
            raise HTTPException(status_code=400, detail="Chemin de fichier interdit")

        file_path = (output_dir / clean_name).resolve()
        if not file_path.is_relative_to(output_dir.resolve()) or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Fichier introuvable sur le worker")

        media_type = "video/mp4" if clean_name.endswith(".mp4") else "image/png"
        return FileResponse(file_path, media_type=media_type, filename=clean_name)

    @app.post("/v1/chat/cancel")
    async def cancel_chat(payload: ChatCancelRequest) -> dict[str, str]:
        active_chat_cancels.add(payload.requestId)
        return {"status": "cancelled", "requestId": payload.requestId}

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: ChatCompletionRequest, request: Request) -> Any:
        request_id = payload.requestId or f"chat_{uuid.uuid4().hex[:10]}"
        last_user_msg = payload.messages[-1].content if payload.messages else "Bonjour"
        summary = last_user_msg[:40] + "..." if len(last_user_msg) > 40 else last_user_msg

        if not payload.stream:
            async with gpu_lock:
                chat_model = swapper.ensure_model(payload.model, load_fn=loaders.get(payload.model))
                content = f"Voici une réponse synthétisée par {payload.model} pour : « {summary} »."
                if callable(chat_model) and not sim_mode:
                    prompt_in = "\n".join(f"{m.role}: {m.content}" for m in payload.messages)
                    try:
                        res = await asyncio.to_thread(chat_model, prompt_in, max_new_tokens=150)
                        if isinstance(res, list) and res and "generated_text" in res[0]:
                            content = res[0]["generated_text"].replace(prompt_in, "").strip()
                        else:
                            content = str(res)
                    except Exception as exc:
                        if "out of memory" in str(exc).lower():
                            swapper.evict_vram()
                        raise
            return {
                "id": request_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
            }

        async def chat_stream_generator() -> AsyncGenerator[str, None]:
            async with gpu_lock:
                chat_model = swapper.ensure_model(payload.model, load_fn=loaders.get(payload.model))
                words = [
                    "Bonjour", " ! ", "Voici", " une", " réponse", " synthétisée", " pour",
                    f" « {summary} »", " par", " le", " worker", " distant", " Colab.",
                ]
                if callable(chat_model) and not sim_mode:
                    if request_id in active_chat_cancels or await request.is_disconnected():
                        return
                    prompt_in = "\n".join(f"{m.role}: {m.content}" for m in payload.messages)
                    tok = getattr(chat_model, "tokenizer", None)
                    if tok is not None:
                        from threading import Thread

                        from transformers import TextIteratorStreamer
                        from transformers.generation import StoppingCriteria, StoppingCriteriaList

                        class CancelCriteria(StoppingCriteria):
                            def __call__(self, input_ids, scores, **kw):
                                return request_id in active_chat_cancels

                        streamer = TextIteratorStreamer(
                            tok, skip_prompt=True, skip_special_tokens=True
                        )
                        crit = StoppingCriteriaList([CancelCriteria()])
                        gen_kw = {
                            "max_new_tokens": 150,
                            "streamer": streamer,
                            "stopping_criteria": crit,
                        }
                        loop = asyncio.get_running_loop()
                        q: asyncio.Queue[tuple[str | None, Exception | None]] = asyncio.Queue()

                        def _worker():
                            try:
                                chat_model(prompt_in, **gen_kw)
                            except Exception as th_err:
                                if "out of memory" in str(th_err).lower():
                                    swapper.evict_vram()
                                loop.call_soon_threadsafe(q.put_nowait, (None, th_err))
                            finally:
                                streamer.end()

                        def _stream_reader():
                            try:
                                for token in streamer:
                                    if request_id in active_chat_cancels:
                                        break
                                    loop.call_soon_threadsafe(q.put_nowait, (token, None))
                            except Exception as s_err:
                                loop.call_soon_threadsafe(q.put_nowait, (None, s_err))
                            finally:
                                loop.call_soon_threadsafe(q.put_nowait, (None, None))

                        th_m = Thread(target=_worker, daemon=True)
                        th_s = Thread(target=_stream_reader, daemon=True)
                        th_m.start()
                        th_s.start()
                        try:
                            while True:
                                if (
                                    request_id in active_chat_cancels
                                    or await request.is_disconnected()
                                ):
                                    return
                                try:
                                    token, err = await asyncio.wait_for(q.get(), timeout=60.0)
                                except asyncio.TimeoutError:
                                    msg = "\n[Erreur: délai de génération dépassé]"
                                    ec = {
                                        "index": 0,
                                        "delta": {"content": msg},
                                        "finish_reason": "error",
                                    }
                                    echunk = {
                                        "id": request_id,
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": payload.model,
                                        "choices": [ec],
                                    }
                                    yield f"data: {json.dumps(echunk)}\n\n"
                                    yield "data: [DONE]\n\n"
                                    return
                                if err is not None:
                                    raise err
                                if token is None:
                                    break
                                d = {"content": token}
                                choice = {"index": 0, "delta": d, "finish_reason": None}
                                chunk = {
                                    "id": request_id,
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": payload.model,
                                    "choices": [choice],
                                }
                                yield f"data: {json.dumps(chunk)}\n\n"
                        finally:
                            streamer.end()
                            th_m.join(timeout=0.5)
                            th_s.join(timeout=0.5)
                        yield "data: [DONE]\n\n"
                        return

                    try:
                        res = await asyncio.to_thread(chat_model, prompt_in, max_new_tokens=150)
                        if isinstance(res, list) and res and "generated_text" in res[0]:
                            txt = res[0]["generated_text"].replace(prompt_in, "").strip()
                            words = [w + " " for w in txt.split()]
                    except Exception as exc:
                        if "out of memory" in str(exc).lower():
                            swapper.evict_vram()
                        raise

                try:
                    for word in words:
                        if request_id in active_chat_cancels or await request.is_disconnected():
                            logger.info("Chat LLM annulé pour %s.", request_id)
                            return

                        chunk = {
                            "id": request_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": payload.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": word},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                        await asyncio.sleep(0.04)

                    yield "data: [DONE]\n\n"
                finally:
                    active_chat_cancels.discard(request_id)

        return StreamingResponse(
            chat_stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return app
