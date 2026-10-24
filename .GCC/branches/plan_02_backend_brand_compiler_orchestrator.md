# Execution Plan: Plan 02/05 — BrandContextCompiler, Orchestrateur Asynchrone SSE & Proxy LLM

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: Le backend compile les Brand Kits avec repli déterministe anglais sans jamais bloquer l'utilisateur, respecte l'ordre strict de priorité des fentes de référence (`userRefs` > `kitRefs` > `logo`), orchestre le cycle de vie des tâches distantes (`pending` $\rightarrow$ `running` $\rightarrow$ `completed` / `cancelled` / `failed`) avec flux SSE et annulation idempotente, route les inférences vers le worker du mode actif (Colab ou local, cf. issue #2), et streame `/v1/chat/completions` au format OpenAI avec interruption propre sur déconnexion client (`alt` exhaustif).
- **Pre-requisites**: Plan 01 complété ([`.GCC/branches/plan_01_backend_storage_domain.md`](plan_01_backend_storage_domain.md)). Références : `SPECIFICATION.md` §4.3–§4.4, diagrammes `05`, `06`, `07`, `08`, `10`. Suivant dans la chaîne : [`.GCC/branches/plan_03_frontend_foundation_gallery.md`](plan_03_frontend_foundation_gallery.md).

## 🛠️ Step-by-Step Sequence

### Step 1: Compilateur de contexte de marque (`BrandContextCompiler`) (TDD)

- [x] **Action**: Écrire `tests/unit/test_brand_compiler.py` couvrant : (1) synthèse par LLM externe quand `COMPILER_LLM_API_KEY` est actif ; (2) bascule immédiate sur le gabarit déterministe anglais en cas d'absence de clé, timeout ou HTTP 5xx (`[Brand Identity: {name}] Style: ...` et `negative_prompt`) ; (3) priorité des slots d'images (`1. userRefs` sanctuarisés et tronqués aux $N$ premiers si `len(userRefs) > maxImageRefs`, `2. referenceImages` du kit, `3. logo` avec consigne *"Here is the brand logo, make sure your generation remains coherent with this brand identity."*) ; (4) repli texte seul si `maxImageRefs == 0` ; (5) création du `BrandKitSnapshot`. Implémenter `app/services/brand_compiler.py` selon `07-sequence-brand-context.svg`.
- [x] **Verify**: `pytest tests/unit/test_brand_compiler.py -q`
- **Verification Proof**:

```text
......                                                                   [100%]
6 passed in 0.33s
```

### Step 2: Client HTTP asynchrone Colab, garde-fou mode Local (`501`) et routes modèles/santé (TDD)

- [x] **Action**: Écrire `tests/api/test_health_and_models.py` vérifiant : (1) `GET /api/health` (latence, VRAM libre, statut tunnel) ; (2) `GET /api/models` et `POST /api/models/switch` ; (3) routage des routes d'inférence vers le worker du mode actif. **Amendé le 2026-10-23** : le garde-fou `501` est remplacé par la passerelle `WorkerGateway` et le runner local de l'issue #2 ([`plan_issue2_local_runner_hot_switch.md`](plan_issue2_local_runner_hot_switch.md), Steps 1–2), réalisés avant ce plan. Implémenter `app/api/routes_models.py` au-dessus de `app/services/worker_gateway.py`.
- [x] **Verify**: `pytest tests/api/test_health_and_models.py -q`
- **Verification Proof**:

```text
....                                                                     [100%]
4 passed in 0.71s
```

### Step 3: Orchestrateur de tâches asynchrones, flux SSE et annulation idempotente (TDD)

- [x] **Action**: Écrire `tests/unit/test_task_orchestrator.py` et `tests/api/test_generation_sse.py` couvrant `06-sequence-generation.svg` et `10-etats-tache-media.svg` : lancement `POST /api/generate/media`, création de l'entrée `Generation` en état `pending` puis `running`, diffusion SSE sur `GET /api/tasks/{task_id}/status`, rapatriement automatique du binaire via `MediaFileStore` et passage à `completed`, gestion du timeout (120s $\rightarrow$ `failed`), et annulation idempotente `POST /api/tasks/{task_id}/cancel` propageant l'arrêt au worker Colab et persistant l'état stable `cancelled`. Implémenter `app/services/task_orchestrator.py` et `app/api/routes_generation.py`.
- [x] **Verify**: `pytest tests/unit/test_task_orchestrator.py tests/api/test_generation_sse.py -q`
- **Verification Proof**:

```text
.....                                                                    [100%]
5 passed in 0.78s
```

### Step 4: Proxy LLM streaming compatible OpenAI (`/v1/chat/completions`) (TDD)

- [x] **Action**: Écrire `tests/api/test_llm_proxy.py` validant les deux branches du fragment `alt` de `08-sequence-proxy-llm.svg` : (1) flux nominal SSE `data: {"choices":[{"delta":{"content":"..."}}]}` clôturé par `data: [DONE]` ; (2) branche d'interruption client (`request.is_disconnected() == True` / `AbortSignal`) interrompant immédiatement le flux amont vers Colab pour libérer la VRAM sans émettre sur la socket fermée. Implémenter `app/api/routes_llm_proxy.py`.
- [x] **Verify**: `pytest tests/ -q && .githooks/pre-push`
- **Verification Proof**:

```text
...............................................................          [100%]
63 passed in 1.73s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 PRE-PUSH — Validation Globale, Secrets Historique & Tests Unitaires
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/3] Détection de secrets sur l'historique complet (gitleaks)...
🔍 gitleaks 8.24.0 — historique du dépôt...
11:01AM INF 62 commits scanned.
11:01AM INF scanned ~2027928 bytes (2.03 MB) in 2.89s
11:01AM INF no leaks found
✅ Aucun secret détecté

[2/3] Tests unitaires (timeout : 5 minutes)...
🧪 Recherche et exécution des suites de tests unitaires...
  Exécution des tests Python (pytest)...
...............................................................          [100%]
63 passed in 1.73s
  ✓ Tests Python validés.

[3/3] Quality Gate intégrale (dépôt entier)...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️  QUALITY GATE — Périmètre : full
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] Vérification de sécurité (fichiers sensibles, secrets et configs)...
[1b/5] Scan gitleaks de l'index...
🔍 gitleaks 8.24.0 — index stagé...
11:01AM INF 1 commits scanned.
11:01AM INF scanned ~69617 bytes (69.62 KB) in 320ms
11:01AM INF no leaks found
✅ Aucun secret détecté
[2/5] Validation Backend Python...
  Exécution de Ruff...
All checks passed!
  ✓ Contrôles Python validés.
[3/5] Validation Frontend TypeScript/React...
  Aucun fichier Frontend à analyser.
[4/5] Scan SAST sécurité (Semgrep)...
  ✓ Scan SAST Semgrep validé (0 vulnérabilité).
[5/5] Validation des invariants d'architecture et workflows...
  ✓ Invariants des workflows GitHub validés.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Quality Gate passée avec succès (full).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Pré-push validé (gitleaks history + tests + Quality Gate full). Envoi vers origin autorisé.
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Condition de course (*race condition*) lorsque l'utilisateur appelle `POST /api/tasks/{task_id}/cancel` au moment exact où le worker Colab termine le téléchargement du média.
- **Mitigation**: Transition d'état protégée par le verrou de l'orchestrateur ; si l'annulation arrive avant la validation finale de `completed`, le fichier partiel est nettoyé et l'état `cancelled` fait foi ; si `completed` est déjà persisté, l'annulation retourne l'état actuel de façon idempotente sans corrompre le média.
- **Risk**: Fuite de descripteurs ou blocage de la boucle d'événements FastAPI lors du streaming SSE de longue durée.
- **Mitigation**: Utilisation de `httpx.AsyncClient` avec streaming par chunks asynchrones et fermeture explicite du contexte dans un bloc `try...finally`.
