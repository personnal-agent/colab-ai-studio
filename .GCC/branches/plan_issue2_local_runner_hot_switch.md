# Execution Plan: Issue #2 — Runner Local GPU & Bascule à Chaud Local / Colab

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: Le backend local FastAPI ne connaît qu'**un seul contrat de worker** (`/health`, `/models`, `/models/switch`, `/infer`, `/tasks/{task_id}/status`, `/tasks/{task_id}/cancel`, `/files/{filename}`, `/v1/chat/completions` — défini au Plan 05 Step 2). Le mode d'exécution (`executionMode: "colab" | "local"`) ne fait que sélectionner l'URL de base de ce worker (`colab.tunnelUrl` ou `local.workerUrl`) au moment de chaque appel, ce qui rend la bascule possible à chaud sans redémarrage. La bascule est refusée (`409 Conflict`) tant qu'une tâche est en état `pending` ou `running`. Le backend reste sous 80 Mo RAM : aucune dépendance GPU (`torch`, ComfyUI) n'est importée dans `app/` hors de `app/local_worker/` et `app/colab_worker/`, qui tournent dans des processus séparés.
- **Pre-requisites**: Plan 01 complété ([`plan_01_backend_storage_domain.md`](plan_01_backend_storage_domain.md)) avec `LocalConfig.workerUrl`. Ce plan **remplace** le garde-fou `501 Not Implemented` prévu au Plan 02 Step 2 ([`plan_02_backend_brand_compiler_orchestrator.md`](plan_02_backend_brand_compiler_orchestrator.md)) et fournit l'API consommée par l'avatar du Plan 03 ([`plan_03_frontend_foundation_gallery.md`](plan_03_frontend_foundation_gallery.md)). Machine hôte de référence pour le runner local : GPU NVIDIA 16 Go VRAM (même classe que la T4 Colab), ComfyUI sur `127.0.0.1:8188`, serveur LLM compatible OpenAI (LM Studio) sur `127.0.0.1:1234`.

## 🛠️ Step-by-Step Sequence

### Step 1: Schéma `LocalConfig.workerUrl` et route de commutation `POST /api/config/execution-mode` (TDD)

- [ ] **Action**: Étendre `LocalConfig` (`app/models/domain.py`) avec `workerUrl: str = "http://127.0.0.1:8190"` (en conservant `device` et `threads`). Écrire `tests/api/test_execution_mode.py` couvrant : (1) `GET /api/config` renvoie le mode actif sans fuite de secret (`compilerLlm.apiKey` masqué) ; (2) `POST /api/config/execution-mode` `{"executionMode": "local"}` persiste via `JSONDocumentStore` et renvoie `200` ; (3) valeur invalide → `422` ; (4) tâche `pending`/`running` présente → `409 Conflict` avec `{"detail": "...", "activeTaskIds": [...]}` et aucune écriture ; (5) publication d'un événement `config` sur le bus SSE. Implémenter `app/api/routes_config.py`.
- [ ] **Verify**: `pytest tests/api/test_execution_mode.py -q && ruff check app tests`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest & ruff output here]
```

### Step 2: Passerelle de worker unique `WorkerGateway` (remplace `colab_client.py` et le stub `501`) (TDD)

- [ ] **Action**: Écrire `tests/unit/test_worker_gateway.py` vérifiant : (1) la résolution de l'URL de base relue à chaque appel (`colab.tunnelUrl` vs `local.workerUrl`), donc une bascule effective sans redémarrage ; (2) `colab` sans `tunnelUrl` → erreur explicite `503` « Worker Colab non configuré » ; (3) worker injoignable → `503` avec le mode et l'URL en cause ; (4) `GET /api/health` expose `{"executionMode", "worker": {"reachable", "latencyMs", "gpu", "vramFreeMb"}}` pour le mode actif. Implémenter `app/services/worker_gateway.py` (`httpx.AsyncClient`, timeouts bornés, fermeture dans `lifespan`). `GET /api/models`, `POST /api/models/switch` et `POST /api/generate/media` passent tous par cette passerelle.
- [ ] **Verify**: `pytest tests/unit/test_worker_gateway.py tests/api/test_health_and_models.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 3: Serveur du worker local `app/local_worker/` conforme au contrat (TDD, ComfyUI simulé)

