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


## 2026-10-27 — PR #29, corrections documentaires

Périmètre : docs et libellés SVG ; aucun code runtime modifié. Aucun scénario de code supplémentaire introduit.

### `PYTHONPATH=. /home/vercel-sandbox/runtime/venv/bin/python /tmp/pr29-validate-docs.py`

```text
Documentation checks passed: 5 JSON blocks, current request/config schemas, 14 UML types, SVG XML, local links, statuses, ports and tokens.
```

### `python -m py_compile .github/scripts/*.py && ruff check .`

```text
All checks passed!
```

### `python -m pytest tests/ -q`

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 9.18s
```

### `npm --prefix frontend run typecheck`

```text
npm error Missing script: "typecheck"
npm error
npm error To see a list of scripts, run:
npm error   npm run
npm error A complete log of this run can be found in: /home/vercel-sandbox/.npm/_logs/2026-10-27T16_16_11_469Z-debug-0.log
```

### `npm --prefix frontend run build`

```text

> colab-ai-studio-frontend@0.1.0 build
> tsc && vite build

vite v6.4.5 building for production...
transforming...
✓ 1666 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.81 kB │ gzip:   0.45 kB
dist/assets/index-B7FgmD5i.css   44.34 kB │ gzip:   7.63 kB
dist/assets/index-FJ2Dz8uL.js   350.06 kB │ gzip: 103.80 kB
✓ built in 3.46s
```

### `npm --prefix frontend test -- --run`

```text

> colab-ai-studio-frontend@0.1.0 test
> vitest --run


 RUN  v4.1.12 /home/vercel-sandbox/workspace/repos/github.com/personnal-agent/colab-ai-studio/frontend


 Test Files  9 passed (9)
      Tests  74 passed (74)
   Start at  16:16:21
   Duration  6.14s (transform 931ms, setup 938ms, import 3.36s, tests 3.83s, environment 6.78s)

