"""Routes de gestion et d'introspection du serveur MCP Local de Colab AI Studio (Module F).

Inspiré de companion/mcp_routes.py d'ArtCraft MCP, adapté pour piloter le studio localement.
Expose :
- GET /api/mcp/health
- POST /api/mcp/start
- POST /api/mcp/stop
- GET /api/mcp/tools
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from app.api.routes_crud import verify_trusted_origin
from app.config import REPO_ROOT

router = APIRouter(prefix="/api/mcp", tags=["MCP"])

_mcp_process: asyncio.subprocess.Process | None = None

MCP_TOOLS_CATALOG: list[dict[str, Any]] = [
    {
        "name": "colab_estimate_workload",
        "description": "Estime le nombre de plans, durée, temps GPU et VRAM requise.",
    },
    {
        "name": "colab_generate_video",
        "description": "Lance une génération vidéo locale (simple ou chaînée multi-plans 10s).",
    },
    {
        "name": "colab_generate_image",
        "description": "Lance une génération d'image haute fidélité locale (Qwen, NoctQ, Flux).",
    },
    {
        "name": "colab_generate_angle_matrix",
        "description": "Génère 4 angles de caméra orbitaux cohérents depuis une image source.",
    },
    {
        "name": "colab_upscale_4k",
        "description": "Lance un upscaling 4K / 8K d'une image ou vidéo (Topaz / Real-ESRGAN).",
    },
    {
        "name": "colab_create_character",
        "description": "Crée une fiche personnage persistante (@Nom) avec identité visuelle fixe.",
    },
    {
        "name": "colab_list_characters",
        "description": "Liste toutes les fiches personnages enregistrées (@Nom).",
    },
    {
        "name": "colab_list_generations",
        "description": "Recherche et filtre les créations de la galerie (1-5★, tags, séquences).",
    },
]


def _get_mcp_script_path() -> Path:
    return REPO_ROOT / "scripts" / "colab_mcp_server.py"


@router.get("/health")
async def mcp_health() -> dict[str, Any]:
    """Retourne l'état du serveur MCP local et le catalogue d'outils exposés."""
    script_path = _get_mcp_script_path()
    running = _mcp_process is not None and _mcp_process.returncode is None
    return {
        "running": running,
        "pid": _mcp_process.pid if _mcp_process else None,
        "returncode": _mcp_process.returncode if _mcp_process else None,
        "scriptPath": str(script_path),
        "available": script_path.is_file(),
        "toolsCount": len(MCP_TOOLS_CATALOG),
        "tools": MCP_TOOLS_CATALOG,
    }


@router.get("/tools")
async def mcp_tools() -> list[dict[str, Any]]:
    """Retourne la liste des outils MCP exposés par Colab AI Studio."""
    return MCP_TOOLS_CATALOG


@router.post("/start", dependencies=[Depends(verify_trusted_origin)])
async def mcp_start() -> dict[str, Any]:
    """Démarre le sous-processus MCP local en arrière-plan."""
    global _mcp_process

    if _mcp_process is not None and _mcp_process.returncode is None:
        return {
            "started": False,
            "running": True,
            "reason": "MCP server already running",
            "pid": _mcp_process.pid,
        }

    script_path = _get_mcp_script_path()
    if not script_path.is_file():
        return {"started": False, "running": False, "reason": f"Script introuvable: {script_path}"}

    _mcp_process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return {
        "started": True,
        "running": True,
        "pid": _mcp_process.pid,
        "scriptPath": str(script_path),
    }


@router.post("/stop", dependencies=[Depends(verify_trusted_origin)])
async def mcp_stop() -> dict[str, Any]:
    """Arrête proprement le sous-processus MCP local s'il est en cours d'exécution."""
    global _mcp_process

    if _mcp_process is None or _mcp_process.returncode is not None:
        return {"stopped": False, "running": False, "reason": "MCP server not running"}

    pid = _mcp_process.pid
    with contextlib.suppress(ProcessLookupError):
        _mcp_process.terminate()
        try:
            await asyncio.wait_for(_mcp_process.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            _mcp_process.kill()
            await _mcp_process.wait()

    return {"stopped": True, "running": False, "pid": pid}
