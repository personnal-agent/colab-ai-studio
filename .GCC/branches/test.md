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
