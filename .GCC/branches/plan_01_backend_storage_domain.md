# Execution Plan: Plan 01/05 — Socle Backend FastAPI, Modèles de Domaine & Persistance Atomique

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: Le backend local FastAPI démarre avec une empreinte mémoire inférieure à 80 Mo RAM, expose les schémas Pydantic v2 conformes au diagramme `04-modele-de-donnees.svg` et à `SPECIFICATION.md` §4.2, garantit des écritures JSON strictement sérialisées par `asyncio.Lock` et atomiques via `os.replace` dans `data/`, et isole physiquement les binaires générés selon la règle `Project.storagePath` exclusif vs `outputs/projects/<id>/` vs `outputs/YYYY-MM-DD/`.
- **Pre-requisites**: Python 3.10+, spécifications validées (`SPECIFICATION.md`, `ARCHITECTURE.md`, `.modelisation/logiciel/diagrammes/04-modele-de-donnees.svg`). Suivant dans la chaîne : [`plan_issue2_local_runner_hot_switch.md`](plan_issue2_local_runner_hot_switch.md) puis [`.GCC/branches/plan_02_backend_brand_compiler_orchestrator.md`](plan_02_backend_brand_compiler_orchestrator.md).

## 🛠️ Step-by-Step Sequence

### Step 1: Initialisation du projet Python et configuration de test pytest

- [x] **Action**: Créer `requirements.txt` (avec `fastapi`, `uvicorn`, `pydantic>=2.7`, `httpx`, `pytest`, `pytest-asyncio`, `psutil`), initialiser l'arborescence `app/{__init__,api,models,services,storage}/` et `tests/{unit,api,e2e}/`, ainsi que `app/config.py` pour la résolution des chemins (`data/`, `outputs/`).
- [x] **Verify**: `pytest tests/ -q && python3 -m py_compile app/config.py`
- **Verification Proof**:

```text
All checks passed!
python3 -m py_compile app/config.py -> exit code 0
```

### Step 2: Modèles de domaine Pydantic v2 et énumération TaskStatus (TDD)

- [x] **Action**: Écrire en premier les tests unitaires `tests/unit/test_models.py` couvrant `TaskStatus` (`pending`, `running`, `completed`, `cancelled`, `failed`), `Generation`, `GenerationParameters`, `GenerationReferences`, `BrandKitSnapshot`, `BrandKit` (`Logo`, `Color`, `Font`, `Asset`, `Guideline`), `Project` et `StudioConfig` (`ColabConfig`, `LocalConfig` enrichi de `workerUrl` pour l'issue #2, `CompilerLlmConfig`, `LlmProxyConfig`). Implémenter ensuite `app/models/domain.py` conformément à `04-modele-de-donnees.svg` et `SPECIFICATION.md` §4.2.1–§4.2.4.
- [x] **Verify**: `pytest tests/unit/test_models.py -q`
- **Verification Proof**:

```text
..............                                                           [100%]
14 passed in 0.19s
All checks passed!
```

### Step 3: Gestionnaire de persistance documentaire JSON atomique (`JSONDocumentStore`) (TDD)

- [x] **Action**: Écrire `tests/unit/test_json_store.py` testant la sérialisation concurrente (`asyncio.gather` avec 10 écritures parallèles sérialisées) et la résilience aux écritures partielles. Implémenter `app/storage/json_store.py` avec un `asyncio.Lock` dédié par collection (`generations.json`, `brand_kits.json`, `projects.json`, `config.json`), écriture dans un fichier temporaire du même répertoire et renommage atomique POSIX `os.replace`.
- [x] **Verify**: `pytest tests/unit/test_json_store.py -q`
- **Verification Proof**:

```text
......                                                                   [100%]
6 passed in 0.10s
All checks passed!
```

### Step 4: Gestionnaire de fichiers médias et isolation de stockage (`MediaFileStore`) (TDD)

- [x] **Action**: Écrire `tests/unit/test_media_store.py` vérifiant les 3 règles de destination : (1) `project.storagePath` personnalisé renseigné $\rightarrow$ écriture exclusive dans `storagePath` avec 0 fichier créé dans `outputs/` ; (2) projet sans `storagePath` $\rightarrow$ `outputs/projects/<id>/` ; (3) hors projet $\rightarrow$ `outputs/YYYY-MM-DD/`. Implémenter `app/storage/media_store.py` (résolution de chemin, sauvegarde binaire et miniature, suppression sur disque, rejet sécurisé des chemins sensibles).
- [x] **Verify**: `pytest tests/unit/test_media_store.py -q`
- **Verification Proof**:

```text
......                                                                   [100%]
6 passed in 0.16s
All checks passed!
```

### Step 5: Point d'entrée FastAPI, extraction d'identité Brand Kit et routes CRUD documentaires (TDD)

- [x] **Action**: Écrire `tests/api/test_crud_routes.py` puis implémenter `app/main.py`, `app/services/brand_extractor.py` et `app/api/routes_crud.py` exposant : `GET /api/health`, `GET /api/generations` (filtres `favorite`, `mediaType`, `projectId`, `q`), `PATCH /api/generations/{id}/favorite`, `DELETE /api/generations/{id}` (suppression atomique JSON + fichier via `MediaFileStore`), `GET /api/brand-kits`, `POST /api/brand-kits` (Blank, files, website), `GET /api/projects`, `POST /api/projects` (avec validation de `storagePath`), et `POST /api/config/colab-url`.
- [x] **Verify**: `pytest tests/ -q && ruff check app tests`
- **Verification Proof**:

```text
============================== 31 passed in 0.46s ==============================
All checks passed!
Mesure isolée de l'empreinte mémoire : PID=3291 RSS = 47.63 Mo (< 80 Mo requis).
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Corruption de `data/generations.json` lors de la complétion simultanée de plusieurs tirages parallèles (`batch 1..4`) et d'une action utilisateur (`PATCH` favori ou `DELETE`).
- **Mitigation**: Un `asyncio.Lock` par fichier JSON combiné à `tempfile.mkstemp(dir=data_dir)` + `os.replace()` garantit l'atomicité POSIX et la sérialisation stricte en mémoire.
- **Risk**: Traversée de répertoire (*path traversal*) via un `storagePath` malveillant dans `POST /api/projects`.
- **Mitigation**: Normalisation `Path.resolve()`, interdiction des chemins système sensibles (`/etc`, `/proc`, `/sys`, `.git`, `.githooks`, `.gouvernance`, `.GCC`) et validation d'accès en écriture.
