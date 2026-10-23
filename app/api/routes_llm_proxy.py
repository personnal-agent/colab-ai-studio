"""Routeur Proxy LLM OpenAI-compatible (app/api/routes_llm_proxy.py).

Expose POST /v1/chat/completions compatible OpenAI en relayant vers le worker actif
(Colab distant ou local) selon 08-sequence-proxy-llm.svg :
- Flux nominal SSE streaming clôturé par data: [DONE].
- Mode non-streaming (stream=False) synchrone standard.
- Gestion d'interruption propre (request.is_disconnected() == True) avec libération GPU amont
  sans émission de token sur la socket rompue.
"""

from __future__ import annotations

import contextlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.config import CONFIG_FILE, DATA_DIR
from app.models.domain import StudioConfig
from app.services.worker_gateway import WorkerGateway, WorkerGatewayError
from app.storage.json_store import JSONDocumentStore

router = APIRouter(tags=["Proxy LLM OpenAI"])

_json_store = JSONDocumentStore(DATA_DIR)
_gateway = WorkerGateway(store=_json_store)


async def stream_openai_chat(
    request: Request,
    gateway: WorkerGateway,
    body: dict[str, Any],
    timeout: float,
) -> AsyncIterator[str]:
    _mode, base_url = await gateway.get_active_worker_url()
    client = gateway._get_client()
    request_id = body.get("requestId") or f"chat_{uuid.uuid4().hex[:12]}"
    payload = {**body, "stream": True}

    client_aborted = False
    try:
        async with client.stream(
            "POST",
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=timeout,
        ) as upstream_response:
            if upstream_response.status_code != 200:
                raw_err = await upstream_response.aread()
                yield f"data: {json.dumps({'error': raw_err.decode(errors='replace')})}\n\n"
                return

            async for line in upstream_response.aiter_lines():
                if await request.is_disconnected():
                    client_aborted = True
                    break

                clean_line = line.strip()
                if not clean_line:
                    continue
                yield f"{clean_line}\n\n"
                if clean_line == "data: [DONE]":
                    break
    except httpx.RequestError as exc:
        if not client_aborted:
            yield f"data: {json.dumps({'error': f'Erreur amont worker: {exc}'})}\n\n"
    finally:
        if client_aborted:
            # Signal d'interruption et libération VRAM vers le worker amont
            with contextlib.suppress(Exception):
                await client.post(
                    f"{base_url}/v1/chat/cancel",
                    json={"requestId": request_id},
                    timeout=5.0,
                )


@router.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    raw_config = await _json_store.read_dict(CONFIG_FILE.name, default=StudioConfig().model_dump())
    config = StudioConfig.model_validate(raw_config)

    if not config.llmProxy.enabled:
        raise HTTPException(
            status_code=503,
            detail="Le proxy LLM est désactivé dans config.json",
        )

    try:
        _mode, base_url = await _gateway.get_active_worker_url()
    except WorkerGatewayError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Corps JSON invalide") from exc

    is_stream = bool(body.get("stream", False))

    if is_stream:
        return StreamingResponse(
            stream_openai_chat(
                request=request,
                gateway=_gateway,
                body=body,
                timeout=float(config.llmProxy.timeout),
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Mode synchrone non-streaming
    client = _gateway._get_client()
    try:
        res = await client.post(
            f"{base_url}/v1/chat/completions",
            json=body,
            timeout=float(config.llmProxy.timeout),
        )
        return Response(
            content=res.content,
            status_code=res.status_code,
            media_type="application/json",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503, detail=f"Worker LLM injoignable sur {base_url} : {exc}"
        ) from exc
