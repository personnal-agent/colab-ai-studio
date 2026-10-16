# Current Project Context — Colab AI Studio

## 🏆 Major Milestones (Archived Epics)

- **2026-10-09** : Déploiement complet du socle de gouvernance et qualité des 6 piliers (`coding-stuff` v3.0).
- **2026-10-11** : Consolidation et validation formelle du corpus de modélisation logicielle sous `.modelisation/logiciel/` (11 diagrammes UML SVG + PNG, README d'architecture système et matrice de traçabilité des exigences).
- **2026-10-11** : Harmonisation technique des 11 diagrammes SVG, régénération et validation des 11 rendus PNG, README d'architecture et matrice de traçabilité synchronisés à 100%.
- **2026-10-15** : Purge intégrale de toutes les citations et justifications théoriques externes dans les diagrammes UML et la documentation d'architecture, recentrage 100% sur le domaine métier et l'ingénierie concrète de Colab AI Studio, formalisation du 5ᵉ mode LLM sur le dock dans les spécifications.
- **2026-10-15** : Approbation formelle à 100% de la Pull Request #6 par Greptile (score 5/5, 0 issue bloquante) et CodeRabbit (statut `APPROVED`, 0 finding résiduel, 16/16 review threads résolus), puis fusion sur `main` (`90f8dcb`).
- **2026-10-16** : Séquencement complet de l'implémentation logicielle et du backlog de tests TDD en une chaîne de 5 plans d'exécution sous `.GCC/branches/` (PR #7 fusionnée sur `main`, `046b9d9`).
- **2026-10-16** : Durcissement intégral de la gouvernance anti-mauvais-code sur le modèle de `HIVE-MIND` pour encadrer l'écriture du code par `Gemini 3.8 Flash` (`.coderabbit.yaml` fail-closed `5/5 + 0 findings`, `codecov.yml` `100% patch / 90% project`, `.gitleaks.toml` + `detect-secrets.sh` staged/history, `.dependency-cruiser.cjs`, verrou `ALLOW_CONFIG_EDIT=1`, Semgrep SAST, `<layer_map>` à 5 couches et `codebase-memory-mcp` dans `AGENTS.md` / `CLAUDE.md`).

## 🎯 Objective

Exécution séquentielle en TDD (Red-Green-Refactor) de la chaîne des 5 plans d'implémentation de **Colab AI Studio** sous la barrière de gouvernance durcie (Backend FastAPI & stockage atomique, Compilateur Brand Kit & orchestrateur SSE / Proxy LLM, Socle Frontend React SPA & Galerie, Floating Prompt Dock modulaire & Mode LLM, Worker Google Colab `ModelSwapper` & tests E2E).

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
- **2026-10-15** : Restructuration du diagramme de séquence proxy LLM (`08-sequence-proxy-llm.svg`) en opérateur `alt` exhaustif UML 2.5 séparant strictement le flux nominal (boucle de streaming et clôture `[DONE]`) de la branche d'annulation client (`request.is_disconnected() == true` ou signal client `Abort`) avec libération GPU sans envoi parasite sur socket rompue.
- **2026-10-15** : Remplacement des dénominations théoriques résiduelles (*Plafond de Miller*, *Loi de Déméter*) par des descriptions concrètes du modèle modulaire (*modularisation bornée à 7 composants*, *découplage direct et médiation FastAPI*) dans `02-composants.svg`, `07-sequence-brand-context.svg` et `README.md`.
- **2026-10-16** : Découpage de l'implémentation du code et des tests en une chaîne séquentielle de 5 plans (`.GCC/branches/plan_01` à `plan_05`) alignés sur les budgets de Pull Request et le cycle TDD par tranches verticales.
  - **Context** : Les spécifications (`SPECIFICATION.md`, `UI_SPECIFICATION.md`, `DESIGN_SPECIFICATION.md`) et les 11 diagrammes UML sont validés et fusionnés sur `main` ; l'écriture du code doit être séquencée proprement avec ses suites de tests.
  - **Discarded Options** : Plan monolithique unique couvrant Backend + Frontend + Colab (rejeté car il dépasserait la limite de taille de PR et retarderait la validation unitaire de chaque couche).
  - **Rationale** : Une chaîne de 5 plans ordonnés par dépendances (1. Stockage & Modèles $\rightarrow$ 2. Services Backend & SSE/Proxy $\rightarrow$ 3. Socle Frontend & Galerie $\rightarrow$ 4. Dock Modulaire, Brand Kit & Mode LLM $\rightarrow$ 5. Worker Colab `ModelSwapper` & E2E) garantit que chaque étape est immédiatement testable et livrable en PR atomique.
- **2026-10-16** : Alignement de la gouvernance anti-mauvais-code de `colab-ai-studio` sur l'architecture de défense en profondeur de `HIVE-MIND`.
  - **Context** : Le code va être implémenté par un modèle rapide (`Gemini 3.8 Flash`) qui nécessite des garde-fous techniques automatisés impossibles à contourner localement ou en CI.
  - **Discarded Options** : Conserver des règles uniquement déclaratives dans `AGENTS.md` sans verrouillage des fichiers de configuration de linter ni porte CodeRabbit/Codecov bloquante (rejeté car un modèle rapide peut tenter d'éditer `ruff.toml`/`tsconfig.json` ou d'ajouter des commentaires `# noqa`/`@ts-ignore`).
  - **Rationale** : Ajout de `.coderabbit.yaml` (`5/5 + 0 findings` fail-closed), `codecov.yml` (`100%` patch / `90%` project), `.gitleaks.toml` + `detect-secrets.sh` (staged & history, fail-closed), `.dependency-cruiser.cjs` (`no-circular: error`), verrou `ALLOW_CONFIG_EDIT=1` dans `.githooks/pre-commit`, Semgrep SAST, exclusion des fichiers documentaires du budget de lignes de code dans `governance.yml` (1000/2500 LoC), et synchronisation `AGENTS.md` / `CLAUDE.md` avec `<layer_map>` et `codebase-memory-mcp`.

## 🌿 Active Branches / Plans

- **Chaîne d'implémentation logicielle & TDD (5 plans séquentiels)** :
  1. [`.GCC/branches/plan_01_backend_storage_domain.md`](branches/plan_01_backend_storage_domain.md) : Socle Backend FastAPI, Modèles de Domaine Pydantic v2 (`TaskStatus`, `Generation`, `BrandKit`, `Project`, `StudioConfig`), `JSONDocumentStore` atomique (`asyncio.Lock` + `os.replace`), `MediaFileStore` (isolation `storagePath`), extraction Brand Kit (`brand_extractor.py`) et routes CRUD.
  2. [`.GCC/branches/plan_02_backend_brand_compiler_orchestrator.md`](branches/plan_02_backend_brand_compiler_orchestrator.md) : `BrandContextCompiler` (repli déterministe anglais & priorité des fentes), `TaskOrchestrator` SSE & annulation idempotente, garde-fou mode Local (`501`), et Proxy LLM streaming OpenAI (`/v1/chat/completions`).
  3. [`.GCC/branches/plan_03_frontend_foundation_gallery.md`](branches/plan_03_frontend_foundation_gallery.md) : Socle Frontend React 18 / Vite 5 / Tailwind v3 / Radix UI, Barre supérieure (Favoris, Ask, Projets `storagePath`, Notifications, Avatar Colab/Local), Galerie à 6 types de cartes et modale d'inspection avec **Remix**.
  4. [`.GCC/branches/plan_04_frontend_dock_brandkit_llm.md`](branches/plan_04_frontend_dock_brandkit_llm.md) : `FloatingPromptDock` modulaire piloté par `capabilities` (1 fichier par contrôle, règle de subsomption vidéo, durée `range`/`discrete`), Système Brand Kit complet et 5ᵉ onglet `LLM` conversationnel.
  5. [`.GCC/branches/plan_05_colab_worker_e2e.md`](branches/plan_05_colab_worker_e2e.md) : Worker GPU Google Colab (`ModelSwapper` VRAM T4 16 Go, `colab_worker.ipynb`), intégration E2E (`UC-01` à `UC-08`) et validation portable (`psutil`) du budget mémoire (< 80 Mo RAM).
- **Plans de modélisation complétés (PR #6 fusionnée sur `main`)** :
  - [`.GCC/branches/plan_uml-modelisation.md`](branches/plan_uml-modelisation.md) : Corpus UML et architecture cible sous `.modelisation/logiciel/`.
  - [`.GCC/branches/plan_corrections-uml.md`](branches/plan_corrections-uml.md) : Correction et consolidation des 11 diagrammes UML et du README.
  - [`.GCC/branches/plan_purge_academique.md`](branches/plan_purge_academique.md) : Purge des références externes et théoriques dans les diagrammes UML et le README.

## 📈 Current Status

- ✅ Terminé : Phase 1 (Spécifications et Modélisation UML fusionnées sur `main`), chaîne des 5 plans d'implémentation TDD (PR #7 fusionnée sur `main`), et mise à niveau de la gouvernance anti-mauvais-code sur le modèle de `HIVE-MIND`.
- 🔄 En cours : Livraison de la PR de durcissement de gouvernance (`chore/governance-hardening`), puis exécution du **Plan 01/05** (`plan_01_backend_storage_domain.md`).
- ⏳ En attente : Plans 02/05 à 05/05.

## 👉 Next Session Direction

Démarrer l'exécution TDD du **Plan 01/05** ([`.GCC/branches/plan_01_backend_storage_domain.md`](branches/plan_01_backend_storage_domain.md)) à partir de la Step 1 (initialisation de `app/`, `tests/`, modèles Pydantic v2 et persistance atomique JSON/médias).
