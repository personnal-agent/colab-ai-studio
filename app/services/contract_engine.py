"""Moteur de validation de contrats (ContractEngine) pour Omniforge v3.

Assure la conformité architecturale selon INTEGRATION_PLAN_V3.md & SPECIFICATION01.md :
1. canvas-discipline : validation stricte des calques (dimensions > 0, intégrité hiérarchique).
2. anti-loop guard : prévention des boucles infinies de re-soumission sans mutation.
3. acceptedInputTypes : blocage immédiat des références incompatibles (HTTP 422).
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict, deque
from typing import Any

from app.models.domain import GenerationReferences

logger = logging.getLogger(__name__)


class ContractValidationError(Exception):
    """Exception de base pour les violations de contrats."""


class CanvasDisciplineError(ContractValidationError):
    """Violation de la discipline de calques sur le canevas."""


class AntiLoopError(ContractValidationError):
    """Détection d'une boucle infinie d'exécution agentique sans mutation."""


class IncompatibleInputTypeError(ContractValidationError):
    """Soumission d'ingrédients ou références incompatibles avec le modèle."""


class ContractEngine:
    """Moteur central de vérification des contrats de conception et d'inférence."""

    def __init__(self, max_loop_iterations: int = 3, loop_window_size: int = 10) -> None:
        self.max_loop_iterations = max_loop_iterations
        self.loop_window_size = loop_window_size
        # Historique glissant des requêtes par session : session_id -> deque([hash, ...])
        self._session_history: dict[str, deque[str]] = defaultdict(
            lambda: deque(maxlen=self.loop_window_size)
        )

    def validate_canvas_discipline(self, canvas_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Vérifie la cohérence géométrique et hiérarchique des calques du canevas.

        Règles :
        - Dimensions strictement positives (width > 0, height > 0).
        - Coordonnées finies (pas de NaN ou infini).
        - Pas de cycle parent-enfant dans la hiérarchie.
        """
        if not isinstance(canvas_data, dict):
            return False, "Le payload canevas doit être un dictionnaire valide"

        layers = canvas_data.get("layers", [])
        if not isinstance(layers, list):
            return False, "Le champ 'layers' du canevas doit être une liste"

        seen_layer_ids = set()
        parent_map: dict[str, str] = {}

        for layer in layers:
            if not isinstance(layer, dict):
                return False, "Chaque calque du canevas doit être un objet"

            layer_id = layer.get("id")
            if not layer_id or not isinstance(layer_id, str):
                return False, "Chaque calque doit posséder un 'id' sous forme de chaîne"

            if layer_id in seen_layer_ids:
                return False, f"Identifiant de calque dupliqué : '{layer_id}'"
            seen_layer_ids.add(layer_id)

            # Vérification des dimensions
            width = layer.get("width")
            height = layer.get("height")
            if width is not None and (not isinstance(width, (int, float)) or width <= 0):
                return False, f"Calque '{layer_id}' : largeur invalide ({width}), doit être > 0"
            if height is not None and (not isinstance(height, (int, float)) or height <= 0):
                return False, f"Calque '{layer_id}' : hauteur invalide ({height}), doit être > 0"

            # Vérification des coordonnées
            x = layer.get("x", 0)
            y = layer.get("y", 0)
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                return False, f"Calque '{layer_id}' : coordonnées x/y doivent être numériques"

            parent_id = layer.get("parentId")
            if parent_id:
                if parent_id == layer_id:
                    return False, f"Calque '{layer_id}' : auto-référence parentale interdite"
                parent_map[layer_id] = parent_id

        # Détection de cycles hiérarchiques
        for start_id in parent_map:
            visited = set()
            curr = start_id
            while curr in parent_map:
                if curr in visited:
                    return False, f"Cycle hiérarchique détecté à partir de '{start_id}'"
                visited.add(curr)
                curr = parent_map[curr]

        return True, None

    def check_anti_loop(
        self, session_id: str, prompt: str, state_hash: str | None = None
    ) -> tuple[bool, str | None]:
        """Détecte les boucles infinies de dialogue ou d'inférence sans progression d'état.

        Si un agent re-soumet la même instruction textuelle et le même état plus de
        `max_loop_iterations` fois consécutives, l'exécution est bloquée.
        """
        if not session_id:
            return True, None

        raw_key = f"{prompt.strip()}::{state_hash or 'no_state'}"
        item_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        history = self._session_history[session_id]

        # Comptage des occurrences consécutives à la fin de l'historique
        consecutive_matches = 0
        for h in reversed(history):
            if h == item_hash:
                consecutive_matches += 1
            else:
                break

        if consecutive_matches >= self.max_loop_iterations:
            total_occurrences = consecutive_matches + 1
            return (
                False,
                f"Garde anti-loop déclenchée pour la session '{session_id}' : "
                f"l'instruction se répète sans mutation d'état ({total_occurrences} occurrences)",
            )

        history.append(item_hash)
        return True, None

    def reset_session_loop(self, session_id: str) -> None:
        """Réinitialise l'historique anti-loop pour une session donnée."""
        if session_id in self._session_history:
            self._session_history[session_id].clear()

    def validate_accepted_input_types(
        self,
        model_capabilities: dict[str, Any] | None,
        references: GenerationReferences,
    ) -> tuple[bool, str | None]:
        """Valide la compatibilité stricte des ingrédients soumis avec le modèle actif.

        Conforme à SPECIFICATION01.md §3.2.1 :
        Si le modèle déclare `acceptedInputTypes` dans ses capacités :
        - Les références image (startFrame, endFrame, imageRefs) exigent 'image'.
        - Les références vidéo (videoRefs) exigent 'video'.
        - Les références audio (audioRefs) exigent 'audio'.
        - Les références 3D (meshRef) exigent '3d' ou 'mesh'.
        """
        if not model_capabilities:
            return True, None

        accepted = model_capabilities.get("acceptedInputTypes")
        if not accepted or not isinstance(accepted, list):
            # Pas de restriction déclarée : tout type est accepté par défaut
            return True, None

        accepted_set = {str(t).lower() for t in accepted}

        # 1. Références images
        has_images = bool(references.startFrame or references.endFrame or references.imageRefs)
        if has_images and "image" not in accepted_set:
            return (
                False,
                f"Incompatibilité média : le modèle n'accepte pas les références de type 'image' "
                f"(types acceptés : {sorted(accepted_set)})",
            )

        # 2. Références vidéos
        has_videos = bool(references.videoRefs)
        if has_videos and "video" not in accepted_set:
            return (
                False,
                f"Incompatibilité média : le modèle n'accepte pas les références de type 'video' "
                f"(types acceptés : {sorted(accepted_set)})",
            )

        # 3. Références audios
        has_audios = bool(references.audioRefs)
        if has_audios and "audio" not in accepted_set:
            return (
                False,
                f"Incompatibilité média : le modèle n'accepte pas les références de type 'audio' "
                f"(types acceptés : {sorted(accepted_set)})",
            )

        # 4. Références 3D (meshRef si déclaré)
        mesh_ref = getattr(references, "meshRef", None)
        if mesh_ref and not ({"3d", "mesh"} & accepted_set):
            return (
                False,
                f"Incompatibilité média : le modèle n'accepte pas les références 3D "
                f"(types acceptés : {sorted(accepted_set)})",
            )

        return True, None


_default_contract_engine = ContractEngine()


def get_contract_engine() -> ContractEngine:
    """Fournisseur de dépendance pour le moteur de contrats."""
    return _default_contract_engine
