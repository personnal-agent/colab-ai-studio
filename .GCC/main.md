# Current Project Context — Colab AI Studio

## 🏆 Major Milestones (Archived Epics)
- **2026-10-09** : Déploiement complet du socle de gouvernance et qualité des 6 piliers (`coding-stuff` v3.0).
- **2026-10-11** : Consolidation et validation formelle du corpus de modélisation logicielle sous `.modelisation/logiciel/` (11 diagrammes UML SVG + PNG, README d'architecture système et matrice de traçabilité des exigences).
- **2026-10-11** : Harmonisation technique des 11 diagrammes SVG, régénération et validation des 11 rendus PNG, README d'architecture et matrice de traçabilité synchronisés à 100%.
- **2026-10-15** : Purge intégrale de toutes les citations et justifications théoriques externes dans les diagrammes UML et la documentation d'architecture, recentrage 100% sur le domaine métier et l'ingénierie concrète de Colab AI Studio, formalisation du 5ᵉ mode LLM sur le dock dans les spécifications.

## 🎯 Objective
Livraison par Pull Request des 11 diagrammes UML finalisés, de la documentation d'architecture synchronisée et des spécifications enrichies du mode LLM.

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
- **2026-10-10** : Sélection du corpus UML cible en 7 types et 11 diagrammes : cas d’utilisation; composants; déploiement; classes; activité; séquences génération/compilation de marque/proxy LLM; états-transitions dock/tâche/Model Swapper.
- **2026-10-11** : Validation de l'architecture logicielle : délimitation de la boîte système sur l'Application Studio Locale (UI React + Orchestrateur FastAPI) avec `«system» Google Colab (Worker GPU distant)` en acteur secondaire externe à droite (le code local de pilotage Colab restant à l'intérieur du système). Rejet formel des anti-patrons (clics d'IHM en messages, états finaux sur tâches persistées, types primitifs pour cycles de vie finis).
- **2026-10-15** : Purge intégrale de toutes les citations, mentions académiques et justifications théoriques externes dans les diagrammes UML et la documentation d'architecture.
  - **Context** : L'utilisateur exige formellement qu'aucun document de cours, norme ou méthodologie d'audit ne soit cité ou nommé dans les livrables finaux, qui doivent contenir exclusivement le domaine métier de Colab AI Studio.
  - **Discarded Options** : Suppression totale des encadrés de notes (écartée pour préserver les explications techniques utiles sur l'asynchronisme, la VRAM et le streaming).
  - **Rationale** : Reformulation systématique des cartouches, sous-titres et encadrés en principes d'ingénierie logicielle concrets et opérationnels sans référence théorique ni académique.
- **2026-10-15** : Formalisation du 5ᵉ mode `LLM` sur la barre d'onglets du dock flottant dans `SPECIFICATION.md` et `UI_SPECIFICATION.md` avec masquage dynamique des contrôles multimédia et activation de la vue textuelle conversationnelle.

## 🌿 Active Branches / Plans
- [`docs/ui-system-specifications`](https://github.com/personnal-agent/colab-ai-studio/pull/4) : Consolidation des spécifications UI/système, design tokens, suivi des maquettes et revue Greptile / CodeRabbit (PR #4 ouverte).
- `docs/software-modeling` : Modélisation UML sous `.modelisation/logiciel/` ; livraison PR en cours.

## 📈 Current Status
- ✅ Terminé : Purge intégrale des citations externes sur les 11 diagrammes SVG et PNG ainsi que dans le README. Reformulation 100% orientée métier et système. Spécification du mode LLM sur le dock flottant (`SPECIFICATION.md`, `UI_SPECIFICATION.md`). Validation XML (11/11 OK), conversion PNG haute fidélité (11/11 OK), validation statique Python (exit code 0).
- 🔄 En cours : Création de la Pull Request de livraison sur la branche `docs/software-modeling`.
- ⏳ À venir : Lecture 100% des retours de revue des bots en ligne et signature par le mainteneur.

## 👉 Next Session Direction
Suivre la revue de la Pull Request par les bots et le mainteneur.
