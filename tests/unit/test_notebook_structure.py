"""Tests unitaires de validation structurelle du notebook Colab Worker.

Fichier: tests/unit/test_notebook_structure.py
Vérifie la conformité au format Jupyter nbformat v4 et la présence des cellules indispensables :
- Détection et diagnostic GPU Tesla T4 (nvidia-smi)
- Installation des dépendances (FastAPI, Uvicorn, Pydantic, etc.)
- Configuration et initialisation du ModelSwapper
- Établissement du tunnel chiffré (Cloudflare / ngrok) et affichage de l'URL publique
"""

from __future__ import annotations

import json

from app.config import REPO_ROOT


def test_notebook_file_exists_and_valid_json() -> None:
    """Vérifie l'existence et la validité JSON du notebook colab_worker.ipynb."""
    notebook_path = REPO_ROOT / "colab_worker.ipynb"
    assert notebook_path.is_file(), f"Le fichier {notebook_path} est manquant."

    content = notebook_path.read_text(encoding="utf-8")
    data = json.loads(content)

    assert "cells" in data
    assert "metadata" in data
    assert data.get("nbformat") == 4
    assert isinstance(data["cells"], list)
    assert len(data["cells"]) >= 4


def test_notebook_cells_content() -> None:
    """Vérifie la présence des étapes obligatoires dans le notebook."""
    notebook_path = REPO_ROOT / "colab_worker.ipynb"
    data = json.loads(notebook_path.read_text(encoding="utf-8"))

    all_sources = [
        "".join(cell.get("source", []))
        for cell in data["cells"]
        if cell.get("cell_type") in {"code", "markdown"}
    ]
    combined_text = "\n".join(all_sources)

    # 1. Vérification GPU
    assert "nvidia-smi" in combined_text

    # 2. Dépendances worker
    assert "fastapi" in combined_text
    assert "uvicorn" in combined_text

    # 3. ModelSwapper & protocole VRAM
    assert "ModelSwapper" in combined_text

    # 4. Tunneling, sécurité & URL publique
    assert any(tunnel in combined_text.lower() for tunnel in ["cloudflared", "ngrok", "tunnel"])
    assert "http" in combined_text.lower()
    assert any(secret_kw in combined_text.lower() for secret_kw in ["secret", "worker_secret"])
