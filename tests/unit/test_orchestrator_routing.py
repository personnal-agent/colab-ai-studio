from __future__ import annotations

from app.api.routes_characters import compile_character_mentions
from app.models.domain import Character, CharacterArchetype
from app.services.story_director import build_chained_segment_prompt


def test_compile_character_mentions_injects_visual_anchors() -> None:
    char = Character(
        id="char_01",
        name="Clara",
        triggerToken="@Clara",
        physicalPrompt="Young woman with auburn hair and green eyes",
        archetype=CharacterArchetype.THE_FAMILIAR,
        visualAnchors=["green silk scarf", "silver ring", "freckles"],
        voiceProfileId="voice_clara_warm",
    )
    raw_characters = [char.model_dump()]

    prompt = "A cinematic traveling shot of @Clara walking in a rainy boulevard at dusk."
    compiled, matched_ids, matched_imgs, seed = compile_character_mentions(
        prompt, raw_characters
    )

    assert "char_01" in matched_ids
    # Doit contenir le bloc d'ancrage visuel pour Clara
    assert "[Visual Anchors for Clara: green silk scarf, silver ring, freckles]" in compiled
    assert "[Clara Identity: Young woman with auburn hair and green eyes]" in compiled
    assert "@Clara" not in compiled
    assert "Clara walking in a rainy boulevard" in compiled


def test_build_chained_segment_prompt_incorporates_anchors() -> None:
    char_profiles = [
        {
            "id": "char_01",
            "name": "Clara",
            "archetype": "The Familiar",
            "visualAnchors": ["green silk scarf", "silver ring"],
            "first_seen_segment": 1,
        }
    ]

    prompt = build_chained_segment_prompt(
        seg_idx=1,
        total_segs=3,
        action_prompt="Clara enters the old library.",
        scene_overview="A dramatic thriller scene in an ancient library.",
        char_profiles=char_profiles,
    )

    assert "The Familiar" in prompt or "green silk scarf" in prompt
    assert "Clara enters the old library" in prompt
