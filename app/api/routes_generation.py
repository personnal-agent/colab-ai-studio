"""Routes de génération multimédia, estimation GPU/VRAM, Matrice 4 Angles et flux SSE."""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.routes_characters import compile_character_mentions
from app.api.routes_crud import get_json_store, get_media_store, verify_trusted_origin
from app.api.routes_models import get_worker_gateway
from app.config import CHARACTERS_FILE, GENERATIONS_FILE, UPLOADS_DIR
from app.models.domain import GenerationParameters, GenerationReferences
from app.services.audio_weaver import extract_dialogues
from app.services.contract_engine import ContractEngine, get_contract_engine
from app.services.story_director import (
    StoryDirector,
    calculate_segments_duration,
    parse_explicit_script_segments,
)
from app.services.task_orchestrator import GenerationCreateRequest, TaskOrchestrator
from app.services.worker_gateway import WorkerGateway
from app.storage.json_store import JSONDocumentStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Génération"])

_default_orchestrator = TaskOrchestrator(json_store=get_json_store(), media_store=get_media_store())
_default_story_director = StoryDirector()


def get_task_orchestrator() -> TaskOrchestrator:
    """Fournisseur de dépendance pour l'orchestrateur de tâches."""
    return _default_orchestrator


class TimelinePlanRequest(BaseModel):
    prompt: str = Field(..., description="Prompt ou scénario complet")
    targetDurationSec: float | None = Field(
        default=None, description="Durée totale cible si connue"
    )
    maxSegmentSec: float = Field(default=10.0, description="Durée max par segment")


class WorkloadEstimateRequest(BaseModel):
    prompt: str = Field(default="", description="Prompt utilisateur")
    modelId: str = Field(default="minimax-h3", description="Modèle cible")
    type: str = Field(
        default="video", description="Type de média (video, image, upscale, lip_sync)"
    )
    duration: str = Field(default="5s", description="Durée choisie (5s, 10s, auto)")
    resolution: str = Field(default="1080p", description="Résolution cible")
    batchCount: int = Field(default=1, description="Nombre de copies")


class AngleMatrixRequest(BaseModel):
    sourceImage: str = Field(
        ..., description="ID de génération (gen_xxx) ou chemin/URL d'image source"
    )
    prompt: str = Field(
        default=(
            "Maintain exact subject details, facial identity, and lighting while "
            "rotating camera perspective."
        ),
        description="Instruction de conservation du sujet",
    )
    modelId: str = Field(default="qwen-image-2.1", description="Modèle d'image/angle local")
    aspectRatio: str = Field(default="16:9", description="Ratio d'aspect")
    resolution: str = Field(default="1024x1024", description="Résolution")
    projectId: str | None = None


class ExtractFrameRequest(BaseModel):
    generationId: str = Field(..., description="Identifiant de la génération vidéo")


ANGLE_ORBIT_PRESETS: list[dict[str, Any]] = [
    {
        "label": "Left Orbit (-30°)",
        "h": -30.0,
        "v": 0.0,
        "z": 1.0,
        "directive": (
            "Camera orbiting 30 degrees to the left, three-quarter left profile view "
            "of the exact same subject and scene."
        ),
    },
    {
        "label": "Right Orbit (+30°)",
        "h": 30.0,
        "v": 0.0,
        "z": 1.0,
        "directive": (
            "Camera orbiting 30 degrees to the right, three-quarter right profile view "
            "of the exact same subject and scene."
        ),
    },
    {
        "label": "High Pitch (+20°)",
        "h": 0.0,
        "v": 20.0,
        "z": 1.0,
        "directive": (
            "High-angle cinematic camera shot pitched +20 degrees looking slightly down "
            "at the exact same subject and scene."
        ),
    },
    {
        "label": "Close-Up Zoom (1.4x)",
        "h": 0.0,
        "v": 0.0,
        "z": 1.4,
        "directive": (
            "Intimate 1.4x optical zoom-in close-up shot focusing on the subject's face "
            "and fine organic skin texture."
        ),
    },
]


