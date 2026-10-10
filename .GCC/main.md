# Current Project Context — Colab AI Studio

## 🏆 Major Milestones (Archived Epics)
- **2026-10-09** : Déploiement complet du socle de gouvernance et qualité des 6 piliers (`coding-stuff` v3.0).

## 🎯 Objective
Modéliser le code et l'architecture logicielle de Colab AI Studio (contrats d'interfaces TypeScript, schémas Pydantic, machine à états du dock flottant adaptatif, pipeline BrandContextCompiler, orchestrateur asynchrone FastAPI et gestionnaire dynamique VRAM Colab ModelSwapper) et consolider les spécifications complètes avant la phase de codage.

## 🧠 Decisions Made
- **2026-10-09** : Adoption du socle de gouvernance à 6 piliers avec agent cible Antigravity 2.0 / IDE.
- **2026-10-09** : Suivi de `.GCC/` sous contrôle de version Git pour synchroniser la mémoire des décisions d'architecture entre les sessions.
- **2026-10-09** : Conception de hooks Git hybrides scope-aware (`pre-commit`, `commit-msg`, `pre-push`) prenant en charge Python (FastAPI/Colab) et TypeScript/JavaScript (React/Vite).
- **2026-10-09** : Application du principe de moindre privilège avec interdiction stricte de modification sur `.githooks/**`, `.gouvernance/**`, `.GCC/PROTOCOL.md`, `.env*`.
- **2026-10-10** : Architecture bi-modale (Colab vs Local) fixée à l'installation dans `data/config.json`. Avatar interactif en Colab (crédits, VRAM/RAM, serveur) et grisé inactif en local (bascule dynamique différée à une issue ultérieure).
- **2026-10-10** : Isolation physique de stockage pour les projets (`projects.json` via `storagePath`) : si un chemin sur mesure est renseigné, les médias générés y sont stockés exclusivement sans duplication dans `outputs/`.
- **2026-10-10** : Création de l'issue GitHub [#2](https://github.com/personnal-agent/colab-ai-studio/issues/2) cadrant la bascule dynamique à chaud entre le mode Local et le mode Google Colab.

## 🌿 Active Branches / Plans
- [`docs/ui-system-specifications`](https://github.com/personnal-agent/colab-ai-studio/pull/4) : Consolidation des spécifications UI/système, design tokens et modélisation logicielle (Pull Request #4 ouverte).

## 📈 Current Status
- ✅ Terminé : PR #1 fusionnée dans `main`. Spécifications UI/UX exhaustives (`UI_SPECIFICATION.md`, 24 captures analysées), Design tokens (`DESIGN_SPECIFICATION.md`), architecture système et stockage JSON (`SPECIFICATION.md`), Issue #2 créée, et Pull Request [#4](https://github.com/personnal-agent/colab-ai-studio/pull/4) ouverte et poussée sur GitHub.
- 🔄 En cours : Modélisation du code (contrats d'API, schémas de données, hiérarchie de composants).
- ⏳ À venir : Implémentation du backend FastAPI (`app/`) et du frontend React SPA (`frontend/`).

## 👉 Next Session Direction
Finaliser la modélisation logicielle (architecture des composants React et services FastAPI) puis amorcer l'implémentation modulaire guidée par tests.
