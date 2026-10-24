"""Compilateur de contexte de marque (BrandContextCompiler).

Implémente la compilation de Brand Kit selon SPECIFICATION.md §4.4 :
1. Synthèse par LLM externe (Gemini / OpenAI) si une clé API est configurée.
2. Repli déterministe anglais immédiat et transparent sans clé, timeout ou 5xx.
3. Priorité stricte des fentes d'images de référence :
   - Priorité 1 : userRefs (sanctuarisées, tronquées à N si dépassement).
   - Priorité 2 : kitRefs (images du kit dans la limite des slots restants).
   - Priorité 3 : logo (avec consigne explicite en anglais dans le prompt).
4. Repli texte seul si maxImageRefs == 0.
5. Création et intégrité du BrandKitSnapshot.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import httpx

from app.models.domain import BrandKit, BrandKitSnapshot, CompilerLlmConfig

logger = logging.getLogger(__name__)

LOGO_INSTRUCTION = (
    "Here is the brand logo, make sure your generation remains coherent with this brand identity."
)
STATIC_NEGATIVE_TOKENS = "brand inconsistency, distorted logo, unapproved color palette"


@dataclass(frozen=True)
class CompiledBrandContext:
    prompt: str
    negative_prompt: str
    image_refs: list[str]
    snapshot: BrandKitSnapshot | None = None


class BrandContextCompiler:
    """Service interne de compilation et d'arbitrage de contexte de marque."""

    async def compile(
        self,
        prompt: str,
        brand_kit: BrandKit | None = None,
        user_refs: list[str] | None = None,
        max_image_refs: int = 4,
        llm_config: CompilerLlmConfig | None = None,
    ) -> CompiledBrandContext:
        clean_user_prompt = prompt.strip()

        if brand_kit is None:
            allocated_refs = list((user_refs or [])[:max_image_refs]) if max_image_refs > 0 else []
            return CompiledBrandContext(
                prompt=clean_user_prompt,
                negative_prompt="",
                image_refs=allocated_refs,
                snapshot=None,
            )

        # 1. Allocation ordonnée des fentes d'images
        allocated_refs: list[str] = []
        logo_allocated = False
        if max_image_refs > 0:
            u_refs = user_refs or []
            allocated_refs.extend(u_refs[:max_image_refs])
            slots_remaining = max_image_refs - len(allocated_refs)

            if slots_remaining > 0:
                kit_refs = [img.filePath for img in brand_kit.referenceImages]
                for r in kit_refs[:slots_remaining]:
                    allocated_refs.append(r)
                slots_remaining = max_image_refs - len(allocated_refs)

            if slots_remaining > 0 and brand_kit.logos:
                allocated_refs.append(brand_kit.logos[0].filePath)
                logo_allocated = True

        # 2. Synthèse textuelle : LLM ou repli déterministe
        enriched_prompt: str | None = None
        negative_prompt: str | None = None

        if llm_config and llm_config.is_configured():
            try:
                enriched_prompt, negative_prompt = await self._synthesize_with_llm(
                    clean_user_prompt, brand_kit, llm_config
                )
            except Exception as e:
                logger.warning(
                    "Échec de la synthèse LLM du Brand Kit (%s). Bascule sur repli déterministe.", e
                )

        if enriched_prompt is None or negative_prompt is None:
            enriched_prompt, negative_prompt = self._build_deterministic_brief(
                clean_user_prompt, brand_kit
            )

        # 3. Injection de la consigne logo si le logo est retenu dans les fentes
        if logo_allocated:
            enriched_prompt = (
                f"{enriched_prompt} {LOGO_INSTRUCTION}".strip()
                if enriched_prompt
                else LOGO_INSTRUCTION
            )

        # 4. Création du snapshot
        snapshot = brand_kit.create_snapshot()

        return CompiledBrandContext(
            prompt=enriched_prompt,
            negative_prompt=negative_prompt,
            image_refs=allocated_refs,
            snapshot=snapshot,
        )

    def _build_deterministic_brief(self, prompt: str, kit: BrandKit) -> tuple[str, str]:
        dos = [g.text for g in kit.guidelines if g.kind == "do"]
        donts = [g.text for g in kit.guidelines if g.kind == "dont"]
        hex_colors = ", ".join(c.hex for c in kit.colors)
        fonts = ", ".join(f.family for f in kit.fonts)
        dos_str = "; ".join(dos)
        donts_str = ", ".join(donts)

        parts = [f"[Brand Identity: {kit.name}]"]
        if kit.overview:
            parts.append(f"Style: {kit.overview}")
        if hex_colors:
            parts.append(f"Palette: {hex_colors}")
        if fonts:
            parts.append(f"Typography: {fonts}")
        if dos_str:
            parts.append(f"Guidelines: {dos_str}")

        brand_block = ". ".join(parts) + "."
        enriched_prompt = f"{prompt} {brand_block}".strip() if prompt else brand_block

        if donts_str:
            negative_prompt = f"{donts_str}, {STATIC_NEGATIVE_TOKENS}"
        else:
            negative_prompt = STATIC_NEGATIVE_TOKENS

        return enriched_prompt, negative_prompt

    async def _synthesize_with_llm(
        self, prompt: str, kit: BrandKit, config: CompilerLlmConfig
    ) -> tuple[str, str]:
        api_key = config.get_api_key()
        if not api_key:
            raise ValueError("Clé API LLM non disponible")

        system_instruction = (
            "You are an expert AI prompt engineer and brand identity compiler. "
            "Synthesize the given user prompt and brand kit into an enriched cinematic prompt "
            "and a negative prompt strictly in English. "
            "Output JSON with keys 'prompt' and 'negative_prompt'."
        )
        user_content = (
            f"User Prompt: {prompt}\n"
            f"Brand Name: {kit.name}\n"
            f"Brand Overview: {kit.overview}\n"
            f"Colors: {', '.join(f'{c.label} ({c.hex})' for c in kit.colors)}\n"
            f"Typography: {', '.join(f.family for f in kit.fonts)}\n"
            f"Do: {'; '.join(g.text for g in kit.guidelines if g.kind == 'do')}\n"
            f"Don't: {'; '.join(g.text for g in kit.guidelines if g.kind == 'dont')}\n"
        )

        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            if config.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_instruction}\n\n{user_content}"}]}],
                    "generationConfig": {
                        "temperature": 0.4,
                        "responseMimeType": "application/json",
                    },
                }
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                url = "https://api.openai.com/v1/chat/completions"
                headers["Authorization"] = f"Bearer {api_key}"
                payload = {
                    "model": config.model,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"},
                }
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        parsed = json.loads(cleaned)
        enriched = str(parsed.get("prompt", "")).strip()
        negative = str(parsed.get("negative_prompt", "")).strip()

        if not enriched:
            raise ValueError("Prompt généré par le LLM vide")

        return enriched, negative
