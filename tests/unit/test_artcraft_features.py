"""Tests unitaires et d'intégration pour les 6 Modules ArtCraft (A, B, C, D, E, F)."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes_characters import compile_character_mentions, normalize_trigger_token
from app.main import app
from app.services.audio_weaver import extract_dialogues, synthesize_ambient_and_voice_wav


def test_normalize_trigger_token():
    assert normalize_trigger_token("Tomate") == "@Tomate"
    assert normalize_trigger_token("Super Concombre") == "@Super_Concombre"
    assert normalize_trigger_token("Clara", "@ClaraModel") == "@ClaraModel"


def test_compile_character_mentions():
    chars = [
        {
            "id": "char_1",
            "name": "Tomate",
            "triggerToken": "@Tomate",
            "physicalPrompt": "anthropomorphic ripe red tomato character with apron",
            "referenceImagePath": "/path/to/tomato.png",
            "defaultSeed": 4242,
        }
    ]

    prompt = "Plan 1: @Tomate smiles gently while looking out the window."
    compiled, ids, imgs, seed = compile_character_mentions(prompt, chars)

    assert "char_1" in ids
    assert "/path/to/tomato.png" in imgs
    assert seed == 4242
    assert "[Tomate Identity: anthropomorphic ripe red tomato character with apron]" in compiled
    assert "Tomate smiles gently" in compiled
    assert "@Tomate" not in compiled


def test_extract_dialogues_and_voice_style():
    prompt = (
        'The character whispers in a soft feminine voice "hello darling..." '
        'and then the man answers with a deep voice "good morning".'
    )
    dialogues = extract_dialogues(prompt)
    assert len(dialogues) == 2
    assert dialogues[0]["text"] == "hello darling..."
    assert dialogues[0]["voiceStyle"] == "whisper_intimate"
    assert dialogues[1]["text"] == "good morning"
    assert dialogues[1]["voiceStyle"] == "masculine_deep"


def test_synthesize_ambient_and_voice_wav(tmp_path: Path):
    wav_file = tmp_path / "test_audio.wav"
    dialogues = [{"text": "bonjour", "voiceStyle": "feminine_soft"}]
    res_path = synthesize_ambient_and_voice_wav(wav_file, duration_sec=2.0, dialogues=dialogues)
    assert res_path.exists()
    assert res_path.stat().st_size > 5000


@pytest.mark.asyncio
async def test_mcp_health_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/mcp/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data
        assert data["toolsCount"] >= 8
        assert any(t["name"] == "colab_estimate_workload" for t in data["tools"])


@pytest.mark.asyncio
async def test_workload_estimate_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/generate/estimate",
            json={
                "prompt": (
                    'Plan 1 (0:00-0:10): close up smiling "morning".\n'
                    "Plan 2 (0:10-0:20): walking outside."
                ),
                "modelId": "minimax-h3",
                "type": "video",
                "duration": "auto",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["numSegments"] == 2
        assert data["totalDurationSec"] == 20.0
        assert data["isChained"] is True
        assert data["detectedDialoguesCount"] >= 1
        assert data["estimatedVramGb"] > 15.0
