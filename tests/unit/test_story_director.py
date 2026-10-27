import pytest

from app.services.story_director import (
    StoryDirector,
    build_chained_segment_prompt,
    calculate_segments_duration,
    extract_character_profiles,
    parse_explicit_script_segments,
)


def test_calculate_segments_duration_467s():
    durations = calculate_segments_duration(467.0, max_segment_sec=10.0)
    assert len(durations) == 47
    assert durations[:46] == [10.0] * 46
    assert durations[46] == 7.0
    assert sum(durations) == pytest.approx(467.0, 0.1)


def test_calculate_segments_duration_exact_multiples():
    durations = calculate_segments_duration(30.0, max_segment_sec=10.0)
    assert durations == [10.0, 10.0, 10.0]


def test_calculate_segments_duration_short():
    durations = calculate_segments_duration(5.0, max_segment_sec=10.0)
    assert durations == [5.0]


def test_parse_explicit_script_segments():
    text = (
        "Global scene context: A woman in a room.\n"
        "Plan 1 : Elle se réveille et ouvre les yeux.\n"
        "Plan 2 : Elle s'assoit au bord du lit.\n"
        "Plan 3 : Elle regarde par la fenêtre en souriant.\n"
    )
    ctx, segs = parse_explicit_script_segments(text)
    assert "Global scene context" in ctx
    assert len(segs) == 3
    assert segs[0] == "Elle se réveille et ouvre les yeux."
    assert segs[1] == "Elle s'assoit au bord du lit."
    assert segs[2] == "Elle regarde par la fenêtre en souriant."


@pytest.mark.asyncio
async def test_story_director_heuristic_plan():
    director = StoryDirector()
    prompt = (
        "A cinematic shot of a young woman walking on a beach at sunset. "
        "She turns around to face the camera. The wind blows her hair softly as "
        "waves crash in the background."
    )
    plan = await director.plan_timeline(prompt, target_total_sec=25.0, max_segment_sec=10.0)
    assert plan.num_segments == 3
    assert [s.duration_sec for s in plan.segments] == [10.0, 10.0, 5.0]
    assert plan.total_duration_sec == pytest.approx(25.0)


def test_extract_character_profiles_from_script():
    segs = [
        "Plan 1: Extreme close-up of a table in a sunlit room.",
        (
            "Plan 2: Medium shot showing a fit 37-year-old American man in his late "
            "thirties with short buzzed hair and stubble, wearing only black boxer briefs."
        ),
        (
            "Plan 3: Close-up of a woman in her late twenties with long dark hair tied "
            "back messily, wearing a white button-down shirt."
        ),
        "Plan 4: Medium two-shot from behind the table showing both characters.",
    ]
    profiles = extract_character_profiles("", segs)
    assert len(profiles) >= 2
    male = next((p for p in profiles if p["gender"] == "male"), None)
    female = next((p for p in profiles if p["gender"] == "female"), None)

    assert male is not None
    assert "37-year-old" in male["description"]
    assert male["first_seen_segment"] == 2

    assert female is not None
    assert "late twenties" in female["description"]
    assert female["first_seen_segment"] == 3


def test_build_chained_segment_prompt_anchors():
    profiles = [
        {
            "id": "char_1_male",
            "gender": "male",
            "label": "Male character",
            "description": "fit 37-year-old American man with short buzzed hair and stubble",
        },
        {
            "id": "char_2_female",
            "gender": "female",
            "label": "Female character",
            "description": "woman in her late twenties with long dark hair tied back messily",
        },
    ]

    # Plan 1 (T2V)
    p1 = build_chained_segment_prompt(1, 4, "Extreme close-up of table", "Living room", profiles)
    assert "Scene & Setting Overview" in p1
    assert "Character Identity Continuity Anchors" in p1
    assert "fit 37-year-old" in p1

    # Plan 4 (I2V after cuts)
    p4 = build_chained_segment_prompt(
        4, 4, "Medium two-shot showing both characters", "Living room", profiles
    )
    assert "The scene opens directly on <Picture 1>" in p4
    assert "Strictly preserve the exact same character identities" in p4
    assert "Male character: fit 37-year-old American man" in p4
    assert "Female character: woman in her late twenties" in p4
    assert "Current shot action continuing smoothly from <Picture 1>" in p4
