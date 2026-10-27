"""Configuration centralisée des chemins et de l'environnement Colab AI Studio."""

from __future__ import annotations

import os
from pathlib import Path

# Racine du dépôt (peut être surchargée par REPO_ROOT pour les tests)
REPO_ROOT: Path = Path(os.environ.get("COLAB_STUDIO_ROOT", Path(__file__).resolve().parent.parent))

DATA_DIR: Path = Path(os.environ.get("COLAB_STUDIO_DATA_DIR", REPO_ROOT / "data"))
ASSETS_DIR: Path = DATA_DIR / "assets"
UPLOADS_DIR: Path = DATA_DIR / "uploads"
OUTPUTS_DIR: Path = Path(os.environ.get("COLAB_STUDIO_OUTPUTS_DIR", REPO_ROOT / "outputs"))

# Chemins des fichiers documentaires JSON canoniques
GENERATIONS_FILE: Path = DATA_DIR / "generations.json"
BRAND_KITS_FILE: Path = DATA_DIR / "brand_kits.json"
PROJECTS_FILE: Path = DATA_DIR / "projects.json"
CONFIG_FILE: Path = DATA_DIR / "config.json"
CHARACTERS_FILE: Path = DATA_DIR / "characters.json"


def ensure_directories() -> None:
    """Crée les répertoires obligatoires avec permissions utilisateur."""
    for d in (DATA_DIR, ASSETS_DIR, UPLOADS_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