- [ ] **Action**: Écrire `tests/api/test_local_worker_api.py` (ComfyUI et serveur LLM simulés via `httpx.MockTransport`) puis implémenter `app/local_worker/server.py` (processus séparé, `uvicorn app.local_worker.server:app --port 8190`) exposant le contrat complet. Les modèles et leurs `capabilities` proviennent d'un **manifeste local hors dépôt** (`LOCAL_WORKER_MANIFEST`, défaut `~/.colab-ai-studio/local_models.json`) validé par Pydantic ; seul `app/local_worker/local_models.example.json` (générique, sans workflow privé) est versionné. `/health` lit les métriques GPU via `nvidia-smi --query-gpu` (repli `gpu: null` sans GPU).
- [ ] **Verify**: `pytest tests/api/test_local_worker_api.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 4: Adaptateurs d'inférence `ComfyUIBackend` et `OpenAICompatibleBackend` (TDD)

- [ ] **Action**: Écrire `tests/unit/test_comfyui_backend.py` et `tests/unit/test_openai_backend.py` puis implémenter `app/local_worker/backends/comfyui.py` (injection des paramètres dans le gabarit de workflow via les liaisons `bindings` du manifeste : `prompt`, `seed`, `width`, `height`, `frames`, `fps`, images de référence téléversées par `POST /upload/image` ; soumission `POST /prompt` ; progression via `GET /history/{prompt_id}` ; annulation via `POST /interrupt` + `POST /queue` delete ; récupération du binaire via `GET /view`) et `app/local_worker/backends/openai_compat.py` (relais streaming de `/v1/chat/completions` vers LM Studio avec arrêt immédiat sur déconnexion client).
- [ ] **Verify**: `pytest tests/unit/test_comfyui_backend.py tests/unit/test_openai_backend.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 5: Validation réelle sur la machine hôte GPU (manuelle, hors CI)

- [ ] **Action**: Rédiger `~/.colab-ai-studio/local_models.json` (hors dépôt) déclarant les gabarits vidéo et image locaux de l'utilisateur et le LLM local ; démarrer `app/local_worker` sur `:8190` et le backend sur `:8000` ; enchaîner `POST /api/config/execution-mode local` → `POST /api/generate/media` (vidéo puis image) → SSE → rapatriement dans `storagePath` → `POST /api/config/execution-mode colab` (refus `409` pendant une tâche, succès après).
- [ ] **Verify**: Journal `curl` brut + présence des fichiers et de leur entrée dans `data/generations.json`.
- **Verification Proof**:

```text
[Pending execution — paste raw curl / SSE output here]
```

### Step 6: Contrôle de bascule dans l'IHM (intégré au Plan 03)

- [ ] **Action**: Dans le Plan 03, `frontend/src/stores/configStore.ts` et le menu de l'avatar `[👤]` : choix `Local` / `Colab`, état grisé inerte `#9CA3AF` remplacé par les métriques du worker actif, message bloquant si `409`, mise à jour par l'événement SSE `config`.
- [ ] **Verify**: `npm --prefix frontend test -- --run && npm --prefix frontend run typecheck`
- **Verification Proof**:

```text
[Pending execution — paste raw vitest & tsc output here]
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Bascule pendant une génération longue (vidéo de plusieurs minutes) laissant une tâche orpheline sur l'ancien worker.
- **Mitigation**: `409 Conflict` tant qu'une tâche est `pending`/`running` ; chaque `Generation` mémorise l'`executionMode` et l'URL du worker qui l'exécute, de sorte que le suivi SSE, l'annulation et le rapatriement continuent de viser le worker d'origine.
- **Risk**: Fuite des workflows ou modèles privés de l'utilisateur dans le dépôt public.
- **Mitigation**: Manifeste et gabarits chargés depuis un chemin hors dépôt (`LOCAL_WORKER_MANIFEST`) ; seul un exemple générique est versionné.
- **Risk**: Saturation VRAM si ComfyUI et le serveur LLM local se partagent les 16 Go.
- **Mitigation**: `/models/switch` du worker local libère ComfyUI (`POST /free` `{"unload_models": true, "free_memory": true}`) avant de router vers le LLM, et inversement — même rôle que le `ModelSwapper` Colab.
- **Risk**: Un gabarit ComfyUI ne couvre qu'un plan unique, alors que le studio actuel enchaîne plusieurs plans.
- **Mitigation**: L'enchaînement multi-plans passe par le mode *Video-as-Ingredient* / *Frame Chaining* du dock (une génération = un plan), conformément à `SPECIFICATION.md` ; aucun moteur de chaîne n'est dupliqué dans le worker.
