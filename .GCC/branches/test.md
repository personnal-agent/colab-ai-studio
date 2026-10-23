# Test Execution Log

## Verification Runs

### Run: 2026-10-23 — Plan 01/05 Backend Storage & Domain Models
- **Date**: 2026-10-23
- **Target**: Plan 01/05 (`tests/unit/test_models.py`, `tests/unit/test_json_store.py`, `tests/unit/test_media_store.py`, `tests/api/test_crud_routes.py`)
- **Status**: PASSED
- **Output / Evidence**:
  ```text
  ============================== 31 passed in 0.46s ==============================
  - tests/unit/test_models.py : 14 passed (TaskStatus, Generation, Parameters, References, Snapshots, BrandKit, Project, StudioConfig + LocalConfig.workerUrl)
  - tests/unit/test_json_store.py : 6 passed (lecture/écriture atomique, sérialisation concurrente, absence de résidu .tmp, résilience sur écriture partielle)
  - tests/unit/test_media_store.py : 6 passed (isolation Project.storagePath, partitionnement par défaut et chronologique, suppression, sécurité anti-traversée)
  - tests/api/test_crud_routes.py : 5 passed (health check, générations avec filtres favorite/mediaType/q, favori PATCH, suppression binaire DELETE, projets avec validation de chemin, brand kits Blank/files/website, configuration colab-url)
  - ruff check app tests : 0 erreur, 0 avertissement
  - psutil RSS : 47.63 Mo (< 80 Mo max)
  ```

### Run: 2026-10-23 — Plan 02/05 BrandContextCompiler, TaskOrchestrator SSE & Proxy LLM
- **Date**: 2026-10-23
- **Target**: Plan 02/05 (`tests/unit/test_brand_compiler.py`, `tests/unit/test_task_orchestrator.py`, `tests/api/test_generation_sse.py`, `tests/api/test_llm_proxy.py`, `tests/api/test_health_and_models.py`, `tests/api/test_local_worker_api.py`)
- **Status**: PASSED
- **Output / Evidence**:
  ```text
  ============================== 66 passed in 1.06s ==============================
  - tests/unit/test_brand_compiler.py : 4 passed (gabarit déterministe anglais, priorité des slots userRefs > kitRefs > logo, fallback texte seul, synthèse LLM)
  - tests/unit/test_task_orchestrator.py : 2 passed (cycle de vie nominal pending->running->completed, annulation idempotente)
  - tests/api/test_generation_sse.py : 3 passed (soumission asynchrone, 404 sur tâche inconnue, flux streaming SSE de progression)
  - tests/api/test_llm_proxy.py : 5 passed (streaming nominal OpenAI clôturé par [DONE], synchrone non-streaming, branche interruption client avec annulation amont sans [DONE], garde-fou proxy désactivé 503, worker inaccessible 503)
  - tests/api/test_health_and_models.py : 3 passed (diagnostic santé enrichi, relais liste modèles, changement de modèle)
  - tests/api/test_local_worker_api.py : 5 passed (health, switch, lifecycle, download, completions sync & stream + cancel)
  - ruff check app tests : 0 erreur, 0 avertissement
  - .githooks/pre-push : PASSED (Gitleaks 0 fuite, 66/66 tests, Ruff 0 erreur, Semgrep SAST 0 vulnérabilité, workflows valides)
  ```

### Run: 2026-10-23 — Plan 03/05 Frontend Foundation, Navigation, Projects & Gallery
- **Date**: 2026-10-23
- **Target**: Plan 03/05 (`frontend/src/__tests__/smoke.test.tsx`, `api_client.test.ts`, `header_projects.test.tsx`, `gallery.test.tsx`, `media_modal.test.tsx`)
- **Status**: PASSED
- **Output / Evidence**:
  ```text
  Test Files  5 passed (5)
  Tests  22 passed (22)
  - smoke.test.tsx : 1 passed (montage minimal App)
  - api_client.test.ts : 7 passed (health, generations, favorites toggle, task cancellation, projects CRUD, brand kits CRUD, SSE EventSource streaming)
  - header_projects.test.tsx : 5 passed (TopNavBar composition, WorkerStatusAvatar Colab/Local hot-switch, ProjectsDrawer avec custom storagePath, FavoriteFilterToggle, NotificationsPopover)
  - gallery.test.tsx : 6 passed (SearchAndFilterBar loupe & pills cumulatives, TaskProgressCard SSE & annulation, MediaCard 6 variantes & loop muet hover & favori, MediaGallery)
  - media_modal.test.tsx : 3 passed (MediaPlayerModal plein écran HTML5, rendu métadonnées & snapshot Brand Kit, action Remix avec réinjection complète du contexte)
  - Vite build : dist/ généré proprement en 16.55s (0 erreur, 0 avertissement bloquant)
  - Python tests : 66 passed in 1.15s
  - Total : 88 tests passés avec succès
  - Staged pre-commit : Gitleaks 0 fuite, ESLint 0 warning, Semgrep 0 vulnérabilité
  ```

