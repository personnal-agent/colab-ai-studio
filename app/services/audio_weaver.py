"""Module D : Audio Weaver & Synthèse Vocale / Ambiance Sonore par Plan.

Extrait automatiquement les dialogues entre guillemets ("...") et les descripteurs
d'ambiance sonore dans un prompt de plan, génère une piste audio WAV (voix + ambiance)
et la mixe sans perte dans le conteneur MP4 du plan via FFmpeg.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import math
import re
import shutil
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any

logger = logging.getLogger("audio_weaver")

DIALOGUE_RE = re.compile(
    r"(?:(?P<context>[a-zA-ZÀ-ÿ\s,\-]{0,45}?)\s*)?"
    r'(?:"(?P<quote_en>[^"\n]{1,240})"|«\s*(?P<quote_fr>[^»\n]{1,240})\s*»)',
    re.IGNORECASE,
)


def extract_dialogues(prompt_text: str) -> list[dict[str, str]]:
    """Extrait toutes les répliques entre guillemets et leur intention vocale."""
    if not prompt_text:
        return []

    results: list[dict[str, str]] = []
    for match in DIALOGUE_RE.finditer(prompt_text):
        text = (match.group("quote_en") or match.group("quote_fr") or "").strip()
        if not text or len(text) < 2:
            continue
        ctx = (match.group("context") or "").strip().lower()
        voice_style = "feminine_soft"
        if any(w in ctx for w in ("whisper", "murmur", "chuchot", "breath", "soupir")):
            voice_style = "whisper_intimate"
        elif any(w in ctx for w in ("male", "deep", "man", "cucumber", "homme", "grave")):
            voice_style = "masculine_deep"
        elif any(w in ctx for w in ("excited", "tiktok", "laugh", "energy")):
            voice_style = "energetic"

        results.append(
            {
                "text": text,
                "voiceStyle": voice_style,
                "context": ctx,
            }
        )
    return results


def synthesize_ambient_and_voice_wav(
    output_wav: Path,
    duration_sec: float = 10.0,
    dialogues: list[dict[str, str]] | None = None,
    sample_rate: int = 24000,
) -> Path:
    """Génère un fichier WAV stéréo/mono contenant une ambiance cinématographique douce
    et une enveloppe vocale synthétique si aucun binaire TTS externe n'est requis.
    """
    dur = max(1.0, min(float(duration_sec), 60.0))
    total_samples = int(dur * sample_rate)
    dialogues = dialogues or []

    # Fréquence fondamentale selon le style vocal détecté
    base_freq = 215.0  # Féminin doux par défaut
    is_whisper = False
    if dialogues:
        style = dialogues[0].get("voiceStyle", "feminine_soft")
        if style == "masculine_deep":
            base_freq = 115.0
        elif style == "whisper_intimate":
            base_freq = 230.0
            is_whisper = True
        elif style == "energetic":
            base_freq = 245.0

    # Fenêtre temporelle de parole (ex: de 1.2s à min(dur-0.8, 1.2 + nb_mots*0.35))
    total_words = sum(len(d.get("text", "").split()) for d in dialogues)
    speech_start = 1.0 if total_words > 0 else -1.0
    speech_end = (
        min(dur - 0.5, speech_start + max(1.2, total_words * 0.42)) if total_words > 0 else -1.0
    )

    frames = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        # 1. Ambiance organique très feutrée (accord chaud + léger souffle naturel)
        env_amb = min(1.0, t / 0.5) * min(1.0, (dur - t) / 0.5)
        warm_pad = (
            0.015 * math.sin(2.0 * math.pi * 110.0 * t)
            + 0.010 * math.sin(2.0 * math.pi * 164.81 * t)
            + 0.008 * math.sin(2.0 * math.pi * 220.0 * t)
        ) * env_amb

        # 2. Formants vocaux doux pendant la fenêtre de dialogue
        voice_sig = 0.0
        if speech_start <= t <= speech_end:
            rel_t = t - speech_start
            # Modulation syllabique naturelle (~4 Hz)
            syllable_env = 0.55 + 0.45 * math.sin(2.0 * math.pi * 3.8 * rel_t)
            fade = min(1.0, rel_t / 0.15) * min(1.0, (speech_end - t) / 0.2)
            pitch_mod = base_freq * (1.0 + 0.03 * math.sin(2.0 * math.pi * 1.7 * rel_t))
            formant1 = math.sin(2.0 * math.pi * pitch_mod * t)
            formant2 = 0.45 * math.sin(2.0 * math.pi * (pitch_mod * 2.0) * t)
            formant3 = 0.20 * math.sin(2.0 * math.pi * (pitch_mod * 3.0) * t)
            breath = 0.04 * math.sin(2.0 * math.pi * 1350.0 * t * math.cos(t * 17.0))
            gain = 0.05 if is_whisper else 0.09
            voice_sig = gain * syllable_env * fade * (formant1 + formant2 + formant3) + (
                breath * fade if is_whisper else 0.0
            )

        sample_val = max(-0.95, min(0.95, warm_pad + voice_sig))
        pcm_int16 = int(sample_val * 32767.0)
        frames.extend(struct.pack("<h", pcm_int16))

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))

    return output_wav


async def _try_external_tts(text: str, voice_style: str, out_wav: Path) -> bool:
    """Tente d'utiliser espeak-ng si installé sur le système Linux pour articuler le texte."""
    espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak_bin or not text.strip():
        return False

    pitch = "65" if "feminine" in voice_style or "whisper" in voice_style else "35"
    speed = "135" if "whisper" in voice_style else "155"
    cmd = [espeak_bin, "-p", pitch, "-s", speed, "-w", str(out_wav), text.strip()]
    with contextlib.suppress(Exception):
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=8.0)
        out_wav_ok = await asyncio.to_thread(
            lambda: out_wav.is_file() and out_wav.stat().st_size > 200
        )
        if proc.returncode == 0 and out_wav_ok:
            return True
    return False


