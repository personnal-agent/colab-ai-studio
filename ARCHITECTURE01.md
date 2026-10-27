# Architecture & Cartographie du Projet — Omniforge

> **Statut documentaire — cible à implémenter.** Les documents numérotés décrivent l'évolution Omniforge ; ils ne prouvent pas sa disponibilité. Le code actuel accepte seulement `colab` et `local` via le contrat worker (`/infer`, `/tasks/{task_id}/status`, `/tasks/{task_id}/cancel`, `/files/{path}`). OAuth Colab automatique, TPU/LRU, ComfyUI direct, mode API, catalogue hors-ligne, LoRAs, audio/3D et validation `acceptedInputTypes` restent des objectifs. Voir [SPECIFICATION01.md](SPECIFICATION01.md#4-spécifications-des-3-moteurs-dexécution-colab--local--api) pour les écarts avec l'existant.

**Catalogue cible** : le sélecteur lit uniquement `data/models.json` ; scans Local et imports custom y écrivent via `JSONDocumentStore`. Les signatures de `known_models_catalog.json` servent de gabarits en lecture seule. Voir le contrat détaillé dans [SPECIFICATION01.md](SPECIFICATION01.md).

## 1. Vue d'Ensemble du Système

**Omniforge** est une plateforme de création multimédia assistée par IA structurée autour d'un backend local FastAPI ultra-léger (< 80 Mo de RAM) et d'une application monopage React (SPA) exposant un commutateur global **`[ Studio | Agents ]`**, un catalogue utilisateur cible (`data/models.json`, disponibilité hors-ligne à implémenter ; actuellement `GET /api/models` interroge le worker et peut retourner 503), et, dans l’architecture cible, trois moteurs d’exécution distincts (`api` indisponible actuellement) :
1. **`Colab` (GPU & TPU distants orchestrés par le Backend)** : connexion directe au compte Google (OAuth2), provisionnement et tunnel gérés automatiquement par `ColabSessionOrchestrator` (zéro `ngrok` ou URL/secret manuel), détection matérielle réelle sur **GPU CUDA** (`torch.cuda.mem_get_info()` : T4 16 Go, L4 24 Go, A100 40/80 Go) comme sur **Google Cloud TPU** (`torch_xla` HBM : TPU v5e, v6e, v2-8) et cache mémoire multi-modèles LRU (`ModelSwapper`).
2. **`Local` (GPU PC)** : exécute les modèles en arrière-plan via **ComfyUI en mode "Headless API"** (`127.0.0.1:8188`, mode hybride : connexion à une instance active ou lancement/arrêt en tâche de fond sans ouvrir son interface à nœuds).
3. **`API` (Clés API)** : effectue des appels directs aux fournisseurs externes configurés par l'utilisateur.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  MACHINE LOCALE (PC)                                   │
│                                                                                        │
│   ┌──────────────────────────────────┐          ┌──────────────────────────────────┐   │
│   │        Frontend SPA React        │          │      Backend Local FastAPI       │   │
│   │  (Vite 5, Tailwind v3, Radix UI) │  HTTP /  │   (Python 3.10+, Orchestrateur)  │   │
│   │                                  │◄────────►│                                  │   │
│   │  • Switch : [ Studio | Agents ]  │   SSE    │  • WorkerGateway (Colab/Local/API│   │
│   │  • 6 Pôles : Image, Video,       │          │  • LocalModelRegistry & LoRAs    │   │
│   │    Audio, Lip sync,              │          │  • ComfyWorkflowCompiler         │   │
│   │    Upscaling, 3D Gen             │          │  • Persistance JSON & Médias     │   │
│   │  • Pilule LoRA & Filtre fichiers │          │                                  │   │
│   └──────────────────────────────────┘          └───┬──────────────┬───────────┬───┘   │
└─────────────────────────────────────────────────────┼──────────────┼───────────┼───────┘
                                                      │              │           │
                         ┌────────────────────────────┘              │           └────────────────────────┐
                         ▼                                           ▼                                    ▼
┌────────────────────────────────────────────────┐  ┌────────────────────────────────┐  ┌────────────────────────────────┐
│       MOTEUR LOCAL (COMFYUI HEADLESS)          │  │     MOTEUR COLAB (TUNNEL)      │  │          MOTEUR API            │
│                                                │  │                                │  │                                │
│  • ComfyUI Headless API (127.0.0.1:8188)       │  │  • Serveur FastAPI (T4 16 Go)  │  │  • Appels directs fournisseurs │
│    (Hybride : rattaché ou lancé en fond)       │  │  • Dynamic Model Swapper       │  │    via clés API utilisateur    │
│  • Détection auto (/object_info) + Custom      │  │  • Pipelines Python Diffusers  │  │                                │
│  • Exécution des workflows .api.json & LoRAs   │  │                                │  │                                │
└────────────────────────────────────────────────┘  └────────────────────────────────┘  └────────────────────────────────┘
```

---

## 2. Cartographie des Répertoires

```
omniforge/
├── SPECIFICATION01.md             # Spécifications fonctionnelles et techniques Omniforge
├── UI_SPECIFICATION01.md          # Spécifications ergonomiques (6 pôles, LoRA, Local, Switch)
├── DESIGN_SPECIFICATION01.md      # Tokens de design, pilule LoRA, switch Studio/Agents
├── ARCHITECTURE01.md              # Cartographie d'architecture et flux du système (ce fichier)
│
├── app/                           # Backend local FastAPI
│   ├── main.py                    # Point d'entrée de l'API locale et distribution SPA
│   ├── config.py                  # Configuration globale (Colab, Local ComfyUI, API)
│   ├── models/
│   │   └── domain.py              # Modèles Pydantic v2 (Generation, LoraConfig, ModelSpec...)
│   ├── api/                       # Routeurs HTTP & SSE
│   │   ├── routes_config.py       # Bascule Colab / Local / API & processus ComfyUI
│   │   ├── routes_models.py       # Scan des modèles connus, ajout de workflow custom & LoRAs
│   │   ├── routes_generation.py   # Génération multimédia (6 pôles) + validation des fichiers
│   │   └── routes_crud.py         # Générations, Favoris, Projets, Brand Kits
│   ├── services/                  # Logique métier et orchestration
│   │   ├── worker_gateway.py      # Routage selon executionMode (colab | local | api)
│   │   ├── colab_orchestrator.py  # Connexion Google OAuth, allocation GPU/TPU (T4/L4/A100/TPU) & pont auto
│   │   ├── comfy_process.py       # Gestion hybride du processus ComfyUI Headless (:8188)
│   │   ├── model_registry.py      # Catalogue utilisateur dynamique (data/models.json) + auto-scan
│   │   ├── lora_registry.py       # Registre et import des LoRAs (baseModel, triggerWord, aperçu)
│   │   ├── comfy_compiler.py      # Compilation JSON simple -> Workflow API ComfyUI + LoRA
│   │   ├── api_provider_client.py # Exécution directe via clés API externes
│   │   ├── brand_compiler.py      # Compilation déterministe du Brand Kit
│   │   └── task_orchestrator.py   # Cycle de vie des tâches, bus SSE et annulation
│   ├── colab_worker/              # Serveur distant Google Colab (GPU CUDA & TPU XLA)
│   │   ├── server.py              # Chargement dynamique de modèles (zéro liste codée en dur)
│   │   └── model_swapper.py       # Cache mémoire multi-modèles LRU (GPU VRAM & TPU HBM torch_xla)
│   └── storage/                   # Persistance atomique
│       ├── json_store.py          # JSONDocumentStore (asyncio.Lock + .tmp + os.replace)
│       └── media_store.py         # MediaFileStore (isolation storagePath et outputs/)
│
├── workflows/                     # Gabarits ComfyUI API (.api.json) des modèles connus
│   ├── video/                     # text_to_video.api.json, first_frame_to_video.api.json, last_frame_to_video.api.json, first_last_frame_to_video.api.json, reference_to_video.api.json, hybrid_reference_flf.api.json
│   ├── image/                     # text_to_image.api.json, image_reference.api.json
│   ├── audio/                     # text_to_audio.api.json, voice_clone.api.json, music.api.json, video_to_audio.api.json
│   ├── lipsync/                   # lipsync.api.json
│   ├── upscale/                   # upscale_image.api.json, upscale_video.api.json
│   └── 3d/                        # text_to_3d.api.json, single_image_to_3d.api.json, multiview_to_3d.api.json, rig_animate_3d.api.json
│
├── frontend/                      # Application React SPA (TypeScript strict)
│   └── src/
│       ├── components/
│       │   ├── layout/            # TopNavBar avec Switch [ Studio | Agents ] & Sélecteur Moteur
│       │   ├── gallery/           # Grille média (7 types de cartes dont 3D) et modale Remix
│       │   ├── dock/              # FloatingPromptDock (6 onglets, LoraPillControl, contrôles atomiques)
│       │   ├── models/            # Modale Add / Map Model (import workflow_api.json)
│       │   └── brandkit/          # Popover et modales Brand Kit
│       ├── context/               # État réactif (mode Studio/Agents, moteur actif, modèle, LoRAs)
│       └── services/              # Client API et SSE typé
│
├── data/                          # Persistance JSON locale
│   ├── generations.json
│   ├── brand_kits.json
│   ├── projects.json
│   ├── config.json
│   ├── known_models_catalog.json
│   ├── models.json                # Catalogue unique éditable, workflows custom inclus
│   └── loras.json
│
└── outputs/                       # Binaires générés (.mp4, .png, .wav, .mp3, .flac, .glb, .fbx, .obj)
```

---

## 3. Flux de Données & Responsabilités

### 3.1. Cycle de Génération Cible selon le Moteur Actif (`Colab` | `Local` | `API`)
**État actuel Local** : les requêtes passent par `local.workerUrl` : `POST /infer`, `GET /tasks/{task_id}/status`, `POST /tasks/{task_id}/cancel`, `GET /files/{path}`. La liste ci-dessous décrit le flux cible, incluant les extensions LoRA, ComfyUI et API.

1. L’utilisateur choisit l'un des 6 onglets (`Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`), sélectionne un modèle, active éventuellement un ou plusieurs **LoRAs** compatibles et dépose ses références (le Dock bloque tout fichier dont le type n'est pas accepté par le modèle).
2. La requête JSON simple est envoyée à `POST /api/generate/media`.
3. `WorkerGateway` achemine la tâche selon `executionMode` :
   - **En mode `Colab`** : envoi au serveur Colab (`POST /infer`) qui charge le pipeline Python Diffusers via `ModelSwapper`.
   - **Cible `Local` — intégration ComfyUI directe non implémentée** : `ComfyWorkflowCompiler` sélectionne le gabarit `.api.json` correspondant aux références fournies (noms canoniques listés dans `workflows/` ci-dessus et dans `SPECIFICATION01.md` §4.2.3), téléverse les fichiers de référence vers ComfyUI Headless (`POST /upload/image`), injecte les paramètres et les `triggerWord` des LoRAs, insère les nœuds `LoraLoader` en série avec leur poids (`0.8` par défaut ou valeur affinée), et soumet le graphe à `POST http://127.0.0.1:8188/prompt`.
   - **En mode `API`** : `ApiProviderClient` appelle directement l'API externe configurée.
4. La progression est diffusée en direct via Server-Sent Events (`GET /api/tasks/{task_id}/status`).
5. Dès l'achèvement, `MediaFileStore` enregistre le binaire dans le dossier résolu (`storagePath` du projet, `outputs/projects/<id>/` ou `outputs/YYYY-MM-DD/`) et `JSONDocumentStore` met à jour `data/generations.json`.
