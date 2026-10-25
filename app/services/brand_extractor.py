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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.models.domain import BrandKit, Color, Font, Logo


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


HEX_FINDER = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
FONT_FAMILY_FINDER = re.compile(r"font-family\s*:\s*([^;\}]+)", re.IGNORECASE)


def _rank_colors(hex_matches: list[str]) -> list[Color]:
    counts = Counter(m.upper() for m in hex_matches)
    colors = [
        Color(hex=code, label=f"Teinte {i + 1}", isDominant=(i == 0))
        for i, (code, _) in enumerate(counts.most_common(5))
    ]
    return colors or [
        Color(hex="#000000", label="Noir", isDominant=True),
        Color(hex="#FFFFFF", label="Blanc", isDominant=False),
    ]


async def _validate_safe_url(url: str) -> None:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(
            f"Protocole non supporté : '{scheme}'. Seuls http et https sont autorisés."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"URL invalide, nom d'hôte manquant : '{url}'")

    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1") or any(
        lower_host.endswith(s)
        for s in (".local", ".localhost", ".internal", ".lan", ".arpa", ".home")
    ):
        raise ValueError(f"Accès interdit aux domaines internes ou privés : '{hostname}'")

    try:
        if not ipaddress.ip_address(hostname.strip("[]")).is_global:
            raise ValueError(f"Accès refusé : l'adresse IP '{hostname}' est privée ou réservée.")
    except ValueError as e:
        if "Accès refusé" in str(e):
            raise

    port = parsed.port or (443 if scheme == "https" else 80)
    try:
        addr_infos = await asyncio.to_thread(
            socket.getaddrinfo, hostname, port, proto=socket.IPPROTO_TCP
        )
    except socket.gaierror as e:
        raise ValueError(f"Impossible de résoudre le nom d'hôte '{hostname}' : {e}") from e

    for _, _, _, _, sockaddr in addr_infos:
        try:
            if not ipaddress.ip_address(sockaddr[0]).is_global:
                raise ValueError(
                    f"Accès refusé : l'hôte '{hostname}' ({sockaddr[0]}) résout vers une IP privée."
                )
        except ValueError as e:
            if "Accès refusé" in str(e):
                raise


