from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_crud import get_json_store
from app.main import app
from app.storage.json_store import JSONDocumentStore


@pytest.fixture
async def client(tmp_path):
    store = JSONDocumentStore(tmp_path)
    app.dependency_overrides[get_json_store] = lambda: store
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Origin": "http://localhost:5173"},
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_agent_instructions_lifecycle(client: AsyncClient) -> None:
    # 1. Liste initiale vide
    resp_init = await client.get("/api/agent-instructions")
    assert resp_init.status_code == 200
    assert resp_init.json() == []

    # 2. Création de deux instructions
    inst1_payload = {
        "title": "Style Néo-Noir",
        "description": "Utiliser des ombres très marquées et une lumière rasante néon.",
        "referenceAssetUrls": ["/api/uploads/neon_01.png"],
    }
    resp1 = await client.post("/api/agent-instructions", json=inst1_payload)
    assert resp1.status_code == 201
    created1 = resp1.json()
    id1 = created1["id"]
    assert created1["title"] == "Style Néo-Noir"
    assert created1["isActive"] is True
    assert created1["order"] == 0

    inst2_payload = {
        "title": "Continuité Vestimentaire",
        "description": (
            "Les personnages doivent conserver leur manteau d'hiver tout au long de la scène."
        ),
    }
    resp2 = await client.post("/api/agent-instructions", json=inst2_payload)
    assert resp2.status_code == 201
    created2 = resp2.json()
    id2 = created2["id"]
    assert created2["order"] == 1

    # 3. GET /api/agent-instructions/{id}
    resp_get = await client.get(f"/api/agent-instructions/{id1}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == id1

    # 4. PATCH toggle
    resp_toggle = await client.patch(f"/api/agent-instructions/{id1}/toggle")
    assert resp_toggle.status_code == 200
    assert resp_toggle.json()["isActive"] is False

    # 5. PUT update
    update_payload = {
        "title": "Style Cyberpunk Néo-Noir",
        "description": "Ambiance pluvieuse avec reflets holographiques intenses.",
    }
    resp_put = await client.put(f"/api/agent-instructions/{id1}", json=update_payload)
    assert resp_put.status_code == 200
    assert resp_put.json()["title"] == "Style Cyberpunk Néo-Noir"

    # 6. PUT reorder
    resp_reorder = await client.put(
        "/api/agent-instructions/reorder",
        json={"instructionIds": [id2, id1]},
    )
    assert resp_reorder.status_code == 200
    reordered = resp_reorder.json()
    assert reordered[0]["id"] == id2
    assert reordered[0]["order"] == 0
    assert reordered[1]["id"] == id1
    assert reordered[1]["order"] == 1

    # 7. DELETE
    resp_del = await client.delete(f"/api/agent-instructions/{id2}")
    assert resp_del.status_code == 200
    assert resp_del.json()["deleted"] is True

    # Vérification après suppression
    resp_final = await client.get("/api/agent-instructions")
    assert len(resp_final.json()) == 1
    assert resp_final.json()[0]["id"] == id1
