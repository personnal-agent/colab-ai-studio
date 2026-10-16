# Execution Plan: Plan 05/05 — Worker Distant Google Colab (`ModelSwapper`), Intégration E2E & Sobriété

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: Le worker distant Google Colab (`colab_worker/` + `colab_worker.ipynb`) implémente l'automate `ModelSwapper` (`11-etats-model-swapper.svg`) garantissant qu'un seul modèle lourd réside en VRAM T4 (16 Go) à la fois avec éviction mémoire complète (`del`, `gc.collect()`, `torch.cuda.empty_cache()`, `torch.cuda.ipc_collect()`), récupération sur `OutOfMemoryError` et arrêt coopératif sur annulation. Le cycle complet de bout en bout (UI/API locale $\rightarrow$ compilation Brand Kit $\rightarrow$ worker $\rightarrow$ SSE $\rightarrow$ rapatriement binaire $\rightarrow$ `data/generations.json`) et les contraintes d'empreinte mémoire locale (< 80 Mo RAM backend) sont validés par tests automatisés.
- **Pre-requisites**: Plans 01 à 04 complétés ([`.GCC/branches/plan_04_frontend_dock_brandkit_llm.md`](plan_04_frontend_dock_brandkit_llm.md)). Références : `SPECIFICATION.md` §5, `ARCHITECTURE.md` §1 & §4, diagramme `11-etats-model-swapper.svg`.

## 🛠️ Step-by-Step Sequence

### Step 1: Automate `ModelSwapper` et protocole d'éviction VRAM (TDD)

- [ ] **Action**: Écrire `tests/unit/test_model_swapper.py` (avec abstraction/mock de `torch.cuda` pour exécution sur machine hôte sans GPU) couvrant l'intégralité des transitions de `11-etats-model-swapper.svg` : initialisation à vide, chargement à la demande, réutilisation directe si le modèle requis est déjà résident, éviction préalable avant chargement d'un nouveau modèle, éviction automatique après délai d'inactivité (`gpu_idle == True`), et transition `EnRecuperationSaturation` sur `OutOfMemoryError`. Implémenter `app/colab_worker/model_swapper.py`.
- [ ] **Verify**: `pytest tests/unit/test_model_swapper.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 2: Serveur FastAPI du Worker Colab et pipelines d'inférence interruptibles (TDD)

- [ ] **Action**: Écrire `tests/api/test_colab_worker_api.py` puis implémenter `app/colab_worker/server.py` exposant les routes distantes consommées par le backend local (`/health` avec métriques VRAM/GPU, `/models`, `/models/switch`, `/infer` asynchrone avec callbacks de progression par étape, `/tasks/{task_id}/status`, `/tasks/{task_id}/cancel` interrompant la boucle d'inférence et libérant la VRAM, `/v1/chat/completions` streaming et `/files/{filename}` pour le rapatriement binaire).
- [ ] **Verify**: `pytest tests/api/test_colab_worker_api.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 3: Génération et validation du notebook `colab_worker.ipynb`

- [ ] **Action**: Construire `colab_worker.ipynb` structuré en cellules exécutables sur Google Colab (vérification GPU Tesla T4 `nvidia-smi`, installation des dépendances, initialisation du `ModelSwapper` et du serveur FastAPI distant, ouverture du tunnel chiffré ngrok / Cloudflare Tunnels et affichage de l'URL publique à copier dans Colab AI Studio) et écrire un test de validation structurelle JSON/nbformat dans `tests/unit/test_notebook_structure.py`.
- [ ] **Verify**: `pytest tests/unit/test_notebook_structure.py -q`
- **Verification Proof**:

```text
[Pending execution — paste raw pytest output here]
```

### Step 4: Tests d'intégration de bout en bout (E2E) et mesure isolée du budget mémoire

- [ ] **Action**: (1) Écrire `tests/e2e/test_full_pipeline.py` raccordant le backend local FastAPI au worker Colab simulé pour valider les 8 Cas d'Utilisation de la matrice de traçabilité (`UC-01` à `UC-08` : génération avec Brand Kit et rapatriement dans `outputs/YYYY-MM-DD/` et dans un `storagePath` de projet isolé, suivi SSE, annulation de tâche en cours, favoris/remix, proxy LLM streaming + interruption client). (2) Écrire `tests/e2e/test_memory_footprint.py` qui démarre le backend local FastAPI (`uvicorn app.main:app` servant `frontend/dist`) dans un **processus OS séparé** (`subprocess.Popen`), sans charger le worker Colab ni le lanceur de tests `pytest` dans ce processus, et mesure directement le RSS exclusif du processus backend (`/proc/<pid>/status` `VmRSS`) pour vérifier la contrainte `< 80 Mo RAM`.
- [ ] **Verify**: `pytest tests/ -q && npm --prefix frontend test -- --run && .githooks/pre-push`
- **Verification Proof**:

```text
[Pending execution — paste raw full suite & pre-push output here]
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Expiration ou coupure inopinée du tunnel ngrok / Cloudflare pendant une génération vidéo longue.
- **Mitigation**: Dès la réception de l'événement d'achèvement, `MediaFileStore` rapatrie immédiatement le binaire en local avant de marquer la tâche `completed`. Si le tunnel tombe pendant l'inférence, le timeout/heartbeat bascule proprement la tâche en `failed` avec un message explicite dans le centre de notifications `[🔔]`.
- **Risk**: Fragmentation de la VRAM sur Tesla T4 après plusieurs bascules entre un pipeline vidéo (Wan 2.1 / CogVideoX) et un LLM 7B/8B.
- **Mitigation**: Séquence stricte `del pipeline` $\rightarrow$ `del model` $\rightarrow$ `gc.collect()` $\rightarrow$ `torch.cuda.empty_cache()` $\rightarrow$ `torch.cuda.ipc_collect()` exécutée systématiquement par `ModelSwapper` avant toute nouvelle allocation.
