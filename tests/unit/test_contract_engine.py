"""Tests unitaires pour le moteur de contrats ContractEngine (Omniforge v3)."""

from __future__ import annotations

from app.models.domain import GenerationReferences
from app.services.contract_engine import ContractEngine


def test_canvas_discipline_valid():
    engine = ContractEngine()
    canvas = {
        "layers": [
            {"id": "root", "width": 1920, "height": 1080, "x": 0, "y": 0},
            {"id": "child", "width": 400, "height": 300, "x": 50, "y": 50, "parentId": "root"},
        ]
    }
    valid, err = engine.validate_canvas_discipline(canvas)
    assert valid is True
    assert err is None


def test_canvas_discipline_negative_dimensions():
    engine = ContractEngine()
    canvas = {
        "layers": [
            {"id": "bad_layer", "width": -100, "height": 500, "x": 0, "y": 0},
        ]
    }
    valid, err = engine.validate_canvas_discipline(canvas)
    assert valid is False
    assert "largeur invalide" in str(err)


def test_canvas_discipline_cycle_detection():
    engine = ContractEngine()
    canvas = {
        "layers": [
            {"id": "l1", "width": 100, "height": 100, "parentId": "l2"},
            {"id": "l2", "width": 100, "height": 100, "parentId": "l1"},
        ]
    }
    valid, err = engine.validate_canvas_discipline(canvas)
    assert valid is False
    assert "Cycle hiérarchique détecté" in str(err)


def test_canvas_discipline_self_parent():
    engine = ContractEngine()
    canvas = {
        "layers": [
            {"id": "l1", "width": 100, "height": 100, "parentId": "l1"},
        ]
    }
    valid, err = engine.validate_canvas_discipline(canvas)
    assert valid is False
    assert "auto-référence parentale interdite" in str(err)


def test_anti_loop_guard():
    engine = ContractEngine(max_loop_iterations=2)
    session_id = "test-session-1"
    prompt = "generate landscape"

    # 1re soumission : valide
    valid, _ = engine.check_anti_loop(session_id, prompt)
    assert valid is True

    # 2e soumission identique : valide (atteint max_iterations=2)
    valid, _ = engine.check_anti_loop(session_id, prompt)
    assert valid is True

    # 3e soumission identique : boucle infinie bloquée
    valid, err = engine.check_anti_loop(session_id, prompt)
    assert valid is False
    assert "Garde anti-loop déclenchée" in str(err)

    # Mutation de prompt : débloqué
    new_prompt = "generate sunset landscape"
    valid, err = engine.check_anti_loop(session_id, new_prompt)
    assert valid is True
    assert err is None


def test_validate_accepted_input_types_nominal():
    engine = ContractEngine()
    capabilities = {"acceptedInputTypes": ["text", "image", "3d"]}
    refs = GenerationReferences(meshRef="/path/to/model.obj")

    valid, err = engine.validate_accepted_input_types(capabilities, refs)
    assert valid is True
    assert err is None


def test_validate_accepted_input_types_rejection():
    engine = ContractEngine()
    # Modèle purement text-to-video / text-to-image qui n'accepte pas les images de référence
    capabilities = {"acceptedInputTypes": ["text"]}
    refs = GenerationReferences(imageRefs=["/path/to/reference.png"])

    valid, err = engine.validate_accepted_input_types(capabilities, refs)
    assert valid is False
    assert "références de type 'image'" in str(err)
