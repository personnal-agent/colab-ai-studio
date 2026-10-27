# Test Backlog

## Pending Test Scenarios (Sequenced by Plan Chain)

### Plan 01/05 — Backend Storage & Domain Models (`plan_01_backend_storage_domain.md`)

- [x] **Scenario**: Validation des schémas Pydantic v2 (`tests/unit/test_models.py`)
  - Verification: Couverture complète de `TaskStatus` (`pending`, `running`, `completed`, `cancelled`, `failed`), `Generation`, `GenerationParameters`, `GenerationReferences`, `BrandKitSnapshot`, `BrandKit`, `Project`, `StudioConfig`.
- [x] **Scenario**: Concurrence et écriture atomique POSIX sur `JSONDocumentStore` (`tests/unit/test_json_store.py`)
  - Verification: Exécuter `asyncio.gather` avec 10 écritures concurrentes sur `generations.json` sans perte de mise à jour ni corruption JSON (`asyncio.Lock` + `os.replace`).
- [x] **Scenario**: Isolation physique de stockage dans `MediaFileStore` (`tests/unit/test_media_store.py`)
  - Verification: Vérifier que `project.storagePath` stocke exclusivement les médias dans le dossier cible (0 fichier dupliqué dans `outputs/`), `outputs/projects/<id>/` par défaut pour un projet, et `outputs/YYYY-MM-DD/` hors projet.
