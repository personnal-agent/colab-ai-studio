#!/usr/bin/env python3
"""Serveur MCP (Model Context Protocol) JSON-RPC 2.0 via stdio pour Colab AI Studio.

Permet à n'importe quel agent IA (Claude Desktop, Antigravity, Cursor, Windsurf)
de piloter directement Colab AI Studio en local (estimation GPU/VRAM, génération vidéo
chaînée, génération image, matrice 4 angles caméra, upscaling 4K, fiches personnages @Nom).
"""

from __future__ import annotations

import http.client
import json
import os
import sys
from typing import Any
from urllib.parse import urlparse

STUDIO_API_BASE = os.environ.get("COLAB_STUDIO_API_URL", "http://127.0.0.1:8000")

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "name": "colab_estimate_workload",
        "description": (
            "Estime le découpage en plans (10s max), la durée totale, le temps GPU "
            "et la VRAM requise."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt ou scénario multi-plans"},
                "modelId": {"type": "string", "default": "minimax-h3"},
                "type": {"type": "string", "default": "video"},
                "duration": {"type": "string", "default": "auto"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "colab_generate_video",
        "description": "Lance une génération vidéo simple ou chaînée sur Colab AI Studio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "negativePrompt": {"type": "string"},
                "modelId": {"type": "string", "default": "minimax-h3"},
                "aspectRatio": {"type": "string", "default": "9:16"},
                "resolution": {"type": "string", "default": "1080p"},
                "duration": {"type": "string", "default": "auto"},
                "startFrame": {"type": "string"},
                "endFrame": {"type": "string"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "colab_generate_image",
        "description": "Lance une génération d'image locale sur Colab AI Studio.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "negativePrompt": {"type": "string"},
                "modelId": {"type": "string", "default": "qwen-image-2.1"},
                "aspectRatio": {"type": "string", "default": "9:16"},
                "resolution": {"type": "string", "default": "1024x1024"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "colab_generate_angle_matrix",
        "description": (
            "Génère 4 angles de caméra orbitaux cohérents (Left, Right, High, Zoom) "
            "depuis une image ou génération."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sourceImage": {
                    "type": "string",
                    "description": "Chemin ou ID de génération source",
                },
                "prompt": {
                    "type": "string",
                    "default": (
                        "Maintain exact subject details and lighting while "
                        "rotating camera perspective."
                    ),
                },
                "modelId": {"type": "string", "default": "qwen-image-2.1"},
            },
            "required": ["sourceImage"],
        },
    },
    {
        "name": "colab_upscale_4k",
        "description": "Lance un upscaling 4K sur une image ou une vidéo existante.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Chemin du fichier ou ID de génération (ex: gen_xxx)",
                },
                "resolution": {"type": "string", "default": "4K"},
            },
            "required": ["source"],
        },
    },
    {
        "name": "colab_create_character",
        "description": "Crée une fiche personnage réutilisable (@Nom) avec prompt fixe.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "physicalPrompt": {"type": "string"},
                "referenceImagePath": {"type": "string"},
                "voiceStyle": {"type": "string", "default": "feminine_soft"},
            },
            "required": ["name", "physicalPrompt"],
        },
    },
    {
        "name": "colab_list_characters",
        "description": "Liste tous les personnages enregistrés dans Colab AI Studio.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "colab_list_generations",
        "description": "Liste les créations de la galerie avec filtrage optionnel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mediaType": {"type": "string"},
                "minRating": {"type": "integer"},
                "tag": {"type": "string"},
                "q": {"type": "string"},
            },
        },
    },
]


def _api_request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    parsed = urlparse(STUDIO_API_BASE)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 8000)
    conn_cls = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    conn = conn_cls(host, port, timeout=30.0)
    try:
        data = json.dumps(body) if body is not None else None
        headers = {
            "Content-Type": "application/json",
            "Origin": "http://localhost:5173",
        }
        conn.request(method, path, body=data, headers=headers)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        return json.loads(raw)
    finally:
        conn.close()


