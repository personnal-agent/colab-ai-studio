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


def test_task_status_enum_values():
    assert [s.value for s in TaskStatus] == [
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
    ]


def test_generation_parameters_defaults_and_validation():
    params = GenerationParameters(
        seed=4289102,
        aspectRatio="16:9",
        resolution="720p",
        duration="5s",
    )
    assert params.seed == 4289102
    assert params.aspectRatio == "16:9"
    assert params.frameRate is None
    assert params.audio is None
    assert params.validate() is True
    payload = params.to_payload_dict()
    assert payload["seed"] == 4289102
    assert payload["aspectRatio"] == "16:9"


def test_generation_parameters_invalid_aspect_ratio():
    # Ratios étendus valides
    p1 = GenerationParameters(seed=1, aspectRatio="8:1")
    assert p1.aspectRatio == "8:1"
    p2 = GenerationParameters(seed=2, aspectRatio="2:3")
    assert p2.aspectRatio == "2:3"

    with pytest.raises(ValidationError):
        GenerationParameters(
            seed=1,
            aspectRatio="invalid_ratio",
            resolution="720p",
            duration="5s",
        )
    with pytest.raises(ValidationError):
        GenerationParameters(
            seed=1,
            aspectRatio="0:10",
            resolution="720p",
            duration="5s",
        )


def test_generation_references_empty_and_methods():
    refs = GenerationReferences()
    assert refs.has_visual_references() is False
    refs.imageRefs.append("data/assets/start.png")
    assert refs.has_visual_references() is True
    refs.clear_references()
    assert refs.has_visual_references() is False
    assert refs.imageRefs == []


def test_brand_kit_snapshot_primary_color():
    snapshot = BrandKitSnapshot(
        id="bk_apple",
        name="Apple Style",
        overview="Clean minimal.",
        colors=["#000000", "#FFFFFF"],
        logos=["data/assets/logos/apple.png"],
        fonts=["SF Pro Display"],
        guidelines=["Keep it simple."],
    )
    assert snapshot.get_primary_color() == "#000000"
    tokens = snapshot.format_prompt_tokens()
    assert "[Brand: Apple Style]" in tokens
    assert "#000000" in tokens

    empty_colors = BrandKitSnapshot(
        id="bk_empty",
        name="Empty",
        overview="No colors.",
    )
    assert empty_colors.get_primary_color() is None


def test_brand_kit_create_snapshot():
    kit = BrandKit(
        id="bk_apple_visuals",
        name="Apple Style",
        overview="Minimal aesthetic.",
        logos=[
            Logo(
                id="ast_logo_01",
                filePath="data/assets/logos/apple_white.png",
                label="Logo Principal",
            )
        ],
        colors=[
            Color(hex="#000000", label="Noir Sidéral", isDominant=True),
            Color(hex="#FFFFFF", label="Blanc Pur", isDominant=False),
        ],
        fonts=[Font(family="SF Pro Display", weight="600")],
        referenceImages=[Asset(id="ast_ref_01", filePath="data/assets/refs/shot.jpg")],
        guidelines=[
            Guideline(kind="do", text="Privilégier la lumière naturelle."),
            Guideline(kind="dont", text="Ne jamais surcharger."),
        ],
    )
    snapshot = kit.create_snapshot()
    assert snapshot.id == kit.id
    assert snapshot.name == kit.name
    assert snapshot.colors == ["#000000", "#FFFFFF"]
    assert snapshot.logos == ["data/assets/logos/apple_white.png"]
    assert snapshot.fonts == ["SF Pro Display"]
    assert len(snapshot.guidelines) == 2
    context = kit.compile_context()
    assert "Apple Style" in context


def test_brand_kit_color_hex_validation():
    with pytest.raises(ValidationError):
        Color(hex="invalid_hex")


def test_project_instantiation():
    proj = Project(
        id="proj_court_metrage_01",
        name="Court-métrage Brume",
        description="Scènes de cinématique en extérieur",
        colorTag="#3B82F6",
        storagePath="/home/omni/Videos/Projet_Brume",
    )
    assert proj.id == "proj_court_metrage_01"
    assert proj.storagePath == "/home/omni/Videos/Projet_Brume"


def test_project_invalid_color_tag():
    with pytest.raises(ValidationError):
        Project(id="p1", name="Test", colorTag="red")


def test_generation_lifecycle_methods():
    gen = Generation(
        id="gen_20261009_143022_a8f9",
        status=TaskStatus.PENDING,
        mediaType="video",
        prompt="Un plan aérien cinématique...",
        modelId="seedance-2.5-pro",
        modelName="Seedance 2.5",
        parameters=GenerationParameters(
            seed=42,
            aspectRatio="16:9",
            resolution="720p",
            duration="5s",
        ),
    )
    assert gen.is_completed() is False
    assert gen.get_output_path() is None
    assert gen.toggle_favorite() is True
    assert gen.isFavorite is True
    assert gen.toggle_favorite() is False
    assert gen.isFavorite is False

    gen.mark_failed("Worker unreachable")
    assert gen.status == TaskStatus.FAILED
    assert gen.errorMessage == "Worker unreachable"


def test_studio_config_and_local_worker_url():
    config = StudioConfig()
    assert config.executionMode == ExecutionMode.COLAB
    assert config.is_colab_active() is True
    assert config.local.workerUrl == "http://127.0.0.1:8190"
    assert config.local.is_cpu_fallback() is True
    assert config.get_active_endpoint() == "https://xxxx-xx-xx.ngrok-free.app"

    config.set_execution_mode(ExecutionMode.LOCAL)
    assert config.executionMode == ExecutionMode.LOCAL
    assert config.is_colab_active() is False
    assert config.get_active_endpoint() == "http://127.0.0.1:8190"


def test_colab_config_methods():
    colab = ColabConfig(tunnelUrl="https://colab-tunnel.ngrok-free.app")
    assert colab.is_connected() is True
    colab.touch_ping()
    assert colab.lastPing is not None

    empty = ColabConfig(tunnelUrl="")
    assert empty.is_connected() is False


def test_compiler_llm_config_methods(monkeypatch):
    cfg = CompilerLlmConfig(apiKeyEnv="TEST_LLM_KEY")
    assert cfg.is_configured() is False
    assert cfg.get_api_key() is None

    monkeypatch.setenv("TEST_LLM_KEY", "secret-key-123")
    assert cfg.is_configured() is True
    assert cfg.get_api_key() == "secret-key-123"

    explicit = CompilerLlmConfig(apiKey="explicit-key")
    assert explicit.is_configured() is True
    assert explicit.get_api_key() == "explicit-key"


def test_llm_proxy_config_methods():
    cfg = LlmProxyConfig(port=8000)
    assert cfg.is_running() is True
    assert cfg.get_base_url() == "http://127.0.0.1:8000"
