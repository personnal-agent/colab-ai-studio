"""Extracteur d'identité Brand Kit (brand_extractor.py).

Gère l'extraction d'identité de marque selon SPECIFICATION.md §4.2.2 :
1. Extraction Blank (initialisation vide avec valeurs par défaut cohérentes).
2. Extraction depuis Brand Files : sauvegarde sous data/assets/ et extraction.
3. Extraction depuis Website (URL) : extraction du domaine et métadonnées.
"""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import re
import socket
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


def _validate_safe_url(url: str) -> None:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        msg = f"Protocole non supporté : '{scheme}'. Seuls http et https sont autorisés."
        raise ValueError(msg)

    hostname = parsed.hostname
    if not hostname:
        msg = f"URL invalide, nom d'hôte manquant : '{url}'"
        raise ValueError(msg)

    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1"):
        msg = f"Accès interdit aux adresses locales ou privées : '{hostname}'"
        raise ValueError(msg)

    port = parsed.port or (443 if scheme == "https" else 80)
    try:
        addr_infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        msg = f"Impossible de résoudre le nom d'hôte '{hostname}' : {e}"
        raise ValueError(msg) from e

    for _, _, _, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
        ):
            msg = (
                f"Accès refusé : l'hôte '{hostname}' ({ip_str}) "
                f"résout vers une adresse IP privée ou réservée."
            )
            raise ValueError(msg)


async def _fetch_safe_website(initial_url: str, max_redirects: int = 5) -> httpx.Response:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ColabAIStudio/1.0)"}
    current_url = initial_url
    redirect_count = 0

    async with httpx.AsyncClient(
        timeout=5.0,
        follow_redirects=False,
        headers=headers,
    ) as client:
        while True:
            # 1. Validation de l'adresse de destination (SSRF check à chaque saut)
            _validate_safe_url(current_url)

            # 2. Requête HTTP
            try:
                resp = await client.get(current_url)
            except (httpx.RequestError, OSError) as e:
                msg = f"Impossible de contacter le site '{current_url}' : {e}"
                raise ValueError(msg) from e

            # 3. Contrôle des redirections (3xx)
            if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                redirect_count += 1
                if redirect_count > max_redirects:
                    msg = f"Nombre maximal de redirections dépassé ({max_redirects})"
                    raise ValueError(msg)
                location = resp.headers["location"]
                current_url = urljoin(str(resp.url), location)
                continue

            # 4. Vérification code statut final
            if resp.status_code >= 400:
                msg = f"Le site {current_url} a retourné une erreur HTTP {resp.status_code}"
                raise ValueError(msg)

            return resp


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

        resp = await _fetch_safe_website(clean_url)
        html = resp.text

        # 1. Overview depuis <title> et <meta name="description">
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
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
                and clean_font.lower() not in {"inherit", "sans-serif", "serif", "monospace"}
                and clean_font not in seen_fonts
            ):
                seen_fonts.add(clean_font)
                fonts.append(Font(family=clean_font))
                if len(fonts) >= 3:
                    break

        # 4. Favicon / icône (résolu depuis l'adresse finale de la réponse)
        icon_match = re.search(
            r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\'](.*?)["\']',
            html,
            re.IGNORECASE,
        )
        if icon_match:
            base_url = str(resp.url) if hasattr(resp, "url") else clean_url
            icon_url = urljoin(base_url, icon_match.group(1))
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
