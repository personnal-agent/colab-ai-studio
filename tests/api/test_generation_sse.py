"""Tests d'intégration d'API pour les routes de génération et flux SSE."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_generation import get_task_orchestrator
from app.main import app
from app.models.domain import Generation


class StubOrchestrator:
    def __init__(self):
        self.submitted = []
        self.cancelled = []

    async def submit_generation(self, payload):
        self.submitted.append(payload)
        gen = Generation(
            id="gen_mock123",
            prompt=payload.prompt,
            modelId=payload.modelId,
            modelName="Mock Model",
            parameters=payload.parameters,
        )
        return gen

    async def subscribe_task(self, task_id: str) -> AsyncGenerator[str, None]:
        yield 'event: status\ndata: {"status": "running", "progress": 10}\n\n'
        await asyncio.sleep(0.01)
        yield 'event: progress\ndata: {"status": "running", "progress": 50}\n\n'
        await asyncio.sleep(0.01)
        yield (
            "event: completed\ndata: "
            '{"status": "completed", "progress": 100, "filePath": "/out/mock.mp4"}\n\n'
        )

    async def cancel_task(self, task_id: str):
        self.cancelled.append(task_id)
        return {"status": "cancelled", "taskId": task_id}


@pytest.mark.asyncio
async def test_generation_workflow_and_sse():
    stub = StubOrchestrator()
    app.dependency_overrides[get_task_orchestrator] = lambda: stub

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # 1. POST /api/generate/media
        req_payload = {
            "prompt": "A cyber cat running in rain",
            "modelId": "wan2.1-t2v-14b",
            "type": "video",
            "parameters": {"seed": 42, "aspectRatio": "16:9"},
        }
        post_resp = await client.post(
            "/api/generate/media",
            json=req_payload,
            headers={"Origin": "http://localhost:5173"},
        )
        assert post_resp.status_code == 202
        body = post_resp.json()
        assert body["taskId"] == "gen_mock123"
        assert body["status"] == "pending"

        # 2. GET /api/tasks/{task_id}/status (SSE)
        sse_resp = await client.get("/api/tasks/gen_mock123/status")
        assert sse_resp.status_code == 200
        assert "text/event-stream" in sse_resp.headers["content-type"]
        sse_text = sse_resp.text
        assert "event: status" in sse_text
        assert "event: progress" in sse_text
        assert "event: completed" in sse_text

        # 3. POST /api/tasks/{task_id}/cancel
        cancel_resp = await client.post(
            "/api/tasks/gen_mock123/cancel",
            headers={"Origin": "http://localhost:5173"},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"
        assert "gen_mock123" in stub.cancelled

    app.dependency_overrides.clear()