### Run: 2026-10-23 — Plan 04/05 Floating Prompt Dock, Brand Kit & LLM Mode
- **Date**: 2026-10-23
- **Target**: Plan 04/05 (`dock_capabilities.test.tsx`, `video_subsumption.test.tsx`, `brand_kit.test.tsx`, `llm_mode.test.tsx`)
- **Status**: PASSED
- **Output / Evidence**:
  ```text
  Test Files  9 passed (9)
  Tests  47 passed (47)
  - dock_capabilities.test.tsx : 11 passed (contrôles atomiques batch, enhance, seed, aspect ratio, resolution, duration discrete/range, native audio, talking style, upscale scale/quality/fps, model selector popover avec badges, et registre dynamique ParameterRegistry)
  - video_subsumption.test.tsx : 4 passed (ReferenceSlot, règle de subsomption vidéo complète et combinaisons partielles, avertissement limite maxImageRefs, adaptation Image/LipSync/Upscale)
  - brand_kit.test.tsx : 6 passed (BrandKitHoverCard, BrandKitSelectorPopover état vide et tri lastUsedAt, PromptEditorWithChip chip atomique et Backspace, BrandKitCreateModal 3 sources Blank/Files/Website, BrandKitInspectorModal 8 sections et Use button)
  - llm_mode.test.tsx : 4 passed (Bascule 5e onglet LLM avec masquage fentes/pills média, bandeau API local OpenAI, persistance superficielle [H] sans perte de contexte, conversation streaming avec stop AbortController, verrouillage du dock pendant génération)
  - Vite build : dist/ généré proprement en 17.08s (JS bundle minifié 337.25 kB gzip 101.14 kB)
  - depcruise : 0 violation de cycle (58 modules, 184 dépendances)
  - Python tests : 66 passed in 1.18s
  - Total : 113 tests passés avec succès (47 frontend + 66 backend)
  - ESLint & Ruff : 0 warning, 0 error
  ```

### Run: 2026-10-23 — Plan 05/05 Worker Distant Colab (ModelSwapper), Notebook & Intégration E2E
- **Date**: 2026-10-23
- **Target**: Plan 05/05 (`tests/unit/test_model_swapper.py`, `tests/api/test_colab_worker_api.py`, `tests/unit/test_notebook_structure.py`, `tests/e2e/test_full_pipeline.py`, `tests/e2e/test_memory_footprint.py`)
- **Status**: PASSED
- **Output / Evidence**:
  ```text
  Python Test Files: 12 passed
  Tests: 89 passed in 2.16s
  - test_model_swapper.py : 6 passed (transitions 11-etats, eviction complete, idle timeout, OOM recovery EnRecuperationSaturation)
  - test_colab_worker_api.py : 5 passed (health/VRAM, switch model, infer & cancel lifecycle, file download, chat completions stream)
  - test_notebook_structure.py : 3 passed (validite JSON nbformat v4, cellules clefs GPU/dependencies/swapper/tunnels/server)
  - test_full_pipeline.py : 8 passed (UC-01 generation nominale Brand Kit, UC-02 project storagePath, UC-03 SSE task tracking, UC-04 task cancellation, UC-05 favorite/remix, UC-06 hot-switch local-colab, UC-07 proxy LLM streaming/abort, UC-08 brand compiler fallback)
  - test_memory_footprint.py : 1 passed (mesure independante via processus OS uvicorn, RSS = 48.24 Mo < 80 Mo max)
  Frontend Vitest Files: 9 passed
  Tests: 47 passed in 27.64s
  Total Test Suite: 136 tests verts (89 Python + 47 TypeScript)
  Vite build : dist/ genere proprement
  Depcruise : 0 violation de dependance circulaire (58 modules)
  Linters : Ruff (0 warning, 0 error), ESLint (0 warning, 0 error)
  Security : Semgrep SAST 0 vulnerabilite, Gitleaks 0 secret
  ```
