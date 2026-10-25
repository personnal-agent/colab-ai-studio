# Architecture & Cartographie du Projet — Omniforge

## 1. Vue d'Ensemble du Système

**Omniforge** est une plateforme de création multimédia assistée par IA structurée autour d'un backend local FastAPI ultra-léger (< 80 Mo de RAM) et d'une application monopage React (SPA) exposant un commutateur global **`[ Studio | Agents ]`**, un catalogue de modèles géré par l'utilisateur (`data/models.json`, disponible hors-ligne), et trois moteurs d'exécution distincts :
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
│   ├── video/                     # t2v.api.json, i2v_start.api.json, flf2v.api.json, ref2v.api.json
│   ├── image/                     # t2i.api.json, i2i_ref.api.json
│   ├── audio/                     # voice_tts.api.json, voice_clone.api.json, music.api.json, sfx_v2a.api.json
│   ├── lipsync/                   # lipsync.api.json
│   ├── upscale/                   # upscale_image.api.json, upscale_video.api.json
│   └── 3d/                        # single_to_3d.api.json, multiview_to_3d.api.json, rig_animate.api.json
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
│   ├── custom_models.json
│   └── loras.json
│
└── outputs/                       # Binaires générés (.mp4, .png, .wav, .mp3, .flac, .glb, .fbx, .obj)
```

---

## 3. Flux de Données & Responsabilités

### 3.1. Cycle de Génération selon le Moteur Actif (`Colab` | `Local` | `API`)
1. L'utilisateur choisit l'un des 6 onglets (`Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`), sélectionne un modèle, active éventuellement un ou plusieurs **LoRAs** compatibles et dépose ses références (le Dock bloque tout fichier dont le type n'est pas accepté par le modèle).
2. La requête JSON simple est envoyée à `POST /api/generate/media`.
3. `WorkerGateway` achemine la tâche selon `executionMode` :
   - **En mode `Colab`** : envoi au serveur Colab (`POST /infer`) qui charge le pipeline Python Diffusers via `ModelSwapper`.
   - **En mode `Local`** : `ComfyWorkflowCompiler` sélectionne le gabarit `.api.json` correspondant aux références fournies (`t2v`, `i2v_start`, `flf2v`, `ref2v`, `audio`, `3d`, etc.), téléverse les fichiers de référence vers ComfyUI Headless (`POST /upload/image`), injecte les paramètres et les `triggerWord` des LoRAs, insère les nœuds `LoraLoader` en série avec leur poids (`0.8` par défaut ou valeur affinée), et soumet le graphe à `POST http://127.0.0.1:8188/prompt`.
   - **En mode `API`** : `ApiProviderClient` appelle directement l'API externe configurée.
4. La progression est diffusée en direct via Server-Sent Events (`GET /api/tasks/{task_id}/status`).
5. Dès l'achèvement, `MediaFileStore` enregistre le binaire dans le dossier résolu (`storagePath` du projet, `outputs/projects/<id>/` ou `outputs/YYYY-MM-DD/`) et `JSONDocumentStore` met à jour `data/generations.json`.