def handle_tool_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Exécute un outil MCP contre l'API locale de Colab AI Studio."""
    try:
        if name == "colab_estimate_workload":
            res = _api_request(
                "POST",
                "/api/generate/estimate",
                {
                    "prompt": args.get("prompt", ""),
                    "modelId": args.get("modelId", "minimax-h3"),
                    "type": args.get("type", "video"),
                    "duration": args.get("duration", "auto"),
                },
            )
        elif name == "colab_generate_video":
            res = _api_request(
                "POST",
                "/api/generate/media",
                {
                    "modelId": args.get("modelId", "minimax-h3"),
                    "prompt": args.get("prompt", ""),
                    "negativePrompt": args.get("negativePrompt"),
                    "type": "video",
                    "parameters": {
                        "seed": 0,
                        "aspectRatio": args.get("aspectRatio", "9:16"),
                        "resolution": args.get("resolution", "1080p"),
                        "duration": args.get("duration", "auto"),
                    },
                    "references": {
                        "startFrame": args.get("startFrame"),
                        "endFrame": args.get("endFrame"),
                    },
                },
            )
        elif name == "colab_generate_image":
            res = _api_request(
                "POST",
                "/api/generate/media",
                {
                    "modelId": args.get("modelId", "qwen-image-2.1"),
                    "prompt": args.get("prompt", ""),
                    "negativePrompt": args.get("negativePrompt"),
                    "type": "image",
                    "parameters": {
                        "seed": 0,
                        "aspectRatio": args.get("aspectRatio", "9:16"),
                        "resolution": args.get("resolution", "1024x1024"),
                        "duration": "1s",
                    },
                },
            )
        elif name == "colab_generate_angle_matrix":
            res = _api_request(
                "POST",
                "/api/generate/angle-matrix",
                {
                    "sourceImage": args.get("sourceImage", ""),
                    "prompt": args.get(
                        "prompt",
                        (
                            "Maintain exact subject details and lighting while "
                            "rotating camera perspective."
                        ),
                    ),
                    "modelId": args.get("modelId", "qwen-image-2.1"),
                },
            )
        elif name == "colab_upscale_4k":
            res = _api_request(
                "POST",
                "/api/generate/media",
                {
                    "modelId": "topaz-gigapixel-pro",
                    "prompt": f"Upscale 4K: {args.get('source', '')}",
                    "type": "upscale",
                    "parameters": {
                        "seed": 0,
                        "aspectRatio": "16:9",
                        "resolution": args.get("resolution", "4K"),
                        "duration": "5s",
                    },
                    "references": {"upscaleSource": args.get("source", "")},
                },
            )
        elif name == "colab_create_character":
            res = _api_request(
                "POST",
                "/api/characters",
                {
                    "name": args.get("name", ""),
                    "physicalPrompt": args.get("physicalPrompt", ""),
                    "referenceImagePath": args.get("referenceImagePath"),
                    "voiceStyle": args.get("voiceStyle", "feminine_soft"),
                },
            )
        elif name == "colab_list_characters":
            res = _api_request("GET", "/api/characters")
        elif name == "colab_list_generations":
            res = _api_request("GET", "/api/generations")
        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Outil MCP inconnu : {name}"}],
            }

        return {
            "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]
        }
    except Exception as exc:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Erreur lors de l'appel {name}: {exc}"}],
        }


def process_jsonrpc_message(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Traite un message JSON-RPC 2.0 MCP entrant et retourne la réponse."""
    method = msg.get("method", "")
    req_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "colab-ai-studio-mcp", "version": "1.0.0"},
            },
        }
    if method.startswith("notifications/"):
        return None
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS_SCHEMA},
        }
    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        result = handle_tool_call(tool_name, arguments)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


def main() -> None:
    for line in sys.stdin:
        trimmed = line.strip()
        if not trimmed:
            continue
        try:
            msg = json.loads(trimmed)
        except json.JSONDecodeError:
            continue
        resp = process_jsonrpc_message(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