- [x] **Scenario**: Endpoints CRUD documentaires et extraction d'identité Brand Kit (`tests/api/test_crud_routes.py`)
  - Verification: Tester `GET/DELETE /api/generations`, `PATCH /api/generations/{id}/favorite`, `GET/POST /api/brand-kits` (création `Blank` + extraction d'actifs depuis fichiers [SVG, images, texte, CSS, JSON] et `Website` [URL]), `GET/POST /api/projects`, `POST /api/config/colab-url`.

### Plan 02/05 — BrandContextCompiler, TaskOrchestrator SSE & LLM Proxy (`plan_02_backend_brand_compiler_orchestrator.md`)

- [ ] **Scenario**: Compilation de contexte de marque et repli déterministe anglais (`tests/unit/test_brand_compiler.py`)
  - Verification: Vérifier la synthèse LLM, le basculement automatique sur le gabarit anglais en cas d'erreur/absence de clé, la priorité stricte des fentes (`1. userRefs` sanctuarisés et tronqués aux $N$ premiers si dépassement de `maxImageRefs`, `2. kit referenceImages`, `3. logo`), et le repli texte seul si `maxImageRefs == 0`.
- [ ] **Scenario**: Routage multi-worker et diagnostic Colab (`tests/api/test_health_and_models.py`)
  - Verification: Vérifier le routage `WorkerGateway` pour `executionMode: "local"` (Issue #2) et `executionMode: "colab"`, et valider `GET /api/health`, `GET /api/models`, `POST /api/models/switch`.
- [ ] **Scenario**: Cycle de vie de tâche asynchrone, streaming SSE et annulation idempotente (`tests/unit/test_task_orchestrator.py`, `tests/api/test_generation_sse.py`)
  - Verification: Tester `POST /api/generate/media`, le flux SSE `GET /api/tasks/{task_id}/status`, le rapatriement binaire à l'achèvement (`completed`), le timeout 120s (`failed`), et l'annulation `POST /api/tasks/{task_id}/cancel` (`cancelled`).
- [ ] **Scenario**: Proxy LLM streaming OpenAI et interruption client (`tests/api/test_llm_proxy.py`)
  - Verification: Valider les deux branches du fragment `alt` sur `POST /v1/chat/completions` : streaming nominal `choices[].delta` + `[DONE]` et arrêt immédiat du flux Colab lors de la déconnexion du client (`request.is_disconnected()`).

### Plan 03/05 — Socle Frontend React SPA, Galerie & Projets (`plan_03_frontend_foundation_gallery.md`)

- [ ] **Scenario**: Client API/SSE et contrats TypeScript (`frontend/src/__tests__/api_client.test.ts`)
  - Verification: Vérifier le typage et la souscription SSE.
- [ ] **Scenario**: Barre supérieure, statut Worker Colab/Local et tiroir Projets (`frontend/src/__tests__/header_projects.test.tsx`)
  - Verification: Vérifier le filtre `[★]`, la création de projet avec `storagePath`, et l'avatar `[👤]` actif en mode Colab vs grisé inerte (`#9CA3AF`) en mode Local.
- [ ] **Scenario**: Recherche, filtres cumulatifs, galerie à 6 types de cartes et modale Remix (`frontend/src/__tests__/gallery.test.tsx`, `frontend/src/__tests__/media_modal.test.tsx`)
  - Verification: Vérifier le filtrage temps réel, l'affichage des 6 cartes (`Image`, `Video`, `Audio`, `Upscaled image 4K`, `Upscaled video 4K`, `Lip sync`), la carte SSE en tête de galerie, et la réinjection complète des paramètres au clic sur **Remix**.

### Plan 04/05 — Floating Prompt Dock Modulaire, Brand Kit & Mode LLM (`plan_04_frontend_dock_brandkit_llm.md`)

- [ ] **Scenario**: Registre de paramètres atomiques piloté par `capabilities` (`frontend/src/__tests__/dock_capabilities.test.tsx`)
  - Verification: Vérifier l'injection systématique des contrôles universels (`⚏ 1`–`4`, `🪄 On`, `seed`) et le montage conditionnel des pilules spécifiques, notamment la durée `range` (curseur continu) vs `discrete` (pilules).
- [ ] **Scenario**: Règle de subsomption obligatoire du conditionnement vidéo (`frontend/src/__tests__/video_subsumption.test.tsx`)
  - Verification: Vérifier qu'un modèle supportant le mode complet (`Start frame` + `End frame` + `Ingredients`) active toutes les combinaisons partielles et unitaires, et affiche un avertissement en cas de dépassement de `maxImageRefs`.
- [ ] **Scenario**: Système Brand Kit, extraction d'identité et chip atomique `[@NomDuKit]` (`frontend/src/__tests__/brand_kit.test.tsx`)
  - Verification: Vérifier le popover, la Hover Card, l'unicité et la suppression atomique du chip `[@NomDuKit]`, le raccordement de `[ Continue ]` sur les 3 sources (`Blank`, `Brand files`, `Website`) et la présence effective des actifs extraits (logos, couleurs hex, polices, `overview`) dans l'inspecteur à 8 sections.
- [ ] **Scenario**: Bascule du 5ᵉ onglet `LLM` et mémoire d'état `[H]` (`frontend/src/__tests__/llm_mode.test.tsx`)
  - Verification: Vérifier le masquage des contrôles média, le filtrage sur les modèles LLM, le bandeau `http://localhost:8000/v1/chat/completions`, le streaming SSE avec bouton Stop, et la restauration intacte du brouillon au retour sur un onglet média.

### Plan 05/05 — Worker Distant Google Colab & Intégration de Bout en Bout (`plan_05_colab_worker_e2e.md`)

- [ ] **Scenario**: Automate `ModelSwapper` et éviction VRAM (`tests/unit/test_model_swapper.py`)
  - Verification: Vérifier le chargement à la demande, la réutilisation sans rechargement, l'éviction complète (`del`, `gc.collect()`, `torch.cuda.empty_cache()`, `torch.cuda.ipc_collect()`), l'éviction par inactivité et la récupération sur `OutOfMemoryError`.
- [ ] **Scenario**: API du Worker Colab et structure `colab_worker.ipynb` (`tests/api/test_colab_worker_api.py`, `tests/unit/test_notebook_structure.py`)
  - Verification: Vérifier les routes distantes (`/infer`, `/tasks/{id}/cancel`, `/v1/chat/completions`) et la validité JSON/cellules du notebook Colab.
- [ ] **Scenario**: Parcours E2E (`UC-01` à `UC-08`) et mesure RSS portable dans un sous-processus backend isolé (< 80 Mo) (`tests/e2e/test_full_pipeline.py`, `tests/e2e/test_memory_footprint.py`)
  - Verification: Valider le parcours complet avec worker simulé, mesurer de façon portable (`psutil.Process(proc.pid).memory_info().rss` compatible Linux/macOS/Windows) le RSS exclusif du processus backend FastAPI séparé (sans worker ni lanceur de tests chargé dedans), et exécuter `.githooks/pre-push`.


## PR #29 — Nouvelle revue après publication
- [x] Premier lot publié au commit `e985ef5f5db3375b71761c67f1be4c966d3fb612` ; sixième passe locale sans finding, CI distante verte.
- [x] Accord instructions agents et autorisation de livraison sur la PR acquis.
- [x] Nouveau lot documentaire validé et relu : 3 remarques corrigées puis 9 mineures (1 corrigée, 8 non reproduites).
- [ ] Publier le nouveau lot et vérifier les fils ; ne pas confondre garanties cibles et runtime existant.