async def _fetch_safe_website(initial_url: str, max_redirects: int = 5) -> httpx.Response:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ColabAIStudio/1.0)"}
    current_url = initial_url

    async with httpx.AsyncClient(timeout=5.0, follow_redirects=False, headers=headers) as client:
        for _ in range(max_redirects + 1):
            await _validate_safe_url(current_url)
            if not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+(?:/[^\s<>\"']*)?", current_url):
                raise ValueError(f"URL invalide ou non sécurisée : '{current_url}'")
            try:
                resp = await client.get(current_url)
            except (httpx.RequestError, OSError) as e:
                raise ValueError(f"Impossible de contacter le site '{current_url}' : {e}") from e

            # Contrôle anti-DNS-rebinding sur la socket connectée
            stream = getattr(resp, "extensions", {}).get("network_stream")
            if (
                stream
                and (addr := stream.get_extra_info("server_addr"))
                and isinstance(addr, tuple)
            ):
                is_priv = False
                with contextlib.suppress(ValueError):
                    is_priv = not ipaddress.ip_address(addr[0]).is_global
                if is_priv:
                    raise ValueError(f"Accès refusé : l'adresse IP '{addr[0]}' est privée.")

            if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                current_url = urljoin(str(resp.url), resp.headers["location"])
                await _validate_safe_url(current_url)
                continue

            if resp.status_code >= 400:
                raise ValueError(
                    f"Le site {current_url} a retourné une erreur HTTP {resp.status_code}"
                )
            return resp

    raise ValueError(f"Nombre maximal de redirections dépassé ({max_redirects})")


class BrandKitExtractor:
    def __init__(self, assets_dir: Path | str) -> None:
        self.assets_dir = Path(assets_dir).resolve()
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def create_blank(self, name: str, overview: str = "") -> BrandKit:
        now = _utc_now_iso()
        return BrandKit(
            id=f"bk_{uuid.uuid4().hex[:8]}",
            name=name.strip() or "Nouveau Brand Kit",
            overview=overview.strip() or f"Identité visuelle {name}",
            createdAt=now,
            updatedAt=now,
        )

    async def extract_from_files(
        self,
        name: str,
        files: list[tuple[str, bytes]],
        overview: str = "",
    ) -> BrandKit:
        def _process_files() -> tuple[list[Logo], list[Color], list[Font]]:
            logos: list[Logo] = []
            extracted_fonts: list[Font] = []
            color_candidates: list[str] = []
            seen_fonts: set[str] = set()

            for filename, content in files:
                ext = Path(filename).suffix.lower()
                dest_path = self.assets_dir / f"ast_{uuid.uuid4().hex[:8]}_{Path(filename).name}"
                dest_path.write_bytes(content)

                if ext in {".png", ".svg", ".webp", ".jpg", ".jpeg"}:
                    logos.append(
                        Logo(
                            id=f"ast_logo_{uuid.uuid4().hex[:6]}",
                            filePath=str(dest_path.resolve()),
                            label=Path(filename).stem,
                        )
                    )

                if ext in {".ttf", ".otf", ".woff", ".woff2"}:
                    font_family = Path(filename).stem.replace("-", " ").title()
                    if font_family not in seen_fonts:
                        seen_fonts.add(font_family)
                        extracted_fonts.append(
                            Font(family=font_family, filePath=str(dest_path.resolve()))
                        )

                if ext in {".svg", ".txt", ".json", ".css"}:
                    with contextlib.suppress(Exception):
                        text = content.decode("utf-8", errors="ignore")
                        color_candidates.extend(HEX_FINDER.findall(text))
                        for font_m in FONT_FAMILY_FINDER.findall(text):
                            p = font_m.split(",")[0].strip().strip("'\"")
                            if (
                                p
                                and p.lower() not in {"inherit", "sans-serif", "serif", "monospace"}
                                and p not in seen_fonts
                            ):
                                seen_fonts.add(p)
                                extracted_fonts.append(Font(family=p))

            return logos, _rank_colors(color_candidates), extracted_fonts

        logos, colors, fonts = await asyncio.to_thread(_process_files)
        now = _utc_now_iso()
        return BrandKit(
            id=f"bk_{uuid.uuid4().hex[:8]}",
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
        resp = await _fetch_safe_website(clean_url)
        html = resp.text

        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        desc_m = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I | re.S
        )
        title = title_m.group(1).strip() if title_m else ""
        desc = desc_m.group(1).strip() if desc_m else ""
        overview_text = (
            f"{title} - {desc}"
            if (title and desc)
            else (desc or title or f"Identité visuelle {domain}")
        )

        logos: list[Logo] = []
        fonts: list[Font] = []
        seen_fonts = set()
        for font_m in FONT_FAMILY_FINDER.findall(html):
            clean_font = font_m.split(",")[0].strip().strip("'\"")
            if (
                clean_font
                and clean_font.lower() not in {"inherit", "sans-serif", "serif", "monospace"}
                and clean_font not in seen_fonts
            ):
                seen_fonts.add(clean_font)
                fonts.append(Font(family=clean_font))
                if len(fonts) >= 3:
                    break

        icon_m = re.search(
            r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\'](.*?)["\']', html, re.I
        )
        if icon_m:
            base_url = str(resp.url) if hasattr(resp, "url") else clean_url
            logos.append(
                Logo(
                    id=f"ast_logo_{uuid.uuid4().hex[:6]}",
                    filePath=urljoin(base_url, icon_m.group(1)),
                    label="Favicon",
                )
            )

        now = _utc_now_iso()
        return BrandKit(
            id=f"bk_{uuid.uuid4().hex[:8]}",
            name=name.strip() or domain,
            overview=overview_text,
            logos=logos,
            colors=_rank_colors(HEX_FINDER.findall(html)),
            fonts=fonts,
            createdAt=now,
            updatedAt=now,
        )
