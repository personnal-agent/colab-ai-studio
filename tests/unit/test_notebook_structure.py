"""Validation structurelle du notebook colab_worker.ipynb."""

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "colab_worker.ipynb"


def test_notebook_exists():
    assert NOTEBOOK_PATH.exists(), f"Le notebook {NOTEBOOK_PATH} est introuvable."


def test_notebook_valid_json_and_format():
    content = NOTEBOOK_PATH.read_text(encoding="utf-8")
    data = json.loads(content)

    assert "nbformat" in data
    assert data["nbformat"] >= 4
    assert "cells" in data
    assert isinstance(data["cells"], list)
    assert len(data["cells"]) >= 4


def test_notebook_essential_commands_and_keywords():
    content = NOTEBOOK_PATH.read_text(encoding="utf-8")

    # Vérification des commandes indispensables
    assert "nvidia-smi" in content
    assert "fastapi" in content.lower()
    assert "uvicorn" in content.lower()
    assert "modelswapper" in content.lower() or "model_swapper" in content.lower()
    assert "tunnel" in content.lower() or "ngrok" in content.lower()
