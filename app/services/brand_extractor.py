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
from urllib.parse import urljoin, urlparse

import httpx

from app.models.domain import BrandKit, Color, Font, Logo


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


HEX_FINDER = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
FONT_FAMILY_FINDER = re.compile(r"font-family\s*:\s*([^;\}]+)", re.IGNORECASE)


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
        def _process_files() -> tuple[list[Logo], list[Color], list[Font]]:
            logos: list[Logo] = []
            extracted_colors: list[Color] = []
            extracted_fonts: list[Font] = []
            color_candidates: set[str] = set()
            seen_fonts: set[str] = set()

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

                # Polices de caractères binaires
                if ext in {".ttf", ".otf", ".woff", ".woff2"}:
                    font_family = Path(filename).stem.replace("-", " ").title()
                    if font_family not in seen_fonts:
                        seen_fonts.add(font_family)
                        extracted_fonts.append(
                            Font(family=font_family, filePath=str(dest_path.resolve()))
                        )

                # Recherche heuristique de codes HEX et font-family dans les fichiers textuels
                if ext in {".svg", ".txt", ".json", ".css"}:
                    with contextlib.suppress(Exception):
                        text = content.decode("utf-8", errors="ignore")
                        for hex_match in HEX_FINDER.findall(text):
                            color_candidates.add(hex_match.upper())

                        for font_match in FONT_FAMILY_FINDER.findall(text):
                            primary_font = font_match.split(",")[0].strip().strip("'\"")
                            if (
                                primary_font
                                and primary_font.lower()
                                not in {"inherit", "sans-serif", "serif", "monospace"}
                                and primary_font not in seen_fonts
                            ):
                                seen_fonts.add(primary_font)
                                extracted_fonts.append(Font(family=primary_font))

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

            return logos, extracted_colors, extracted_fonts

        logos, colors, fonts = await asyncio.to_thread(_process_files)
        kit_id = f"bk_{uuid.uuid4().hex[:8]}"
        now = _utc_now_iso()
        return BrandKit(
            id=kit_id,
            name=name.strip() or "Brand Kit extrait",
            overview=overview.strip() or f"Style extrait des fichiers de {name}",
            logos=logos,
            colors=colors,
            fonts=fonts,
            createdAt=now,
            updatedAt=now,
        )

    async def extract_from_website(self, name: str, website_url: str) -> BrandKit:
        clean_url = website_url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = f"https://{clean_url}"

        domain = urlparse(clean_url).netloc or clean_url
        kit_id = f"bk_{uuid.uuid4().hex[:8]}"
        now = _utc_now_iso()

        logos: list[Logo] = []
        colors: list[Color] = []
        fonts: list[Font] = []
        overview_text = f"Identité visuelle issue du site {domain}"

        with contextlib.suppress(Exception):
            headers = {"User-Agent": "Mozilla/5.0 (compatible; ColabAIStudio/1.0)"}
            async with httpx.AsyncClient(
                timeout=5.0, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get(clean_url)
                if resp.status_code < 400:
                    html = resp.text

                    # 1. Overview depuis <title> et <meta name="description">
                    title_match = re.search(
                        r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
                    )
                    desc_match = re.search(
                        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
                        html,
                        re.IGNORECASE | re.DOTALL,
                    )
                    title = title_match.group(1).strip() if title_match else ""
                    desc = desc_match.group(1).strip() if desc_match else ""
                    if desc:
                        overview_text = f"{title} - {desc}" if title else desc
                    elif title:
                        overview_text = title

                    # 2. Couleurs hex depuis HTML et styles inline
                    hex_candidates = set(HEX_FINDER.findall(html))
                    for idx, hex_code in enumerate(sorted(hex_candidates)[:5]):
                        colors.append(
                            Color(
                                hex=hex_code.upper(),
                                label=f"Couleur web {idx + 1}",
                                isDominant=(idx == 0),
                            )
                        )

                    # 3. Polices depuis font-family
                    seen_fonts = set()
                    for font_match in FONT_FAMILY_FINDER.findall(html):
                        clean_font = font_match.split(",")[0].strip().strip("'\"")
                        if (
                            clean_font
                            and clean_font.lower()
                            not in {"inherit", "sans-serif", "serif", "monospace"}
                            and clean_font not in seen_fonts
                        ):
                            seen_fonts.add(clean_font)
                            fonts.append(Font(family=clean_font))
                            if len(fonts) >= 3:
                                break

                    # 4. Favicon / icône
                    icon_match = re.search(
                        r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\'](.*?)["\']',
                        html,
                        re.IGNORECASE,
                    )
                    if icon_match:
                        icon_url = urljoin(clean_url, icon_match.group(1))
                        logos.append(
                            Logo(
                                id=f"ast_logo_{uuid.uuid4().hex[:6]}",
                                filePath=icon_url,
                                label="Favicon",
                            )
                        )

        if not colors:
            colors = [
                Color(hex="#000000", label="Primaire", isDominant=True),
                Color(hex="#FFFFFF", label="Fond", isDominant=False),
            ]

        return BrandKit(
            id=kit_id,
            name=name.strip() or domain,
            overview=overview_text,
            logos=logos,
            colors=colors,
            fonts=fonts,
            createdAt=now,
            updatedAt=now,
        )
