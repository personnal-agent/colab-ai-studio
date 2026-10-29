from app.models.domain import (
    AgentInstruction,
    Character,
    CharacterArchetype,
)


def test_character_archetypes_enum_contains_google_flow_archetypes() -> None:
    expected_archetypes = {
        "The Eccentric",
        "The Professional",
        "The Wildcard",
        "The Familiar",
        "The Wicked",
        "The Fantastical",
    }
    actual_archetypes = {arch.value for arch in CharacterArchetype}
    assert actual_archetypes == expected_archetypes


def test_character_backward_compatibility_defaults() -> None:
    char = Character(
        id="char_001",
        name="Chantal",
        triggerToken="[Chantal]",
        physicalPrompt="Woman with curly dark hair",
    )
    assert char.archetype == CharacterArchetype.THE_FAMILIAR
    assert char.visualAnchors == []
    assert char.voiceProfileId is None
    assert char.enginePreference == "local"
    assert char.updatedAt is not None


def test_character_with_flow_pro_fields() -> None:
    char = Character(
        id="char_002",
        name="Landry",
        triggerToken="[Landry]",
        physicalPrompt="Tall athletic man with beard",
        archetype=CharacterArchetype.THE_PROFESSIONAL,
        visualAnchors=["navy blue suit", "gold watch", "short fade haircut"],
        voiceProfileId="voice_landry_deep_fr",
        voiceStyle="masculine_deep",
        enginePreference="hybrid",
    )
    assert char.archetype == CharacterArchetype.THE_PROFESSIONAL
    assert len(char.visualAnchors) == 3
    assert "navy blue suit" in char.visualAnchors
    assert char.voiceProfileId == "voice_landry_deep_fr"
    assert char.enginePreference == "hybrid"

    # Vérification de sérialisation dictionnaire
    data = char.model_dump()
    assert data["archetype"] == "The Professional"
    assert data["enginePreference"] == "hybrid"
    assert data["visualAnchors"] == ["navy blue suit", "gold watch", "short fade haircut"]


def test_agent_instruction_model() -> None:
    inst = AgentInstruction(
        id="inst_001",
        title="Style Cinématographique Nuit",
        description="Toujours appliquer un éclairage clair-obscur néon avec reflets mouillés.",
        isActive=True,
        referenceAssetUrls=["/api/uploads/neon_ref_01.png"],
        order=1,
    )
    assert inst.id == "inst_001"
    assert inst.title == "Style Cinématographique Nuit"
    assert inst.isActive is True
    assert inst.referenceAssetUrls == ["/api/uploads/neon_ref_01.png"]
    assert inst.order == 1
    assert inst.createdAt is not None
    assert inst.updatedAt is not None

    dumped = inst.model_dump()
    assert dumped["title"] == "Style Cinématographique Nuit"
    assert dumped["order"] == 1
