"""Proxy LLM streaming compatible OpenAI (app/api/routes_llm_proxy.py).

Conforme à 08-sequence-proxy-llm.svg :
- Expose POST /v1/chat/completions (compatible OpenAI, IDE Cursor, Continue, etc.)
- Relaye en streaming SSE le flux amont du worker Colab ou Local.
- Gestion d'interruption propre (request.is_disconnected() == True) :
  envoie POST /v1/chat/cancel au worker pour libérer immédiatement la VRAM GPU,
  et rompt la socket côté backend sans émettre data: [DONE].
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.routes_models import get_worker_gateway
from app.services.worker_gateway import (
    WorkerGateway,
    WorkerNotConfiguredError,
    WorkerUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["LLM Proxy"])


class ChatMessage(BaseModel):
    role: str
    content: str | list[Any]


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = "default"
    messages: list[ChatMessage]
    stream: bool = True
    temperature: float | None = 0.7
    max_tokens: int | None = None
    extra_body: dict[str, Any] = Field(default_factory=dict)


@router.post("/chat/completions")
async def chat_completions_proxy(
    payload: ChatCompletionRequest,
    request: Request,
    gateway: WorkerGateway = Depends(get_worker_gateway),
) -> Any:
    """Relais de chat completions compatible API OpenAI avec streaming et annulation VRAM."""
    try:
        _, base_url = await gateway.get_active_worker_url()
    except (WorkerNotConfiguredError, WorkerUnavailableError) as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    request_id = f"chat_{uuid.uuid4().hex[:10]}"
    req_dict = payload.model_dump(exclude_none=True)
    req_dict["requestId"] = request_id
    worker_headers = await gateway.get_worker_headers()

    # Si le client ne demande pas le streaming, appel synchrone simple
    if not payload.stream:
        try:
            resp = await gateway.http_client.post(
                f"{base_url}/v1/chat/completions",
                json=req_dict,
                headers=worker_headers,
                timeout=120.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Erreur amont worker LLM : {e}") from e

    async def stream_generator() -> AsyncGenerator[str, None]:
        url = f"{base_url}/v1/chat/completions"
        stop_event = asyncio.Event()
        is_cancelled = False

        async def cancel_upstream() -> None:
            nonlocal is_cancelled
            if not is_cancelled:
                is_cancelled = True
                logger.info(
                    "Interruption client sur %s. Annulation sur le worker %s.",
                    request_id,
                    base_url,
                )
                try:
                    # Sanctuarisé par asyncio.shield contre l'annulation ASGI
                    await asyncio.shield(
                        gateway.http_client.post(
                            f"{base_url}/v1/chat/cancel",
                            json={"requestId": request_id},
                            headers=worker_headers,
                            timeout=5.0,
                        )
                    )
                except Exception as cancel_err:
                    logger.warning(
                        "Échec notification annulation LLM sur %s : %s",
                        base_url,
                        cancel_err,
                    )

        async def watch_disconnect() -> None:
            while not stop_event.is_set():
                if await request.is_disconnected():
                    stop_event.set()
                    await cancel_upstream()
                    return
                await asyncio.sleep(0.1)

        disconnect_task = asyncio.create_task(watch_disconnect())
        completed_normally = False
        try:
            async with gateway.http_client.stream(
                "POST",
                url,
                json=req_dict,
                headers=worker_headers,
                timeout=120.0,
            ) as upstream_resp:
                upstream_resp.raise_for_status()
                async for line in upstream_resp.aiter_lines():
                    if stop_event.is_set() or await request.is_disconnected():
                        stop_event.set()
                        await cancel_upstream()
                        return

                    if line:
                        yield f"{line}\n\n"
                        if "[DONE]" in line:
                            completed_normally = True
        except (asyncio.CancelledError, GeneratorExit):
            stop_event.set()
            await cancel_upstream()
            raise
        except Exception as e:
            if not stop_event.is_set() and not await request.is_disconnected():
                logger.error("Erreur relayage stream LLM %s : %s", request_id, e)
                err_data = json.dumps({"error": {"message": str(e), "type": "upstream_error"}})
                yield f"data: {err_data}\n\n"
        finally:
            stop_event.set()
            if not completed_normally:
                await cancel_upstream()
            disconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await disconnect_task

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(stream_generator(), media_type="text/event-stream", headers=headers)
