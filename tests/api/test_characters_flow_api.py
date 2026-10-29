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
async def test_character_crud_with_archetypes_and_anchors(client: AsyncClient) -> None:
    # 1. Création avec les champs Google Flow Pro
    payload = {
        "name": "Professeur Chronos",
        "physicalPrompt": "Old eccentric inventor with wild silver hair and steampunk goggles",
        "archetype": "The Eccentric",
        "visualAnchors": ["brass goggles", "tweed vest", "silver pocket watch"],
        "voiceProfileId": "voice_eccentric_old_01",
        "voiceStyle": "masculine_quirky",
        "enginePreference": "hybrid",
    }
    resp = await client.post("/api/characters", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    char_id = created["id"]
    assert created["name"] == "Professeur Chronos"
    assert created["archetype"] == "The Eccentric"
    assert created["visualAnchors"] == ["brass goggles", "tweed vest", "silver pocket watch"]
    assert created["voiceProfileId"] == "voice_eccentric_old_01"
    assert created["enginePreference"] == "hybrid"

    # 2. GET individuel
    resp_get = await client.get(f"/api/characters/{char_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == char_id

    # 3. GET 404 sur ID inexistant
    resp_404 = await client.get("/api/characters/non_existent_id")
    assert resp_404.status_code == 404

    # 4. Filtrage par archétype
    resp_filter = await client.get("/api/characters?archetype=The%20Eccentric")
    assert resp_filter.status_code == 200
    assert len(resp_filter.json()) >= 1
    assert resp_filter.json()[0]["archetype"] == "The Eccentric"

    resp_empty = await client.get("/api/characters?archetype=The%20Wicked")
    assert resp_empty.status_code == 200
    assert len(resp_empty.json()) == 0

    # 5. PUT /api/characters/{id}
    update_payload = {
        "archetype": "The Wildcard",
        "visualAnchors": ["glowing monocle", "cybernetic arm"],
        "enginePreference": "local",
    }
    resp_put = await client.put(f"/api/characters/{char_id}", json=update_payload)
    assert resp_put.status_code == 200
    updated = resp_put.json()
    assert updated["archetype"] == "The Wildcard"
    assert updated["visualAnchors"] == ["glowing monocle", "cybernetic arm"]
    assert updated["enginePreference"] == "local"
    # Vérifier que les champs non modifiés sont préservés
    assert updated["name"] == "Professeur Chronos"

    # 6. DELETE /api/characters/{id}
    resp_del = await client.delete(f"/api/characters/{char_id}")
    assert resp_del.status_code == 200
    assert resp_del.json()["deleted"] is True

    # Vérification que le personnage est bien supprimé
    resp_check = await client.get(f"/api/characters/{char_id}")
    assert resp_check.status_code == 404