@router.post(
    "/generate/estimate",
    response_model=dict[str, Any],
)
async def estimate_workload(
    payload: WorkloadEstimateRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Module E : Estime en temps réel (<5ms) le nombre de plans, le temps GPU RTX 5000 Ada,
    la VRAM requise, les personnages @Nom détectés et les dialogues audio.
    """
    prompt_text = (payload.prompt or "").strip()
    mtype = (payload.type or "video").lower()
    mid = (payload.modelId or "").lower()
    batch = max(1, min(int(payload.batchCount or 1), 8))

    # 1. Détection des personnages @Nom
    chars_raw = await store.read_list(CHARACTERS_FILE.name)
    _, matched_char_ids, _, _ = compile_character_mentions(prompt_text, chars_raw)
    matched_char_names = [
        c.get("triggerToken") or f"@{c.get('name')}"
        for c in chars_raw
        if c.get("id") in matched_char_ids
    ]

    # 2. Détection des dialogues parlés (Module D Audio Weaver)
    dialogues = extract_dialogues(prompt_text)

    # 3. Calcul du nombre de plans et de la durée totale
    _, explicit_segs = parse_explicit_script_segments(prompt_text)
    if mtype == "video":
        if len(explicit_segs) >= 2:
            num_segments = len(explicit_segs)
            total_duration_sec = float(num_segments * 10.0)
            is_chained = True
        elif (payload.duration or "").strip().lower() == "auto":
            clauses = [
                c.strip() for c in prompt_text.replace("\n", ".").split(".") if len(c.strip()) > 8
            ]
            est_sec = max(10.0, float(max(1, len(clauses)) * 10.0))
            durs = calculate_segments_duration(est_sec, 10.0)
            num_segments = len(durs)
            total_duration_sec = sum(durs)
            is_chained = num_segments > 1
        else:
            dur_str = str(payload.duration or "5s").lower().replace("s", "").strip()
            try:
                total_duration_sec = float(dur_str)
            except ValueError:
                total_duration_sec = 5.0
            num_segments = 1
            is_chained = False
    else:
        num_segments = 1
        total_duration_sec = 1.0
        is_chained = False

    # 4. Estimation Temps GPU (RTX 5000 Ada 32 Go) & VRAM
    if mtype == "video":
        if "minimax" in mid:
            sec_per_seg = 165.0 if total_duration_sec >= 10.0 or num_segments > 1 else 95.0
            vram_gb = 21.8
        elif "noctq" in mid:
            sec_per_seg = 75.0
            vram_gb = 16.4
        else:
            sec_per_seg = 90.0
            vram_gb = 18.0
        estimated_seconds_gpu = int(round(sec_per_seg * num_segments * batch))
    elif mtype == "upscale":
        estimated_seconds_gpu = 12 * batch
        vram_gb = 6.5
    elif mtype in {"lip_sync", "lipsync"}:
        estimated_seconds_gpu = 35 * batch
        vram_gb = 10.2
    else:
        estimated_seconds_gpu = 18 * batch
        vram_gb = 12.4

    return {
        "mediaType": mtype,
        "modelId": payload.modelId,
        "numSegments": num_segments,
        "totalDurationSec": total_duration_sec,
        "isChained": is_chained,
        "estimatedSecondsGpu": estimated_seconds_gpu,
        "estimatedVramGb": vram_gb,
        "vramTotalGb": 32.0,
        "detectedCharacters": matched_char_names,
        "detectedDialoguesCount": len(dialogues),
    }


@router.post(
    "/generate/angle-matrix",
    status_code=202,
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def generate_angle_matrix(
    payload: AngleMatrixRequest,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Module A : Génère automatiquement 4 angles de caméra orbitaux cohérents
    (Left -30°, Right +30°, High Pitch +20°, Zoom 1.4x) à partir d'une image de référence.
    """
    src_img = payload.sourceImage.strip()
    base_prompt = payload.prompt.strip()

    # Si sourceImage est un ID de génération (gen_xxx), on récupère son filePath et son prompt
    if src_img.startswith("gen_") or "/api/generations/" in src_img:
        gen_id = (
            src_img.split("/api/generations/")[1].split("/")[0]
            if "/api/generations/" in src_img
            else src_img
        )
        gens = await store.read_list(GENERATIONS_FILE.name)
        found = next((g for g in gens if g.get("id") == gen_id), None)
        if found:
            if found.get("filePath"):
                src_img = found["filePath"]
            if found.get("prompt") and (
                not base_prompt or base_prompt.startswith("Maintain exact subject")
            ):
                base_prompt = f"{found['prompt']} — {base_prompt}"

    # Si la source est une vidéo, on extrait une frame de référence haute fidélité
    is_video_src = any(
        src_img.lower().endswith(ext) for ext in (".mp4", ".mov", ".webm", ".mkv", ".avi")
    )
    if is_video_src:
        src_path = Path(src_img)
        src_is_file = await asyncio.to_thread(src_path.is_file)
        if src_is_file:
            ffmpeg_path = Path("/home/instructeur/.local/bin/ffmpeg")
            has_ffmpeg = await asyncio.to_thread(ffmpeg_path.exists)
            ffmpeg_bin = str(ffmpeg_path) if has_ffmpeg else (shutil.which("ffmpeg") or "ffmpeg")
            await asyncio.to_thread(UPLOADS_DIR.mkdir, parents=True, exist_ok=True)
            frame_filename = f"matrix_src_{uuid.uuid4().hex[:8]}.png"
            frame_path = UPLOADS_DIR / frame_filename
            cmd = [
                str(ffmpeg_bin),
                "-y",
                "-ss",
                "00:00:01",
                "-i",
                str(src_path),
                "-vframes",
                "1",
                str(frame_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if frame_path.is_file():
                src_img = str(frame_path.resolve())

    jobs: list[dict[str, Any]] = []
    for preset in ANGLE_ORBIT_PRESETS:
        angle_prompt = f"[{preset['label']}] {preset['directive']} {base_prompt}"
        req = GenerationCreateRequest(
            prompt=angle_prompt,
            modelId=payload.modelId,
            type="image",
            parameters=GenerationParameters(
                seed=0,
                aspectRatio=payload.aspectRatio,
                resolution=payload.resolution,
                duration="1s",
                horizontalAngle=preset["h"],
                verticalAngle=preset["v"],
                zoomFactor=preset["z"],
            ),
            references=GenerationReferences(imageRefs=[src_img] if src_img else []),
            projectId=payload.projectId,
            tags=["angle-matrix", preset["label"]],
            cameraAngleLabel=preset["label"],
        )
        gen = await orchestrator.submit_generation(req)
        jobs.append(
            {
                "taskId": gen.id,
                "generationId": gen.id,
                "cameraAngleLabel": preset["label"],
                "status": gen.status.value,
            }
        )

    return {"count": len(jobs), "jobs": jobs}


@router.post(
    "/generate/extract-last-frame",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def extract_last_frame_from_generation(
    payload: ExtractFrameRequest,
    store: JSONDocumentStore = Depends(get_json_store),
) -> dict[str, Any]:
    """Module C : Extrait la dernière frame d'une vidéo (Start/End Frame)."""
    gens = await store.read_list(GENERATIONS_FILE.name)
    found = next((g for g in gens if g.get("id") == payload.generationId), None)
    if not found or not found.get("filePath"):
        raise HTTPException(status_code=404, detail="Génération ou fichier média introuvable")

    src_path = Path(found["filePath"])
    src_is_file = await asyncio.to_thread(src_path.is_file)
    if not src_is_file:
        raise HTTPException(status_code=404, detail="Fichier introuvable sur disque")

    await asyncio.to_thread(UPLOADS_DIR.mkdir, parents=True, exist_ok=True)
    out_filename = f"frame_{payload.generationId}_{uuid.uuid4().hex[:6]}.png"
    out_path = UPLOADS_DIR / out_filename

    if src_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        await asyncio.to_thread(shutil.copy2, src_path, out_path)
    else:
        ffmpeg_path = Path("/home/instructeur/.local/bin/ffmpeg")
        has_ffmpeg = await asyncio.to_thread(ffmpeg_path.exists)
        ffmpeg_bin = str(ffmpeg_path) if has_ffmpeg else (shutil.which("ffmpeg") or "ffmpeg")
        cmd = [
            str(ffmpeg_bin),
            "-sseof",
            "-0.1",
            "-i",
            str(src_path),
            "-update",
            "1",
            "-q:v",
            "2",
            str(out_path),
            "-y",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if not out_path.is_file():
            raise HTTPException(status_code=500, detail="Échec d'extraction de la frame via FFmpeg")

    return {
        "filePath": str(out_path.resolve()),
        "filename": out_filename,
        "url": f"/api/uploads/{out_filename}",
    }


@router.post(
    "/generate/plan-timeline",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def plan_timeline_preview(
    payload: TimelinePlanRequest,
) -> dict[str, Any]:
    """Analyse un scénario et renvoie l'estimation de durée et le découpage en plans."""
    plan = await _default_story_director.plan_timeline(
        prompt=payload.prompt,
        target_total_sec=payload.targetDurationSec,
        max_segment_sec=payload.maxSegmentSec,
    )
    return plan.model_dump()


@router.post(
    "/generate/media",
    status_code=202,
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def generate_media(
    payload: GenerationCreateRequest,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
    gateway: WorkerGateway = Depends(get_worker_gateway),
    contract_engine: ContractEngine = Depends(get_contract_engine),
) -> dict[str, Any]:
    """Déclenche une génération asynchrone (image, vidéo, audio, lip-sync, upscale, 3D)."""
    # 1. Validation stricte des contraintes de contrats d'entrée (acceptedInputTypes)
    try:
        models = await gateway.list_models()
        target_model = next((m for m in models if m.get("id") == payload.modelId), None)
        if target_model:
            caps = target_model.get("capabilities", {})
            valid, err_msg = contract_engine.validate_accepted_input_types(caps, payload.references)
            if not valid:
                raise HTTPException(status_code=422, detail=err_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Vérification des capacités worker non bloquante : %s", e)

    try:
        gen = await orchestrator.submit_generation(payload)
        return {
            "taskId": gen.id,
            "generationId": gen.id,
            "status": "pending",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Échec de soumission de génération : {e}",
        ) from e


@router.get("/tasks/{task_id}/status")
async def get_task_status_stream(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> StreamingResponse:
    """Abonnement au flux SSE temps réel d'une tâche de génération."""
    task = await orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        orchestrator.subscribe_task(task_id),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=dict[str, Any],
    dependencies=[Depends(verify_trusted_origin)],
)
async def cancel_task(
    task_id: str,
    orchestrator: TaskOrchestrator = Depends(get_task_orchestrator),
) -> dict[str, Any]:
    """Annule une tâche de génération de façon idempotente."""
    res = await orchestrator.cancel_task(task_id)
    if res.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return res
