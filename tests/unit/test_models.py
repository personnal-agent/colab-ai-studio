"""Tests unitaires du modèle de domaine Pydantic v2 (Step 2 du Plan 01)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.domain import (
    Asset,
    BrandKit,
    BrandKitSnapshot,
    ColabConfig,
    Color,
    CompilerLlmConfig,
    ExecutionMode,
    Font,
    Generation,
    GenerationParameters,
    GenerationReferences,
    Guideline,
    LlmProxyConfig,
    Logo,
    Project,
    StudioConfig,
    TaskStatus,
)


def test_task_status_and_params():
    assert {s.value for s in TaskStatus} == {
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
    }
    p = GenerationParameters(
        seed=42, aspectRatio="16:9", resolution="720p", duration="5s",
        talkingStyle="Expressive", upscaleScale="4x", upscaleQuality="Slow",
        upscaleFrameRate="60fps",
    )
    assert (
        p.seed == 42
        and p.aspectRatio == "16:9"
        and p.talkingStyle == "Expressive"
        and p.upscaleScale == "4x"
        and p.validate()
        and p.to_payload_dict()["seed"] == 42
    )
    assert GenerationParameters(seed=1, aspectRatio="8:1").aspectRatio == "8:1"
    assert GenerationParameters(seed=2, aspectRatio="2:3").aspectRatio == "2:3"
    for bad in ("invalid", "0:10"):
        with pytest.raises(ValidationError):
            GenerationParameters(seed=1, aspectRatio=bad)


def test_generation_references_and_lifecycle():
    refs = GenerationReferences()
    assert not refs.has_visual_references()
    refs.imageRefs.append("start.png")
    assert refs.has_visual_references()
    refs.clear_references()
    assert not refs.has_visual_references() and refs.imageRefs == []

    gen = Generation(
        id="g_test",
        status=TaskStatus.PENDING,
        prompt="misty forest",
        modelId="m1",
        modelName="Model 1",
        parameters=GenerationParameters(seed=42),
    )
    assert not gen.is_completed() and gen.get_output_path() is None
    assert gen.toggle_favorite() is True and gen.toggle_favorite() is False
    gen.mark_failed("Unreachable")
    assert gen.status == TaskStatus.FAILED and gen.errorMessage == "Unreachable"


def test_brand_kit_snapshot_and_context():
    snap = BrandKitSnapshot(
        id="bk_1",
        name="Style",
        overview="Minimal.",
        colors=["#000000", "#FFFFFF"],
        fonts=["SF Pro"],
        guidelines=["Simple."],
    )
    assert snap.get_primary_color() == "#000000" and "[Brand: Style]" in snap.format_prompt_tokens()
    assert BrandKitSnapshot(id="bk_e", name="Empty", overview="").get_primary_color() is None

    kit = BrandKit(
        id="bk_full",
        name="Apple Style",
        overview="Aesthetic",
        logos=[Logo(id="l1", filePath="logo.png")],
        colors=[Color(hex="#000000", label="Noir"), Color(hex="#FFFFFF", label="Blanc")],
        fonts=[Font(family="SF Pro")],
        referenceImages=[Asset(id="a1", filePath="shot.jpg")],
        guidelines=[Guideline(kind="do", text="Light"), Guideline(kind="dont", text="Noise")],
    )
    s = kit.create_snapshot()
    assert s.id == kit.id and s.colors == ["#000000", "#FFFFFF"] and len(s.guidelines) == 2
    assert "Apple Style" in kit.compile_context()
    with pytest.raises(ValidationError):
        Color(hex="invalid")


def test_project_and_configs(monkeypatch):
    p = Project(id="p1", name="Court", colorTag="#3B82F6", storagePath="/home/omni/Videos")
    assert p.id == "p1" and p.storagePath == "/home/omni/Videos"
    with pytest.raises(ValidationError):
        Project(id="p2", name="Bad", colorTag="red")

    cfg = StudioConfig()
    assert (
        cfg.is_colab_active()
        and cfg.local.workerUrl == "http://127.0.0.1:8190"
        and cfg.local.is_cpu_fallback()
    )
    cfg.set_execution_mode(ExecutionMode.LOCAL)
    assert (
        cfg.executionMode == ExecutionMode.LOCAL
        and cfg.get_active_endpoint() == "http://127.0.0.1:8190"
    )

    colab = ColabConfig(tunnelUrl="https://colab.ngrok-free.app")
    colab.touch_ping()
    assert colab.is_connected() and colab.lastPing and not ColabConfig(tunnelUrl="").is_connected()

    monkeypatch.setenv("TEST_KEY", "secret-123")
    assert (
        CompilerLlmConfig(apiKeyEnv="TEST_KEY").get_api_key() == "secret-123"
        and CompilerLlmConfig(apiKey="direct").get_api_key() == "direct"
        and not CompilerLlmConfig(apiKeyEnv="DUMMY_VAR_NOT_SET").is_configured()
    )

    proxy = LlmProxyConfig(port=8000)
    assert proxy.is_running() and proxy.get_base_url() == "http://127.0.0.1:8000"