async def weave_audio_into_video_segment(
    video_path: Path,
    prompt_text: str,
    duration_sec: float = 10.0,
) -> dict[str, Any]:
    """Génère la bande sonore du plan (dialogues + ambiance) et l'incorpore dans le MP4."""
    dialogues = extract_dialogues(prompt_text)
    ffmpeg_path = Path("/home/instructeur/.local/bin/ffmpeg")
    has_ffmpeg = await asyncio.to_thread(ffmpeg_path.exists)
    ffmpeg_bin = str(ffmpeg_path) if has_ffmpeg else (shutil.which("ffmpeg") or "ffmpeg")

    with tempfile.TemporaryDirectory(prefix="audio_weaver_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        wav_path = tmp_path / "segment_audio.wav"

        tts_ok = False
        if dialogues:
            full_line = " ... ".join(d["text"] for d in dialogues)
            style = dialogues[0].get("voiceStyle", "feminine_soft")
            tts_ok = await _try_external_tts(full_line, style, wav_path)

        if not tts_ok:
            await asyncio.to_thread(
                synthesize_ambient_and_voice_wav,
                wav_path,
                duration_sec,
                dialogues,
            )

        muxed_mp4 = tmp_path / "muxed_output.mp4"
        cmd = [
            str(ffmpeg_bin),
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(wav_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(muxed_mp4),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode == 0 and muxed_mp4.is_file() and muxed_mp4.stat().st_size > 500:
            await asyncio.to_thread(shutil.copy2, muxed_mp4, video_path)
            return {
                "muxed": True,
                "dialoguesCount": len(dialogues),
                "dialogues": dialogues,
            }
        else:
            logger.debug(
                "Muxing FFmpeg ignoré sur %s: %s",
                video_path,
                stderr.decode("utf-8", errors="ignore")[:200],
            )
            return {
                "muxed": False,
                "dialoguesCount": len(dialogues),
                "dialogues": dialogues,
            }
