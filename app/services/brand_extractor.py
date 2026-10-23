"""Extracteur d'identité Brand Kit (brand_extractor.py).

Gère l'extraction d'identité de marque selon SPECIFICATION.md §4.2.2 :
1. Extraction Blank (initialisation vide avec valeurs par défaut cohérentes).
2. Extraction depuis Brand Files : sauvegarde sous data/assets/ et extraction.
3. Extraction depuis Website (URL) : extraction du domaine et métadonnées.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models.domain import BrandKit, Color, Logo


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


HEX_FINDER = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")


class BrandKitExtractor:
    def __init__(self, assets_dir: Path | str) -> None:
        self.assets_dir = Path(assets_dir).resolve()
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def create_blank(self, name: str, overview: str = "") -> BrandKit:
        kit_id = f"bk_{uuid.uuid4().hex[:8]}"
        now = _utc_now_iso()
        return BrandKit(
            id=kit_id,
            name=name.strip() or "Nouveau Brand Kit",
            overview=overview.strip() or f"Identité visuelle {name}",
            createdAt=now,
            updatedAt=now,
        )

    async def extract_from_files(
        self,
        name: str,
        files: list[tuple[str, bytes]],  # (filename, binary_content)
        overview: str = "",
    ) -> BrandKit:
        def _process_files() -> tuple[list[Logo], list[Color]]:
            logos: list[Logo] = []
            extracted_colors: list[Color] = []
            color_candidates: set[str] = set()

            for filename, content in files:
                ext = Path(filename).suffix.lower()
                dest_name = f"ast_{uuid.uuid4().hex[:8]}_{Path(filename).name}"
                dest_path = self.assets_dir / dest_name
                dest_path.write_bytes(content)

                if ext in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
                    logos.append(
                        Logo(
                            id=f"ast_logo_{uuid.uuid4().hex[:6]}",
                            filePath=str(dest_path.resolve()),
                            label=Path(filename).stem,
                        )
                    )

                # Recherche heuristique de codes HEX dans les fichiers texte/svg/pdf textuels
                if ext in {".svg", ".txt", ".json", ".css"}:
                    with contextlib.suppress(Exception):
                        text = content.decode("utf-8", errors="ignore")
                        for hex_match in HEX_FINDER.findall(text):
                            color_candidates.add(hex_match.upper())

            # Si au moins une couleur est trouvée, on l'ajoute
            for idx, hex_code in enumerate(sorted(color_candidates)[:5]):
                extracted_colors.append(
                    Color(
                        hex=hex_code,
                        label=f"Teinte {idx + 1}",
                        isDominant=(idx == 0),
                    )
                )

            # Si aucune couleur n'a pu être extraite, palette neutre par défaut
            if not extracted_colors:
                extracted_colors = [
                    Color(hex="#000000", label="Noir", isDominant=True),
                    Color(hex="#FFFFFF", label="Blanc", isDominant=False),
                ]

            return logos, extracted_colors

        logos, colors = await asyncio.to_thread(_process_files)
        kit_id = f"bk_{uuid.uuid4().hex[:8]}"
        now = _utc_now_iso()
        return BrandKit(
            id=kit_id,
            name=name.strip() or "Brand Kit extrait",
            overview=overview.strip() or f"Style extrait des fichiers de {name}",
            logos=logos,
            colors=colors,
            createdAt=now,
            updatedAt=now,
        )

    async def extract_from_website(self, name: str, website_url: str) -> BrandKit:
        kit_id = f"bk_{uuid.uuid4().hex[:8]}"
        now = _utc_now_iso()
        # Heuristique d'aperçu d'URL
        clean_url = website_url.strip()
        domain = clean_url.replace("https://", "").replace("http://", "").split("/")[0]
        overview = f"Style et identité visuelle du site {domain}"
        return BrandKit(
            id=kit_id,
            name=name.strip() or domain,
            overview=overview,
            colors=[
                Color(hex="#000000", label="Primaire", isDominant=True),
                Color(hex="#FFFFFF", label="Fond", isDominant=False),
            ],
            createdAt=now,
            updatedAt=now,
        )
