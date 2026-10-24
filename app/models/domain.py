"""Modèles de domaine Pydantic v2 pour Colab AI Studio (app/models/domain.py).

Conformes au diagramme de classes UML et à SPECIFICATION.md §4.2.1-§4.2.4.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


HEX_COLOR_REGEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    COLAB = "colab"
    LOCAL = "local"


class DomainBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class GenerationParameters(DomainBase):
    seed: int
    aspectRatio: str = "16:9"
    resolution: str = "720p"
    duration: str = "5s"
    frameRate: str | None = None
    audio: bool | None = None
    enhance: bool | None = None

    @field_validator("aspectRatio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d+:\d+$", clean):
            raise ValueError(f"Format de ratio non supporté : '{v}' (attendu 'W:H')")
        w, h = map(int, clean.split(":"))
        if w <= 0 or h <= 0:
            raise ValueError(f"Dimensions du ratio strictement positives requises : '{v}'")
        return clean

    def validate(self) -> bool:
        return True

    def to_payload_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class GenerationReferences(DomainBase):
    startFrame: str | None = None
    endFrame: str | None = None
    imageRefs: list[str] = Field(default_factory=list)
    videoRefs: list[str] = Field(default_factory=list)
    audioRefs: list[str] = Field(default_factory=list)
    upscaleSource: str | None = None
    brandKitId: str | None = None

    def has_visual_references(self) -> bool:
        return bool(self.startFrame or self.endFrame or self.imageRefs or self.videoRefs)

    def clear_references(self) -> None:
        self.startFrame = self.endFrame = self.upscaleSource = self.brandKitId = None
        self.imageRefs.clear()
        self.videoRefs.clear()
        self.audioRefs.clear()


class BrandKitSnapshot(DomainBase):
    id: str
    name: str
    overview: str
    colors: list[str] = Field(default_factory=list)
    logos: list[str] = Field(default_factory=list)
    fonts: list[str] = Field(default_factory=list)
    guidelines: list[str] = Field(default_factory=list)

    def get_primary_color(self) -> str | None:
        return self.colors[0] if self.colors else None

    def format_prompt_tokens(self) -> str:
        parts = [f"[Brand: {self.name}]", f"Style: {self.overview}"]
        if self.colors:
            parts.append(f"Palette: {', '.join(self.colors)}")
        if self.fonts:
            parts.append(f"Typography: {', '.join(self.fonts)}")
        if self.guidelines:
            parts.append(f"Guidelines: {'; '.join(self.guidelines)}")
        return " ".join(parts)


class Logo(BaseModel):
    id: str
    filePath: str
    label: str = "Logo Principal"


class Color(BaseModel):
    hex: str
    label: str
    isDominant: bool = False

    @field_validator("hex")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        if not HEX_COLOR_REGEX.match(v):
            raise ValueError(f"Format couleur hexadécimal invalide : '{v}'")
        return v.upper()


class Font(BaseModel):
    family: str
    weight: str = "400"
    filePath: str | None = None


class Asset(BaseModel):
    id: str
    filePath: str


class Guideline(BaseModel):
    kind: Literal["do", "dont"] = "do"
    text: str


class BrandKit(DomainBase):
    id: str
    name: str
    overview: str
    logos: list[Logo] = Field(default_factory=list)
    colors: list[Color] = Field(default_factory=list)
    fonts: list[Font] = Field(default_factory=list)
    referenceImages: list[Asset] = Field(default_factory=list)
    voices: list[dict[str, Any]] = Field(default_factory=list)
    captions: list[dict[str, Any]] = Field(default_factory=list)
    guidelines: list[Guideline] = Field(default_factory=list)
    createdAt: str = Field(default_factory=_utc_now_iso)
    updatedAt: str = Field(default_factory=_utc_now_iso)
    lastUsedAt: str | None = None

    def compile_context(self) -> str:
        return self.create_snapshot().format_prompt_tokens()

    def create_snapshot(self) -> BrandKitSnapshot:
        return BrandKitSnapshot(
            id=self.id,
            name=self.name,
            overview=self.overview,
            colors=[c.hex for c in self.colors],
            logos=[logo.filePath for logo in self.logos],
            fonts=[f.family for f in self.fonts],
            guidelines=[g.text for g in self.guidelines],
        )


class Project(DomainBase):
    id: str
    name: str
    description: str | None = None
    colorTag: str | None = None
    storagePath: str | None = None
    createdAt: str = Field(default_factory=_utc_now_iso)

    @field_validator("colorTag")
    @classmethod
    def validate_color_tag(cls, v: str | None) -> str | None:
        if v is not None and not HEX_COLOR_REGEX.match(v):
            raise ValueError(f"Format colorTag invalide : '{v}'")
        return v.upper() if v else None


class Generation(DomainBase):
    id: str
    status: TaskStatus = TaskStatus.PENDING
    mediaType: str = "video"
    prompt: str
    negativePrompt: str | None = None
    compiledPrompt: str | None = None
    filePath: str | None = None
    thumbnailPath: str | None = None
    progress: int | None = 0
    errorMessage: str | None = None
    modelId: str
    modelName: str
    parameters: GenerationParameters
    references: GenerationReferences = Field(default_factory=GenerationReferences)
    brandKitSnapshot: BrandKitSnapshot | None = None
    isFavorite: bool = False
    projectId: str | None = None
    createdAt: str = Field(default_factory=_utc_now_iso)
    workerUrl: str | None = None

    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def mark_failed(self, reason: str) -> None:
        self.status, self.errorMessage = TaskStatus.FAILED, reason

    def get_output_path(self) -> str | None:
        return self.filePath

    def toggle_favorite(self) -> bool:
        self.isFavorite = not self.isFavorite
        return self.isFavorite


class ColabConfig(BaseModel):
    tunnelUrl: str = "https://xxxx-xx-xx.ngrok-free.app"
    accountEmail: str | None = None
    lastPing: str | None = None

    def is_connected(self) -> bool:
        return bool(self.tunnelUrl and not self.tunnelUrl.startswith("https://xxxx"))

    def touch_ping(self) -> None:
        self.lastPing = _utc_now_iso()


class LocalConfig(BaseModel):
    device: str = "cpu"
    threads: int = 4
    workerUrl: str = "http://127.0.0.1:8190"

    def is_cpu_fallback(self) -> bool:
        return self.device.lower() == "cpu"

    def get_device_name(self) -> str:
        return self.device


class CompilerLlmConfig(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-1.5-flash"
    apiKeyEnv: str = "COMPILER_LLM_API_KEY"
    apiKey: str | None = None

    def is_configured(self) -> bool:
        return bool(self.get_api_key())

    def get_api_key(self) -> str | None:
        return self.apiKey or os.environ.get(self.apiKeyEnv)


class LlmProxyConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    timeout: int = 120

    def is_running(self) -> bool:
        return self.enabled

    def get_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class StudioConfig(DomainBase):
    executionMode: ExecutionMode = ExecutionMode.COLAB
    colab: ColabConfig = Field(default_factory=ColabConfig)
    local: LocalConfig = Field(default_factory=LocalConfig)
    compilerLlm: CompilerLlmConfig = Field(default_factory=CompilerLlmConfig)
    defaultStoragePath: str = "outputs/"
    llmProxy: LlmProxyConfig = Field(default_factory=LlmProxyConfig)

    def is_colab_active(self) -> bool:
        return self.executionMode == ExecutionMode.COLAB

    def get_active_endpoint(self) -> str:
        return (
            self.colab.tunnelUrl
            if self.executionMode == ExecutionMode.COLAB
            else self.local.workerUrl
        )

    def set_execution_mode(self, mode: ExecutionMode) -> None:
        self.executionMode = mode
