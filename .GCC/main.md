# Current Project Context — Colab AI Studio

## 🏆 Major Milestones (Archived Epics)
- **2026-10-09** : Déploiement complet du socle de gouvernance et qualité des 6 piliers (`coding-stuff` v3.0).

## 🎯 Objective
Mise en place de l'environnement de gouvernance, des règles d'agents (`AGENTS.md`), de la persistance de session (`.GCC/`), des garde-fous Git locaux (`.githooks/`), des workflows GitHub Actions (`.github/`) et de l'architecture blueprint (`ARCHITECTURE.md`) pour Colab AI Studio.

## 🧠 Decisions Made
- **2026-10-09** : Adoption du socle de gouvernance à 6 piliers avec agent cible Antigravity 2.0 / IDE.
- **2026-10-09** : Suivi de `.GCC/` sous contrôle de version Git pour synchroniser la mémoire des décisions d'architecture entre les sessions.
- **2026-10-09** : Conception de hooks Git hybrides scope-aware (`pre-commit`, `commit-msg`, `pre-push`) prenant en charge Python (FastAPI/Colab) et TypeScript/JavaScript (React/Vite).
- **2026-10-09** : Application du principe de moindre privilège avec interdiction stricte de modification sur `.githooks/**`, `.gouvernance/**`, `.GCC/PROTOCOL.md`, `.env*`.
- **2026-10-10** : Architecture bi-modale (Colab vs Local) fixée à l'installation dans `data/config.json`. Avatar interactif en Colab (crédits, VRAM/RAM, serveur) et grisé inactif en local (bascule dynamique différée à une issue ultérieure).
- **2026-10-10** : Isolation physique de stockage pour les projets (`projects.json` via `storagePath`) : si un chemin sur mesure est renseigné, les médias générés y sont stockés exclusivement sans duplication dans `outputs/`.

## 🌿 Active Branches / Plans
- `chore/governance-coding-stuff-baseline` : Initialisation du socle de gouvernance et des garde-fous de qualité.

## 📈 Current Status
- ✅ Terminé : Socle des 6 piliers installé (AGENTS.md, ARCHITECTURE.md, .GCC/, .gouvernance/, .githooks/, .github/, permissions).
- 🔄 En cours : Création de la Pull Request isolant uniquement les ajouts de gouvernance.
- ⏳ À venir : Phase 2 du projet (initialisation du backend FastAPI et du frontend React SPA).

## 👉 Next Session Direction
Initier le développement du backend local FastAPI (`app/`) et de l'application frontend React SPA (`frontend/`) selon les spécifications de `SPECIFICATION.md` et `UI_SPECIFICATION.md`.
