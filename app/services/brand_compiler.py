"""Compilateur de contexte de marque (app/services/brand_compiler.py).

Transposition déterministe et par LLM des Brand Kits selon SPECIFICATION.md §4.4 :
1. Repli déterministe anglais immédiat en cas d'absence de clé ou d'erreur réseau/API.
2. Priorité stricte des slots : 1) userRefs, 2) kitRefs, 3) logo.
3. Injection de consigne logo en anglais si le logo a été alloué à un slot.
4. Repli texte seul si le modèle récepteur impose maxImageRefs == 0.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

import httpx

from app.models.domain import BrandKit, BrandKitSnapshot


@dataclass
class CompiledBrandResult:
    compiled_prompt: str
    negative_prompt: str
    assigned_image_refs: list[str]
    snapshot: BrandKitSnapshot


class BrandContextCompiler:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        client: httpx.AsyncClient | None = None,
        timeout: float = 8.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._client = client
        self.timeout = timeout

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=self.timeout)

    async def compile(
        self,
        prompt: str,
        kit: BrandKit,
        user_refs: list[str] | None = None,
        max_image_refs: int = 4,
    ) -> CompiledBrandResult:
        refs_input = list(user_refs or [])

        # 1. Attribution des slots d'images selon la priorité stricte
        assigned_refs: list[str] = []
        logo_injected = False

        if max_image_refs > 0:
            # Priorité 1 : Références manuelles de l'utilisateur (sanctuarisées)
            for r in refs_input:
                if len(assigned_refs) < max_image_refs:
                    assigned_refs.append(r)

            # Priorité 2 : Images de référence du kit
            for asset in kit.referenceImages:
                if len(assigned_refs) < max_image_refs:
                    assigned_refs.append(asset.filePath)

            # Priorité 3 : Logo de la marque
            if kit.logos and len(assigned_refs) < max_image_refs:
                assigned_refs.append(kit.logos[0].filePath)
                logo_injected = True

        # 2. Composition du Brief textuel (LLM ou Gabarit Déterministe Anglais)
        hex_colors = [c.hex for c in kit.colors]
        fonts = [f.family for f in kit.fonts]
        dos = [g.text for g in kit.guidelines if g.kind == "do"]
        donts = [g.text for g in kit.guidelines if g.kind == "dont"]

        fallback_brief = (
            f"[Brand Identity: {kit.name}] Style: {kit.overview}. "
            f"Palette: {', '.join(hex_colors) if hex_colors else 'Neutral'}. "
            f"Typography: {', '.join(fonts) if fonts else 'Modern'}. "
            f"Guidelines: {'; '.join(dos) if dos else 'Consistent aesthetics'}."
        )

        brief_text = fallback_brief
        if self.api_key:
            client = self._get_client()
            prompt_system = (
                "You are an expert film director and brand designer. Enhance the user prompt "
                f"incorporating the brand brief '{kit.name}': {kit.overview}. "
                "Keep it cinematic, evocative, and strictly in English."
            )
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": prompt},
                ],
            }
            try:
                with contextlib.suppress(Exception):
                    res = await client.post(
                        "https://api.openai.com/v1/chat/completions", json=payload
                    )
                    if res.status_code == 200:
                        data = res.json()
                        content = (
                            data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                            .strip()
                        )
                        if content:
                            brief_text = content
            finally:
                if self._client is None:
                    with contextlib.suppress(Exception):
                        await client.aclose()

        compiled_prompt = f"{prompt.strip()}. {brief_text}".strip()
        if logo_injected:
            compiled_prompt += (
                " Here is the brand logo, make sure your generation remains coherent "
                "with this brand identity."
            )

        # 3. Construction du Negative Prompt avec les interdictions ("Don't")
        dont_elements: list[str] = list(donts)
        dont_elements.extend(
            [
                "brand inconsistency",
                "distorted logo",
                "unapproved color palette",
            ]
        )
        negative_prompt = ", ".join(dont_elements)

        snapshot = kit.create_snapshot()
        return CompiledBrandResult(
            compiled_prompt=compiled_prompt,
            negative_prompt=negative_prompt,
            assigned_image_refs=assigned_refs,
            snapshot=snapshot,
        )
