"""Tests unitaires pour BrandContextCompiler (Step 1 du Plan 02).

Vérifie :
1. Repli déterministe anglais immédiat en l'absence de clé API LLM ou en cas d'erreur.
2. Synthèse via LLM externe quand COMPILER_LLM_API_KEY est actif.
3. Priorité stricte des slots de référence :
   - Priorité 1 : userRefs sanctuarisés (tronqués aux N premiers si dépassement).
   - Priorité 2 : images de référence du kit.
   - Priorité 3 : logo de marque avec consigne explicite en anglais.
4. Repli texte seul si le modèle impose maxImageRefs == 0.
5. Génération du BrandKitSnapshot figé.
"""

from __future__ import annotations

import httpx
import pytest

from app.models.domain import (
    Asset,
    BrandKit,
    Color,
    Font,
    Guideline,
    Logo,
)
from app.services.brand_compiler import BrandContextCompiler


@pytest.fixture
def sample_apple_kit():
    return BrandKit(
        id="bk_apple_visuals",
        name="Apple Style",
        overview="Minimal aesthetic, neutral backgrounds, soft studio lighting.",
        logos=[
            Logo(
                id="ast_logo_01",
                filePath="data/assets/logos/apple_white.png",
                label="Logo Principal",
            )
        ],
        colors=[
            Color(hex="#000000", label="Noir", isDominant=True),
            Color(hex="#FFFFFF", label="Blanc", isDominant=False),
        ],
        fonts=[Font(family="SF Pro Display", weight="600")],
        referenceImages=[
            Asset(id="ast_ref_01", filePath="data/assets/refs/clean_product_shot.jpg")
        ],
        guidelines=[
            Guideline(kind="do", text="Always favor natural light and clean surfaces."),
            Guideline(kind="dont", text="Never overload with flashy graphic elements."),
        ],
    )


async def test_deterministic_fallback_when_no_api_key(sample_apple_kit):
    compiler = BrandContextCompiler(api_key=None)
    result = await compiler.compile(
        prompt="A photo of a smartwatch on a desk",
        kit=sample_apple_kit,
        user_refs=["user_ref_1.jpg"],
        max_image_refs=4,
    )

    assert "[Brand Identity: Apple Style]" in result.compiled_prompt
    assert "Minimal aesthetic" in result.compiled_prompt
    assert "#000000" in result.compiled_prompt
    assert "SF Pro Display" in result.compiled_prompt
    assert "Never overload" in result.negative_prompt
    assert "unapproved color palette" in result.negative_prompt

    # Vérification des slots
    assert len(result.assigned_image_refs) == 3
    assert result.assigned_image_refs[0] == "user_ref_1.jpg"
    assert result.assigned_image_refs[1] == "data/assets/refs/clean_product_shot.jpg"
    assert result.assigned_image_refs[2] == "data/assets/logos/apple_white.png"
    assert "Here is the brand logo" in result.compiled_prompt

    # Snapshot
    assert result.snapshot.id == sample_apple_kit.id
    assert result.snapshot.name == "Apple Style"


async def test_user_refs_priority_and_truncation(sample_apple_kit):
    compiler = BrandContextCompiler(api_key=None)
    # L'utilisateur dépose 3 références mais le modèle n'en accepte que 2
    user_refs = ["ref_u1.jpg", "ref_u2.jpg", "ref_u3.jpg"]
    result = await compiler.compile(
        prompt="A smartwatch",
        kit=sample_apple_kit,
        user_refs=user_refs,
        max_image_refs=2,
    )

    # Priorité 1 : les 2 premières userRefs remplissent tous les slots
    assert len(result.assigned_image_refs) == 2
    assert result.assigned_image_refs == ["ref_u1.jpg", "ref_u2.jpg"]
    # Ni les images du kit ni le logo ne doivent écraser les userRefs
    assert "data/assets/logos/apple_white.png" not in result.assigned_image_refs
    assert "Here is the brand logo" not in result.compiled_prompt


async def test_text_only_model_fallback(sample_apple_kit):
    compiler = BrandContextCompiler(api_key=None)
    result = await compiler.compile(
        prompt="A smartwatch",
        kit=sample_apple_kit,
        user_refs=["user_ref_1.jpg"],
        max_image_refs=0,
    )

    # Zéro image assignée
    assert result.assigned_image_refs == []
    # Mais le brief textuel de marque reste enrichi
    assert "[Brand Identity: Apple Style]" in result.compiled_prompt


async def test_llm_synthesis_when_api_key_present(sample_apple_kit):
    def mock_llm_handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Cinematic shot of a minimalist smartwatch on an ash-gray desk, "
                                "soft ambient lighting, clean lines, pristine elegance."
                            )
                        }
                    }
                ]
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_llm_handler))
    compiler = BrandContextCompiler(api_key="valid-key-test", client=mock_client)

    result = await compiler.compile(
        prompt="A photo of a smartwatch",
        kit=sample_apple_kit,
        user_refs=[],
        max_image_refs=2,
    )

    assert "pristine elegance" in result.compiled_prompt
    assert "unapproved color palette" in result.negative_prompt
