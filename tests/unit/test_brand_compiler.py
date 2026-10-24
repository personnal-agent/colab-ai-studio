"""Tests unitaires pour BrandContextCompiler (app/services/brand_compiler.py)."""

from __future__ import annotations

import httpx
import pytest

from app.models.domain import Asset, BrandKit, Color, CompilerLlmConfig, Font, Guideline, Logo
from app.services.brand_compiler import BrandContextCompiler, CompiledBrandContext


@pytest.fixture
def sample_brand_kit() -> BrandKit:
    return BrandKit(
        id="bk_acme",
        name="Acme Studios",
        overview="Futuristic minimalism with cinematic lighting",
        colors=[
            Color(hex="#0A84FF", label="Electric Blue", isDominant=True),
            Color(hex="#FFFFFF", label="Pure White"),
        ],
        fonts=[Font(family="Cabinet Grotesk"), Font(family="Inter")],
        logos=[Logo(id="l1", filePath="/data/assets/acme_logo.png", label="Main Logo")],
        referenceImages=[
            Asset(id="ast_1", filePath="/data/assets/ref1.jpg"),
            Asset(id="ast_2", filePath="/data/assets/ref2.jpg"),
        ],
        guidelines=[
            Guideline(kind="do", text="Keep compositions uncluttered and high contrast"),
            Guideline(kind="dont", text="Do not use saturated yellow or cartoonish shaders"),
        ],
    )


@pytest.mark.asyncio
async def test_compile_without_brand_kit():
    compiler = BrandContextCompiler()
    res = await compiler.compile("A misty neon forest", None, ["/u1.jpg", "/u2.jpg"], 3)
    assert isinstance(res, CompiledBrandContext) and res.prompt == "A misty neon forest"
    assert res.negative_prompt == "" and res.image_refs == ["/u1.jpg", "/u2.jpg"]
    assert res.snapshot is None


@pytest.mark.asyncio
async def test_compile_deterministic_fallback_when_no_api_key(sample_brand_kit):
    compiler = BrandContextCompiler()
    res = await compiler.compile(
        "A hovercar racing", sample_brand_kit, ["/car.jpg"], 4, CompilerLlmConfig(apiKey=None)
    )
    assert "[Brand Identity: Acme Studios]" in res.prompt
    assert "Palette: #0A84FF, #FFFFFF" in res.prompt
    assert "Do not use saturated yellow" in res.negative_prompt
    assert res.image_refs == [
        "/car.jpg",
        "/data/assets/ref1.jpg",
        "/data/assets/ref2.jpg",
        "/data/assets/acme_logo.png",
    ]
    assert "Here is the brand logo" in res.prompt
    assert res.snapshot.id == "bk_acme"


@pytest.mark.asyncio
async def test_compile_llm_synthesis_success(sample_brand_kit, monkeypatch):
    compiler = BrandContextCompiler()
    cfg = CompilerLlmConfig(apiKey="valid_secret_key")

    mock_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                '{"prompt": "Cinematic hovercar with electric blue accents", '
                                '"negative_prompt": "cartoonish shaders"}'
                            )
                        }
                    ]
                }
            }
        ]
    }

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return httpx.Response(
                200,
                request=httpx.Request("POST", "https://mock.url"),
                json=mock_resp,
            )

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: MockAsyncClient())
    res = await compiler.compile("A hovercar in rain", sample_brand_kit, [], 2, cfg)
    assert "electric blue accents" in res.prompt
    assert "cartoonish shaders" in res.negative_prompt


@pytest.mark.asyncio
async def test_compile_llm_fallback_on_timeout_or_error(sample_brand_kit, monkeypatch):
    compiler = BrandContextCompiler()

    class FailingAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            raise httpx.TimeoutException("LLM timeout")

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: FailingAsyncClient())
    res = await compiler.compile(
        "A hovercar in rain",
        sample_brand_kit,
        [],
        2,
        CompilerLlmConfig(apiKey="valid_secret_key"),
    )
    assert "[Brand Identity: Acme Studios]" in res.prompt
    assert "brand inconsistency, distorted logo" in res.negative_prompt


@pytest.mark.asyncio
async def test_image_slots_prioritization_and_logo_instruction(sample_brand_kit):
    compiler = BrandContextCompiler()
    r1 = await compiler.compile("Test", sample_brand_kit, ["/u1.jpg", "/u2.jpg"], 3)
    assert r1.image_refs == ["/u1.jpg", "/u2.jpg", "/data/assets/ref1.jpg"]
    assert "Here is the brand logo" not in r1.prompt

    r2 = await compiler.compile("Test", sample_brand_kit, ["/u1.jpg", "/u2.jpg", "/u3.jpg"], 2)
    assert r2.image_refs == ["/u1.jpg", "/u2.jpg"]
    assert "Here is the brand logo" not in r2.prompt


@pytest.mark.asyncio
async def test_text_only_model_drops_all_images(sample_brand_kit):
    compiler = BrandContextCompiler()
    res = await compiler.compile("Kling prompt", sample_brand_kit, ["/u1.jpg"], 0)
    assert res.image_refs == [] and "[Brand Identity: Acme Studios]" in res.prompt
    assert "Here is the brand logo" not in res.prompt