```

### `PATH=/home/vercel-sandbox/runtime/venv/bin:$PATH .githooks/pre-push`

```text
[0;34m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
[0;34m🚀 PRE-PUSH — Validation Globale, Secrets Historique & Tests Unitaires[0m
[0;34m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m

[0;34m[1/3] Détection de secrets sur l'historique complet (gitleaks)...[0m
[0;34m🔍 gitleaks 8.30.1 — historique du dépôt...[0m
4:17PM INF 67 commits scanned.
4:17PM INF scanned ~2400593 bytes (2.40 MB) in 457ms
4:17PM INF no leaks found
[0;32m✅ Aucun secret détecté[0m

[0;34m[2/3] Tests unitaires (timeout : 5 minutes)...[0m
[0;34m🧪 Recherche et exécution des suites de tests unitaires...[0m
[0;34m  Exécution des tests Python (pytest)...[0m
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 6.36s
[0;32m  ✓ Tests Python validés.[0m
[0;34m  Exécution des tests Frontend (npm test)...[0m

> colab-ai-studio-frontend@0.1.0 test
> vitest --run


 RUN  v4.1.12 /home/vercel-sandbox/workspace/repos/github.com/personnal-agent/colab-ai-studio/frontend


 Test Files  9 passed (9)
      Tests  74 passed (74)
   Start at  16:17:24
   Duration  6.11s (transform 978ms, setup 1.33s, import 3.39s, tests 3.93s, environment 6.84s)

[0;32m  ✓ Tests Frontend validés.[0m

[0;34m[3/3] Quality Gate intégrale (dépôt entier)...[0m
[0;34m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
[0;34m🛡️  QUALITY GATE — Périmètre : full[0m
[0;34m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
[0;34m[1/5] Vérification de sécurité (fichiers sensibles, secrets et configs)...[0m
[0;34m[1b/5] Scan gitleaks de l'index...[0m
[0;34m🔍 gitleaks 8.30.1 — index stagé...[0m
4:17PM INF 0 commits scanned.
4:17PM INF scanned ~0 bytes (0) in 244ms
4:17PM INF no leaks found
[0;32m✅ Aucun secret détecté[0m
[0;34m[2/5] Validation Backend Python...[0m
  Fichiers Python ciblés :
   • .github/scripts/verify_workflows.py
   • app/__init__.py
   • app/api/__init__.py
   • app/api/routes_config.py
   • app/api/routes_crud.py
   • app/api/routes_generation.py
   • app/api/routes_llm_proxy.py
   • app/api/routes_models.py
   • app/colab_worker/model_swapper.py
   • app/colab_worker/server.py
   • app/config.py
   • app/main.py
   • app/models/__init__.py
   • app/models/domain.py
   • app/services/__init__.py
   • app/services/brand_compiler.py
   • app/services/brand_extractor.py
   • app/services/task_orchestrator.py
   • app/services/worker_gateway.py
   • app/storage/__init__.py
   • app/storage/json_store.py
   • app/storage/media_store.py
   • tests/__init__.py
   • tests/api/__init__.py
   • tests/api/test_colab_worker_api.py
   • tests/api/test_crud_routes.py
   • tests/api/test_execution_mode.py
   • tests/api/test_generation_sse.py
   • tests/api/test_health_and_models.py
   • tests/api/test_llm_proxy.py
   • tests/e2e/__init__.py
   • tests/e2e/test_full_pipeline.py
   • tests/e2e/test_memory_footprint.py
   • tests/unit/__init__.py
   • tests/unit/test_brand_compiler.py
   • tests/unit/test_json_store.py
   • tests/unit/test_media_store.py
   • tests/unit/test_model_swapper.py
   • tests/unit/test_models.py
   • tests/unit/test_notebook_structure.py
   • tests/unit/test_task_orchestrator.py
   • tests/unit/test_worker_gateway.py
  Exécution de Ruff...
All checks passed!
[0;32m  ✓ Contrôles Python validés.[0m
[0;34m[3/5] Validation Frontend TypeScript/React...[0m
  Fichiers Frontend ciblés :
   • frontend/.eslintrc.cjs
   • frontend/postcss.config.js
   • frontend/src/App.tsx
   • frontend/src/__tests__/api_client.test.ts
   • frontend/src/__tests__/app.test.tsx
   • frontend/src/__tests__/brand_kit.test.tsx
   • frontend/src/__tests__/dock_capabilities.test.tsx
   • frontend/src/__tests__/gallery.test.tsx
   • frontend/src/__tests__/header_projects.test.tsx
   • frontend/src/__tests__/llm_mode.test.tsx
   • frontend/src/__tests__/media_modal.test.tsx
   • frontend/src/__tests__/video_subsumption.test.tsx
   • frontend/src/components/brand-kit/BrandKitCreateModal.tsx
   • frontend/src/components/brand-kit/BrandKitHoverCard.tsx
   • frontend/src/components/brand-kit/BrandKitInspectorModal.tsx
   • frontend/src/components/brand-kit/BrandKitSelectorPopover.tsx
   • frontend/src/components/brand-kit/PromptEditorWithChip.tsx
   • frontend/src/components/dock/FloatingPromptDock.tsx
   • frontend/src/components/dock/LlmChatView.tsx
   • frontend/src/components/dock/ParameterRegistry.tsx
   • frontend/src/components/dock/conditioning/ConditioningTray.tsx
   • frontend/src/components/dock/conditioning/ReferenceSlot.tsx
   • frontend/src/components/dock/controls/AspectRatioPill.tsx
   • frontend/src/components/dock/controls/BatchCountPill.tsx
   • frontend/src/components/dock/controls/DurationControlPill.tsx
   • frontend/src/components/dock/controls/EnhancePromptPill.tsx
   • frontend/src/components/dock/controls/FineSettingsPopover.tsx
   • frontend/src/components/dock/controls/ModelSelectorPopover.tsx
   • frontend/src/components/dock/controls/NativeAudioPill.tsx
   • frontend/src/components/dock/controls/ResolutionPill.tsx
   • frontend/src/components/dock/controls/SeedControlPill.tsx
   • frontend/src/components/dock/controls/TalkingStylePill.tsx
   • frontend/src/components/dock/controls/UpscaleFrameRatePill.tsx
   • frontend/src/components/dock/controls/UpscaleQualityPill.tsx
   • frontend/src/components/dock/controls/UpscaleScalePill.tsx
   • frontend/src/components/gallery/MediaCard.tsx
   • frontend/src/components/gallery/MediaGallery.tsx
   • frontend/src/components/gallery/MediaPlayerModal.tsx
   • frontend/src/components/gallery/SearchAndFilterBar.tsx
   • frontend/src/components/gallery/TaskProgressCard.tsx
   • frontend/src/components/header/AskHelpDrawer.tsx
   • frontend/src/components/header/FavoriteFilterToggle.tsx
   • frontend/src/components/header/NotificationsPopover.tsx
   • frontend/src/components/header/ProjectsDrawer.tsx
   • frontend/src/components/header/TopNavBar.tsx
   • frontend/src/components/header/WorkerStatusAvatar.tsx
   • frontend/src/main.tsx
   • frontend/src/services/apiClient.ts
   • frontend/src/setupTests.ts
   • frontend/src/types/studio.ts
   • frontend/tailwind.config.js
   • frontend/vite.config.ts
  Audit des dépendances de production (npm audit high/critical)...
found 0 vulnerabilities
  Compilation TypeScript stricte (npx tsc --noEmit)...
  Analyse d'architecture et cycles de dépendances (dependency-cruiser)...

✔ no dependency violations found (57 modules, 203 dependencies cruised)

  Exécution du linter Frontend (zéro warning toléré)...

> colab-ai-studio-frontend@0.1.0 lint
> eslint src/ --max-warnings=0

[0;32m  ✓ Contrôles Frontend validés.[0m
[0;34m[4/5] Scan SAST sécurité (Semgrep)...[0m
Downloading pydantic-core (2.1MiB)
Downloading cryptography (4.5MiB)
Downloading pygments (1.2MiB)
Downloading semgrep (68.5MiB)
 Downloaded pygments
 Downloaded pydantic-core
 Downloaded cryptography
 Downloaded semgrep
Installed 66 packages in 257ms
[0;32m  ✓ Scan SAST Semgrep validé (0 vulnérabilité).[0m
[0;34m[5/5] Validation des invariants d'architecture et workflows...[0m
[0;32m  ✓ Invariants des workflows GitHub validés.[0m
[0;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
[0;32m✅ Quality Gate passée avec succès (full).[0m
[0;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m

[0;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
[0;32m✅ Pré-push validé (gitleaks history + tests + Quality Gate full). Envoi vers origin autorisé.[0m
[0;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[0m
```

Le script typecheck est absent ; couverture équivalente par tsc dans le build et tsc --noEmit dans le hook. Premier pre-push bloqué par gitleaks absent, puis installation vérifiée par SHA-256 et succès du hook complet. Revue locale initiale : neuf retours (un majeur, huit mineurs, dont trois répétitions de sujets), corrigés ; passe finale en attente. Inspection SVG via Chromium cloud, labels ports/états lisibles. Les tests antérieurs du backlog restent historiques et ne sont pas requalifiés par cette exécution.

### Instructions agents approuvées par l’utilisateur

Patch AGENTS.md et CLAUDE.md appliqué après accord explicite dans cette session.
```text
Agent guidance checks passed: AGENTS.md and CLAUDE.md identical; v3 references, UI registry, TPU memory contract and local links valid.
```
Revue indépendante ciblée en lecture seule : zéro finding résiduel. Références/précédence v3, registre UI six pôles et séquence TPU conformes ; aucune modification par le reviewer.

### Revue locale finale et corrections documentaires

CodeRabbit passe 1 : 9 remarques (1 majeure, 8 mineures, trois répétitions de sujets), traitées.
CodeRabbit passe 2 : 4 remarques mineures, traitées. Événement terminal observé :
```text
{"type":"complete","status":"review_completed","findings":4,"outcome":"completed","message":"Review completed"}
```
Revue ciblée des quatre derniers sujets : deux formulations normatives résiduelles dans README02 repérées puis retirées. Aucune passe CodeRabbit ultérieure à zéro finding n’est revendiquée.

Dernière commande : `PYTHONPATH=. /home/vercel-sandbox/runtime/venv/bin/python /home/vercel-sandbox/workspace/workspace-context/pr29-validate-docs.py` (exit 0).
```text
Documentation checks passed: 6 JSON blocks, current request/config schemas, 14 UML types, SVG XML, local links, statuses, ports and tokens.
Final review fixes passed: academic citations removed, 7 engineering rules retained, effective health URLs and current handoff verified.
```

`git diff --check` : sortie vide, exit 0. Application/tests/dépendances inchangés depuis le pre-push intégral vert ; résultats réutilisés. Aucun commit, push ni thread distant résolu.

### Corrections de la revue imposée par le hook

La tentative historique `npm --prefix frontend run typecheck` ci-dessus reste en échec observé (script absent). Les deux guides agents documentent maintenant la commande supportée, exécutée depuis la racine :
```sh
(cd frontend && npx tsc --noEmit)
```
Sortie stdout/stderr vide, exit 0. Les guides sont identiques et distinguent le worker manuel actuel des capacités OAuth/TPU/LRU cibles, ainsi que le téléchargement en mémoire actuel du streaming incrémental futur. Validation documentaire et `git diff --check` : exit 0. Suites applicatives/build/gate réutilisés, leurs entrées sont inchangées.

CodeRabbit passe 3 : événement terminal `review_completed`, 6 remarques mineures sur quatre sujets (deux doublons). Toutes traitées et vérifiées ; passe de confirmation lancée après terminaison.

CodeRabbit passe 4 : terminal `review_completed`, 5 remarques (1 majeure et 4 mineures, dont un doublon). Contrat `resource_v3` de `.hilo/index.sqlite` rétabli dans le plan, DoD avec URL effectives et test distinct des défauts, compte des passes harmonisé, première preuve 5 JSON explicitement historique. Toutes traitées.

Dernière validation documentaire : exit 0, six JSON. Assertions supplémentaires :
```text
Canonical SQLite index and effective endpoint DoD assertions passed.
```
`git diff --check` : exit 0, sortie vide.

### Clôture des revues locales

Cinq passes CodeRabbit terminées : 9, 4, 6, 5 puis 3 remarques (doublons inclus), toutes traitées. Dernière passe : trois mineures, vérifiées par assertions ciblées ; aucune nouvelle passe CLI à zéro finding revendiquée.
Passe 5 : RG-01 inclut config.json, description des trois moteurs qualifiée comme cible, références du socle conservées avec les cibles dans le registre agents. Commande exécutée (exit 0) :
`/home/vercel-sandbox/runtime/venv/bin/python /home/vercel-sandbox/workspace/workspace-context/pr29-validate-final.py`
```text
Final review checks passed: identical agent guides, baseline references, target capabilities, supported typecheck, config persistence, canonical SQLite index and effective endpoint DoD.
```
Dernier validateur documentaire : six JSON, schémas actuels, XML/liens/états/ports/tokens, sept règles conservées ; exit 0. Aucun commit/push effectué.


## Nouvelle revue distante de la PR #29 — 2026-10-27 après e985ef5

Premier lot publié au commit `e985ef5f5db3375b71761c67f1be4c966d3fb612` après autorisation explicite ; sixième passe locale zéro finding, CI distante ensuite verte. Le nouveau retour distant 5671529062 contient cinq remarques directes, un nitpick et un complément : Auth séparé et cycle de vie explicite, quatre sondes dont Local Service, coordinateur FastAPI unique / Gateway écrivain SQLite unique, publication no-replace avec preuve de propriété, dépendances externes de validation, prérequis Colab et inventaire handoff.

Revue indépendante en lecture seule : incohérence temporaire conservé/supprimé et état incertain après timeout SQLite repérés et corrigés ; aucune modification par le reviewer. Sources Colab officielles vérifiées via HTTPS (outil web indisponible 401), scope/allowlist/eligible/proxy-token confirmés. Les deux anciens fils Local/formats restent des limites runtime, non déclarées implémentées.

Commandes exécutées depuis la racine (exit 0) :
`PYTHONPATH=. /home/vercel-sandbox/runtime/venv/bin/python /home/vercel-sandbox/workspace/workspace-context/pr29-validate-docs.py`
```text
Documentation checks passed: 6 JSON blocks, current request/config schemas, 14 UML types, SVG XML, local links, statuses, ports and tokens.
Final review fixes passed: academic citations removed, 7 engineering rules retained, effective health URLs and current handoff verified.
```
`/home/vercel-sandbox/runtime/venv/bin/python /home/vercel-sandbox/workspace/workspace-context/pr29-validate-followup.py`
```text
Follow-up documentation checks passed: Auth lifecycle, four readiness probes, publication owner/no-replace/recovery, Colab prerequisites, portable handoff warning; 104 application/gate inputs unchanged.
```
`git diff --check` : sortie vide, exit 0. Les 99 tests backend, 74 frontend, build et gate du premier lot sont réutilisés après contrôle des empreintes inchangées. Le hook obligatoire sera exécuté normalement lors du push. Les scripts et logs `workspace-context/` sont externes à ce dépôt et absents d’un checkout indépendant.

Prochaine étape : revue CodeRabbit du nouveau diff, puis publication autorisée. Les événements terminaux et résultats de livraison seront conservés dans le registre externe de validation pour garder le patch effectivement relu inchangé.


### Revue locale du nouveau lot

La première session CodeRabbit a été interrompue par la reprise d’environnement, sans résultat terminal observé. La session relancée a terminé `review_completed`, exit 0, trois remarques (deux majeures, une mineure) : attendre la fin de l’opération Colab et ses erreurs, définir le prérequis de durabilité Windows, synchroniser l’index GCC de publication. Toutes corrigées. Les sources officielles operations.get/wait ont été consultées ; aucune garantie Windows actuellement implémentée ou testée n’est revendiquée.

Après corrections, les deux commandes documentaires ci-dessus ont été réexécutées : mêmes sorties, exit 0 ; `git diff --check` sortie vide, exit 0. Les assertions vérifient aussi Operation.done/error et le blocage de publication durable avant validation de l’adaptateur Windows. Passe de confirmation sélectionnée ; résultat terminal puis livraison seront enregistrés dans le registre externe `workspace-context/validation-record.md` et les logs associés sans modifier le patch relu.


### Résultat de la passe de confirmation

CodeRabbit : terminal `review_completed`, exit 0, neuf remarques mineures. Une précision valide corrigée : repli Colab manuel uniquement si URL/secret effectif déjà configurés et worker joignable ; sinon Local déjà configuré/joignable, ou état Configuration requise. Huit suggestions d’espacement non reproduites : aucun blanc répété dans les 28 lignes source citées, indentation Markdown préservée.

Commande : `/home/vercel-sandbox/runtime/venv/bin/python /home/vercel-sandbox/workspace/workspace-context/pr29-check-review-spacing.py`, exit 0 :
```text
Review spacing check passed: no repeated whitespace in 28 cited source lines (Markdown indentation preserved).
```
Les deux validateurs documentaires ont été réexécutés après correction, mêmes sorties, exit 0. `git diff --check` : sortie vide, exit 0. Bilan du nouveau lot : première session interrompue sans résultat, puis 3 remarques (2 majeures/1 mineure) corrigées, puis 9 mineures (1 corrigée/8 non reproduites). Aucune passe zéro finding revendiquée pour ce lot. Livraison autorisée sur la même PR ; preuve de publication et nouveaux résultats des hooks dans le registre externe.
