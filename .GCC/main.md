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
- **2026-10-10** : Intégration sous contrôle de version Git des 24 captures et maquettes d'écran dans `ui-specifications/` via exception dans `.gitignore`.
- **2026-10-10** : Sérialisation exclusive des écritures JSON (`data/generations.json`) via `asyncio.Lock` applicatif et renommage atomique POSIX `os.replace`.
- **2026-10-10** : Contrat d'annulation de tâche asynchrone (`POST /api/tasks/{task_id}/cancel`) avec arrêt worker et état terminal `cancelled`.
- **2026-10-10** : Conformité WCAG AA (contraste placeholder `#6B7280`), tokens typographiques Tailwind v3 et gestion du quota utilisateur `userRefs`.
- **2026-10-10** : Spécification de la modularité atomique UI (1 fichier par responsabilité, zéro page en dur), séparation stricte des modes vidéo (Ingrédients Dataset Bible / Video-as-Ingredient vs Frame Chaining First/Last Frame avec règle de subsomption obligatoire pour tout mode complet), et gestion modulaire de la durée (intervalle continu range vs paliers discrets).

## 🌿 Active Branches / Plans
- [`docs/ui-system-specifications`](https://github.com/personnal-agent/colab-ai-studio/pull/4) : Consolidation des spécifications UI/système, design tokens, suivi des maquettes et revue Greptile / CodeRabbit (PR #4 ouverte).

## 📈 Current Status
- ✅ Terminé : Spécifications UI/système/architecture mises à jour avec la modularité atomique des paramètres, les 2 modes vidéo (Ingrédients vs Frame Chaining, subsomption) et la durée configurable (range vs discrete).
- 🔄 En cours : Validation locale de la Quality Gate et vérification du respect du budget strict de PR (<= 1000 lignes).
- ⏳ À venir : Modélisation logicielle (contrats TypeScript, schémas Pydantic, composants React).

## 👉 Next Session Direction
Valider le Quality Gate local, vérifier le budget de gouvernance de la PR, committer conventionnellement les spécifications et engager la modélisation du code.
