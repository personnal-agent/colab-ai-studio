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


def test_notebook_structure_and_content() -> None:
    """Vérifie l'existence, validité JSON et étapes indispensables du notebook."""
    notebook_path = REPO_ROOT / "colab_worker.ipynb"
    assert notebook_path.is_file(), f"{notebook_path} manquant."
    data = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert data.get("nbformat") == 4 and len(data.get("cells", [])) >= 4

    sources = [
        "".join(c.get("source", []))
        for c in data["cells"]
        if c.get("cell_type") in {"code", "markdown"}
    ]
    txt = "\n".join(sources).lower()
    for kw in ("nvidia-smi", "fastapi", "uvicorn", "modelswapper", "http"):
        assert kw in txt
    assert any(t in txt for t in ("cloudflared", "ngrok", "tunnel"))
    assert any(s in txt for s in ("secret", "worker_secret"))
