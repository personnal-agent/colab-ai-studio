# Spécifications Fonctionnelles & Techniques — Omniforge

## 1. Vision du Projet

**Omniforge** est un système hybride de création multimédia par intelligence artificielle (image, vidéo UGC et cinématique tous formats réseaux, audio voix/musique/SFX, synchronisation labiale, upscaling et génération 3D) conçu pour fonctionner selon trois modes d'exécution au choix :
1. **`Colab` (GPU & TPU distants orchestrés automatiquement par le Backend)** : connexion directe au **compte Google** de l'utilisateur (OAuth2), détection automatique des accélérateurs disponibles sur le compte (**GPU NVIDIA** : `T4 16 Go`, `L4 24 Go`, `A100 40/80 Go` ; **Google Cloud TPU** : `TPU v5e`, `TPU v6e`, `TPU v2-8` avec mémoire HBM 16 Go à 128 Go, et unités de calcul *Compute Units*), provisionnement et tunnel chiffré orchestrés à 100 % par le backend local (**zéro `ngrok` ou URL/secret à copier-coller par l'utilisateur**), et cache mémoire multi-modèles LRU basé sur la VRAM (CUDA) ou HBM (TPU `torch_xla`) réellement disponible.
2. **`Local` (GPU PC)** : exécution locale en arrière-plan via **ComfyUI en mode "Headless API"** (`127.0.0.1:8188`) sans jamais ouvrir ni exposer son interface à nœuds.
3. **`API` (Clés API externes)** : appels directs aux fournisseurs d'inférence distants via les clés API configurées par l'utilisateur.

Le catalogue de modèles n'est **jamais codé en dur** dans le serveur Python : il est persisté localement dans `data/models.json` (toujours accessible hors-ligne) et l'utilisateur peut librement **ajouter, configurer ou supprimer ses propres modèles** dans l'interface.

L'interface expose en barre supérieure un commutateur global **`[ Studio | Agents ]`** :
- **`Studio`** : l'interface de génération directe par galerie et *Floating Prompt Dock* modulaire.
- **`Agents`** : le point de bascule vers l'interface dédiée aux agents autonomes (connectée après harmonisation de sa palette de couleurs).

---

## 2. Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MACHINE LOCALE (PC)                                   │
│                                                                                         │
│   ┌───────────────────────────────┐         ┌───────────────────────────────────────┐   │
│   │      Interface Web (UI)       │ <=====> │        Backend Local (FastAPI)        │   │
│   │                               │  HTTP   │                                       │   │
│   │  • Switch : [ Studio | Agents]│   SSE   │  • Gestionnaire d'état & configs      │   │
│   │  • 6 Pôles : Image, Video,    │         │  • Registre Modèles & LoRAs           │   │
│   │    Audio, Lip sync,           │         │  • Compilateur JSON -> ComfyUI API    │   │
│   │    Upscaling, 3D Gen          │         │  • Rapatriement auto des médias       │   │
│   │  • Pilule LoRA & Sélecteurs   │         │  • Persistance atomique JSON (data/)  │   │
│   └───────────────────────────────┘         └───┬───────────────┬───────────────┬───┘   │
└─────────────────────────────────────────────────┼───────────────┼───────────────┼───────┘
                                                  │               │               │
                       ┌──────────────────────────┘               │               └──────────────────────────┐
                       ▼                                          ▼                                          ▼
┌─────────────────────────────────────────────┐  ┌──────────────────────────────────────┐  ┌──────────────────────────────────┐
│     MOTEUR 1 : LOCAL (COMFYUI HEADLESS)     │  │     MOTEUR 2 : GOOGLE COLAB (GPU)    │  │       MOTEUR 3 : CLÉS API        │
│                                             │  │                                      │  │                                  │
│  • ComfyUI Headless API (127.0.0.1:8188)    │  │  • Serveur FastAPI distant (ngrok)   │  │  • Appels directs fournisseurs   │
│  • Mode hybride (rattaché ou lancé en fond) │  │  • Gestionnaire VRAM (Model Swapper) │  │    (Image, Vidéo, Audio,         │
│  • Exécution des workflows .api.json        │  │  • Pipelines Python Diffusers        │  │    Lip sync, Upscale, 3D)        │
│  • Injection dynamique des chaînes LoRA     │  │                                      │  │                                  │
└─────────────────────────────────────────────┘  └──────────────────────────────────────┘  └──────────────────────────────────┘
```

---

## 3. Spécifications de l'Interface Utilisateur (UI/UX)

### 3.1. Commutateur Global `[ Studio | Agents ]`
Placé dans la barre supérieure :
- **`Studio`** : affiche la grille de galerie et le *Floating Prompt Dock* à 6 onglets.
- **`Agents`** : bouton de bascule réservé à l'ouverture de l'espace Agents (aucun sous-écran intermédiaire n'est généré côté `Studio`).

### 3.2. Mode `Studio` : 6 Pôles de Création & Modularité par Schéma (`capabilities`)

L'interface repose sur une modularité stricte : **aucun écran ou page n'est codé en dur par modèle**. Chaque contrôle est une entité composant isolée (**un fichier par responsabilité**) qui ne s'affiche que si le modèle sélectionné déclare la capacité correspondante dans son schéma `capabilities`.

Le *Floating Prompt Dock* regroupe **6 onglets de catégorie** (l'ancien onglet `[ LLM ]` est retiré du Dock Studio) :
1. **`Image`** : génération d'images fixes, posters, cartes et visuels.
2. **`Video`** : génération vidéo (UGC, cinématique, tous formats réseaux sociaux).
3. **`Audio`** : modèles de voix (TTS / clonage), musique et effets sonores (SFX / Foley), incluant les modèles polyvalents (ex. *SeedAudio 1.0*) et les modèles spécialisés.
4. **`Lip sync`** : synchronisation labiale à partir d'un visage source et d'une piste vocale.
5. **`Upscaling`** : rehaussement de résolution image et vidéo jusqu'à 4K.
6. **`3D Gen`** : modèles de génération 3D (scène 3D par description, objet 3D depuis une image ou plusieurs angles, auto-rigging et animation 3D).

#### 3.2.1. Réutilisation de la Zone de Prompt et des Fentes de Référence (Zéro Composant Superflu)
- **Zone de Prompt Unique** :
  - Gère directement la description visuelle/sonore, le texte parlé (TTS), les paroles structurées (`[verse]`, `[chorus]`) et les balises d'expression (`[laugh]`, `[whisper]`) sans créer d'éditeur ou de champ de texte secondaire redondant.
- **Fentes de Référence Existantes & Validation Stricte des Fichiers** :
  - Les fentes du plateau supérieur (`Start frame`, `End frame`, `Image refs`, `Video refs`, `Audio refs`, ainsi que `Mesh ref` en 3D) sont réutilisées pour tous les pôles :
    - Une vidéo à bruiter en Audio/SFX (Video-to-Audio / Foley) se dépose directement dans `Video refs` (ingrédient vidéo).
    - Un échantillon vocal pour le clonage de voix se dépose dans `Audio refs` (ou dans la fente dédiée `Voice clone` si le modèle distingue un ingrédient musical d'une empreinte vocale).
    - Les vues d'un objet à convertir en 3D se déposent dans `Image refs` (1 image ou jusqu'à 4 angles `Front`/`Back`/`Left`/`Right` selon le modèle), et le maillage à rigger/animer dans `Mesh ref` (`.glb`, `.obj`, `.fbx`).
  - **Blocage des fichiers incompatibles (`acceptedInputTypes`)** : le système vérifie systématiquement les types d'entrées supportés par le modèle actif et **empêche le chargement de tout fichier incompatible** (ex. rejet immédiat du dépôt d'une image sur un modèle purement audio, ou d'un fichier audio sur un modèle 3D).

#### 3.2.2. Conditionnement Vidéo & Règle de Subsomption
1. **Mode Ingrédients (*Ingredient Mode* / `reference-to-video`)** : maintien de l'identité sémantique (Dataset Bible : personnages, décors, objets, effets, ou clip vidéo précédent $N-1$). Jusqu'à 9 références.
2. **Mode Temporel (*Frame Chaining*)** : première image (`Start frame` / `first-frame-to-video`) et/ou dernière image (`End frame` / `first-last-frame-to-video`).
* **Règle de subsomption obligatoire** : tout modèle supportant le mode complet (`Start frame` + `End frame` + `Ingrédients`) supporte obligatoirement l'ensemble des modes partiels et unitaires.

#### 3.2.3. Pilule Dédiée `[ LoRA ]` dans la Rangée Inférieure du Dock
- **Emplacement** : pilule dédiée dans la rangée du bas du Dock (à côté du modèle, du ratio et de la résolution), affichée dès que `capabilities.supportsLora === true`.
- **Filtrage par compatibilité** : le popover n'affiche **que les LoRAs compatibles avec le modèle actif** (`baseModel` : ex. uniquement les LoRAs `wan2.1` lorsque *Wan 2.1* est sélectionné).
- **Sélection 1-clic & Curseur dépliable** :
  - Un clic active ou désactive le LoRA avec son poids automatique par défaut (ex. `0.8`). Plusieurs LoRAs peuvent être activés simultanément.
  - Un petit curseur de poids discret ou dépliable (`0.1` à `1.5`) permet d'affiner la force uniquement si l'utilisateur souhaite la modifier.
- **Ajout / Import de LoRA** : permet d'enregistrer un LoRA avec une **image d'aperçu**, un **nom** et un **mot-clé déclencheur (`triggerWord`)** qui est injecté automatiquement dans le prompt lors de la génération.

#### 3.2.4. Pilules Dynamiques Spécifiques aux Onglets `[ Audio ]` et `[ 3D Gen ]`
Affichées uniquement lorsque le modèle sélectionné les déclare dans `capabilities` :
- **En mode `[ Audio ]`** :
  - **Sous-mode (`audioSubMode`)** : `[Voice | Music | SFX]` pour les modèles hybrides (ex. *SeedAudio 1.0*).
  - **Voix / Langue (`voicePreset`)** : sélecteur de voix intégrée (ex. *Kokoro-82M*, *Qwen2.5-Omni*).
  - **Mode Vocal (`vocalMode`)** : `[Vocal + Inst | Instrumental]` pour les modèles musicaux (*ACE-Step*, *DiffRhythm*, *YuE*).
  - **Vitesse / Expressivité (`speed` / `emotion`)** : vitesse d'élocution (`0.5x–2.0x`) ou intensité émotionnelle (*Chatterbox*, *CosyVoice 2*).
  - **Durée (`duration`)** et **Format de sortie (`outputFormat`)** : `.wav`, `.mp3`, `.flac`.
- **En mode `[ 3D Gen ]`** :
  - **Sous-mode 3D (`threeDSubMode`)** : `Scene 3D`, `Object 3D (Single/Multi-view)`, `Rig & Animate`.
  - **Résolution Géométrique (`octreeResolution`)** : `256`, `384`, `512` (*Hunyuan3D-2*, *TripoSG*, *Step1X-3D*).
  - **Polycount (`targetPolycount`)** : `10k`, `40k`, `100k`, `Raw`.
  - **Texture PBR (`pbrTexture`)** : commutateur `[PBR On | Off]` (génération des textures Albedo/Normal/Metallic/Roughness vs géométrie seule).
  - **Topologie (`remeshTopology`)** : `[Triangle | Quad]`.
  - **Options de Rigging & Animation (`skeletonTemplate` / `animationPreset`)** : type de squelette (`Auto`, `Humanoid`, `Quadruped`) et animation (`T-Pose`, `Idle`, `Walk`, `Run`, ou référence mouvement) lorsque un modèle de rig/animation (*UniRig*, *Puppeteer*, *Make-It-Animatable*) est sélectionné.
  - **Format 3D (`outputFormat`)** : `.glb`, `.fbx`, `.obj`, `.ply`.

---

## 4. Spécifications des 3 Moteurs d'Exécution (`Colab` | `Local` | `API`)

Le backend local FastAPI (< 80 Mo de RAM) route chaque requête vers le moteur actif sélectionné dans `data/config.json` (`executionMode: "colab" | "local" | "api"`).

### 4.1. Moteur `Colab` : Connexion Google OAuth, Orchestration 100 % Backend & Support Natif GPU (CUDA) + TPU (XLA/HBM)
Contrairement à une configuration manuelle par URL, le backend local orchestre intégralement la session Google Colab sur **GPU** comme sur **TPU** :
1. **Connexion au Compte Google & Orchestration Automatique (`ColabSessionOrchestrator`)** :
   - L'utilisateur se connecte à son compte Google via `POST /api/auth/google/login` depuis le popover `[👤]`.
   - Le backend récupère le profil Google (`email`, `avatarUrl`, abonnement `Free` / `Pro` / `Google AI Pro`), le solde de **Compute Units (CU)** et les accélérateurs éligibles sur le compte :
     - **GPU NVIDIA** : `T4` (16 Go), `L4` (24 Go), `A100` (40 Go / 80 Go).
     - **Google Cloud TPU** : `TPU v5e` (16 Go à 128 Go HBM), `TPU v6e` (Trillium), `TPU v2-8` (64 Go HBM).
   - Au démarrage d'une session Colab, `ColabSessionOrchestrator` alloue automatiquement le runtime GPU ou TPU choisi, démarre le démon worker et établit le canal chiffré machine-à-machine sans que l'utilisateur n'ouvre jamais Colab ni ne saisisse d'URL `ngrok`/`trycloudflare` ou de `worker_secret`.
2. **Détection Matérielle Réelle (`HardwareProfiler`) & Cache Mémoire Multi-Modèles LRU (`ModelSwapper` GPU/TPU)** :
   - Suppression totale de toute limite codée en dur à 16 Go (`16384.0` Mo) et de tout mode simulation factice.
   - Le worker détecte dynamiquement le backend matériel actif au démarrage et en temps réel :
     - **Mode GPU (`cuda`)** : interroge `torch.cuda.get_device_properties(0)` (`name`, `total_memory`) et `torch.cuda.mem_get_info()` (`free_bytes`, `total_bytes`).
     - **Mode TPU (`xla`)** : interroge `torch_xla.core.xla_model` (`xm.xla_device()`, `xm.get_memory_info(device)` pour lire `bytes_limit` et `bytes_used` de la mémoire HBM haute bande passante) et exécute les pipelines sur le périphérique XLA (`xm.mark_step()`).
   - Tant que la mémoire libre réelle (VRAM sur GPU ou HBM sur TPU) vérifie `free_mem >= model_required_mem + safety_margin_gb`, le `ModelSwapper` maintient **plusieurs pipelines simultanément en cache** (particulièrement avantageux sur L4 24 Go, A100 40/80 Go et TPU 64/128 Go HBM).
   - Lorsque la mémoire libre est insuffisante, il évince uniquement le(s) modèle(s) les moins récemment utilisés (**LRU**) : `del pipeline`, `gc.collect()`, suivi de `torch.cuda.empty_cache()` + `torch.cuda.ipc_collect()` sur GPU, ou `xm.mark_step()` + libération des tampons XLA sur TPU.
3. **Catalogue de Modèles Utilisateur Dynamique (`data/models.json`)** :
   - Le catalogue est stocké sur le PC local dans `data/models.json` et reste disponible à 100 % hors-ligne (aucune erreur `503` lorsque Colab est déconnecté).
   - L'utilisateur peut **ajouter ou supprimer** n'importe quel modèle (`POST /api/models`, `DELETE /api/models/{id}`) en spécifiant son `hfRepoId` (Hugging Face), une URL `.safetensors` ou un chemin Google Drive, avec estimation automatique de l'empreinte mémoire (`hf-mem`). Lors de l'inférence (`POST /infer`), le backend transmet la spécification du modèle au worker Colab qui le charge dynamiquement sur le GPU ou le TPU actif.

### 4.2. Moteur `Local` : Exécution sur PC via ComfyUI "Headless API"

Sur PC, ComfyUI est utilisé exclusivement comme **moteur d'exécution en arrière-plan** pour sa gestion optimisée de la VRAM, sans jamais afficher de graphe de nœuds à l'utilisateur.

#### 4.2.1. Gestion Hybride du Processus ComfyUI (`ComfyProcessManager`)
1. **Connexion à une instance existante** : le backend vérifie si `http://127.0.0.1:8188/system_stats` répond et s'y rattache immédiatement si ComfyUI tourne déjà.
2. **Lancement / Arrêt en tâche de fond** : si aucune instance n'est active, Omniforge peut lancer et arrêter lui-même le processus ComfyUI en arrière-plan à partir du chemin local configuré (`comfyRootPath`) avec l'option `--disable-auto-launch`.
3. **Purge VRAM (`POST /free`)** : permet de décharger les poids de la VRAM locale sur simple appel.

#### 4.2.2. Détection et Enregistrement Hybride des Modèles (`LocalModelRegistry`)
1. **Auto-détection des Modèles Connus** :
   - Omniforge embarque un catalogue de signatures pour les modèles connus (`data/known_models_catalog.json` : *Wan 2.1/2.2*, *Flux.1*, *SDXL*, *LTX-Video*, *CogVideoX*, *SeedAudio*, *CosyVoice 2*, *F5-TTS*, *ACE-Step*, *MMAudio*, *Hunyuan3D-2*, *TRELLIS*, *TripoSG*, *UniRig*, *Real-ESRGAN*, etc.).
   - En interrogeant `GET http://127.0.0.1:8188/object_info` et les dossiers de poids de ComfyUI, dès que les fichiers `.safetensors` requis d'un modèle connu sont présents, **le modèle s'active automatiquement** avec l'ensemble de ses `capabilities` et de ses workflows pré-câblés (`T2V`, `I2V`, `First+Last Frame`, `Reference/Ingredients`).
2. **Modale "Add / Map Model" pour les Modèles et Workflows Custom** :
   - Pour tout nouveau modèle ou workflow personnalisé, l'utilisateur importe un fichier `workflow_api.json` (exporté au format API depuis ComfyUI) dans la modale **Add / Map Model**.
   - Il renseigne le nom, la catégorie (`Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`), la famille de base (`baseModel` pour les LoRAs) et associe les entrées du Dock (`prompt`, `negativePrompt`, `seed`, `width`/`height`, `duration`/`frames`, `startFrame`, `endFrame`, `references`, `outputNode`) aux identifiants de nœuds du JSON. La configuration est enregistrée dans `data/custom_models.json`.

#### 4.2.3. Routage des Workflows ComfyUI derrière le JSON Simple de l'UI (`ComfyWorkflowCompiler`)
L'interface Web envoie toujours le même JSON simple à `POST /api/generate/media` :
```json
{
  "modelId": "wan-2.1",
  "mediaType": "video",
  "prompt": "Un plan cinématique...",
  "negativePrompt": "flou, basse qualité",
  "parameters": {
    "seed": 428910,
    "aspectRatio": "16:9",
    "resolution": "720p",
    "duration": "5s"
  },
  "references": {
    "startFrame": "data/assets/start.png",
    "endFrame": null,
    "imageRefs": [],
    "videoRefs": [],
    "audioRefs": [],
    "meshRef": null,
    "brandKitId": null
  },
  "loras": [
    { "id": "lora_cinematic_wan21", "weight": 0.8 }
  ]
}
```
Le `ComfyWorkflowCompiler` exécute alors 5 opérations transparentes :
1. **Sélection automatique du gabarit de workflow selon les références** :
   - Aucune référence visuelle $\rightarrow$ gabarit `text_to_video.api.json` (ou `text_to_image` / `text_to_audio` / `text_to_3d`).
   - `startFrame` seul $\rightarrow$ gabarit `first_frame_to_video.api.json`.
   - `endFrame` seul $\rightarrow$ gabarit `last_frame_to_video.api.json`.
   - `startFrame` + `endFrame` $\rightarrow$ gabarit `first_last_frame_to_video.api.json`.
   - `imageRefs` ou `videoRefs` (sans start/end) $\rightarrow$ gabarit `reference_to_video.api.json` (Mode Ingrédients).
   - `startFrame` (+ `endFrame`) + `imageRefs` $\rightarrow$ gabarit `hybrid_reference_flf.api.json`.
   - En 3D Gen : `single_image_to_3d.api.json`, `multiview_to_3d.api.json` (2 à 4 images dans `imageRefs`), ou `rig_animate_3d.api.json` (`meshRef` présent).
2. **Téléversement des médias** : envoi des fichiers de `references` à ComfyUI via `POST /upload/image` (ou dossier `input/`).
3. **Injection des paramètres et des *Trigger Words*** : écriture dans les nœuds cibles du `prompt` (auquel sont automatiquement ajoutés les `triggerWord` des LoRAs actifs), du `seed`, des dimensions `(width, height)` calculées depuis `(aspectRatio, resolution)`, et du nombre de frames calculé depuis `duration`.
4. **Chaînage dynamique des LoRAs** : pour chaque LoRA actif dans `loras[]`, insertion dynamique d'un nœud `LoraLoader` entre le chargeur du modèle et le sampler avec le poids choisi (`0.8` par défaut ou valeur affinée au curseur).
5. **Exécution, suivi WebSocket $\rightarrow$ SSE et rapatriement** : soumission à `POST /prompt`, conversion temps réel des événements WebSocket `/ws` de ComfyUI en flux SSE `/api/tasks/{task_id}/status`, annulation via `POST /interrupt`, et rapatriement du fichier généré (`GET /view`) vers le dossier local résolu via `MediaFileStore`.

### 4.3. Moteur `API` : Exécution Directe par Clés API
Lorsque `executionMode` vaut `"api"`, `WorkerGateway` appelle directement les endpoints HTTP des fournisseurs configurés par l'utilisateur dans `data/config.json` (sans passer par Colab ni ComfyUI), suit l'avancement de la tâche et rapatrie systématiquement le fichier final sur le disque local.

---

## 5. Architecture de Stockage Local & Base de Données JSON (`data/`)

Toutes les écritures JSON passent exclusivement par `JSONDocumentStore` (`asyncio.Lock` par fichier + écriture `.tmp` + `os.replace`) :

```
omniforge/
├── data/
│   ├── generations.json           # Journal de toutes les créations (inclut loras[] et 3D/Audio)
│   ├── brand_kits.json            # Profils de marque
│   ├── projects.json              # Collections et dossiers physiques isolés (storagePath)
│   ├── config.json                # Mode d'exécution (colab | local | api), chemins ComfyUI, clés API
│   ├── known_models_catalog.json  # Signatures et bindings des modèles connus pour ComfyUI
│   ├── custom_models.json         # Modèles et workflows ComfyUI ajoutés via "Add / Map Model"
│   ├── loras.json                 # Registre des LoRAs (nom, aperçu, baseModel, triggerWord, defaultWeight)
│   └── assets/                    # Actifs importés + miniatures de LoRAs
├── workflows/                     # Gabarits ComfyUI (.api.json) des modèles connus
└── outputs/                       # Fichiers générés (.png, .mp4, .wav, .mp3, .flac, .glb, .fbx, .obj)
    ├── YYYY-MM-DD/                # Partitionnement chronologique hors projet
    └── projects/<id>/             # Partitionnement par projet par défaut (si storagePath est null)
```

### 5.1. Schéma d'un LoRA dans `data/loras.json`
```json
[
  {
    "id": "lora_neon_cinema_wan21",
    "name": "Neon Cinema Lighting",
    "fileName": "wan21_neon_cinema_v2.safetensors",
    "baseModel": "wan2.1",
    "triggerWord": "neon_cinema_style",
    "defaultWeight": 0.8,
    "minWeight": 0.1,
    "maxWeight": 1.5,
    "thumbnailPath": "data/assets/loras/neon_cinema.jpg",
    "createdAt": "2026-10-25T04:00:00Z"
  }
]
```

### 5.2. Schéma d'un Modèle / Workflow dans `data/known_models_catalog.json` et `data/custom_models.json`
```json
[
  {
    "id": "wan-2.1-local",
    "name": "Wan 2.1",
    "type": "video",
    "baseModel": "wan2.1",
    "engine": "local",
    "requiredFiles": [
      { "folder": "diffusion_models", "pattern": "*wan2.1*t2v*.safetensors" },
      { "folder": "vae", "pattern": "*wan_2.1_vae*.safetensors" }
    ],
    "capabilities": {
      "acceptedInputTypes": ["image", "video"],
      "aspectRatios": ["16:9", "9:16", "1:1", "4:3", "21:9"],
      "resolutions": ["480p", "720p", "1080p"],
      "duration": { "type": "discrete", "values": ["5s", "10s"] },
      "supportsStartFrame": true,
      "supportsEndFrame": true,
      "supportsImageRefs": true,
      "maxImageRefs": 4,
      "supportsVideoRefs": true,
      "supportsLora": true,
      "supportsNegativePrompt": true,
      "supportsSeed": true
    },
    "topologies": {
      "t2v": {
        "workflowFile": "workflows/wan21/t2v.api.json",
        "bindings": {
          "prompt": "6.inputs.text",
          "negativePrompt": "7.inputs.text",
          "seed": "3.inputs.seed",
          "width": "5.inputs.width",
          "height": "5.inputs.height",
          "frames": "5.inputs.length",
          "modelOut": ["1", 0],
          "clipOut": ["2", 0],
          "samplerModelIn": "3.inputs.model",
          "positiveClipIn": "6.inputs.clip",
          "negativeClipIn": "7.inputs.clip",
          "outputNode": "8"
        }
      },
      "i2v_start": {
        "workflowFile": "workflows/wan21/i2v_start.api.json",
        "bindings": {
          "prompt": "6.inputs.text",
          "negativePrompt": "7.inputs.text",
          "startFrame": "10.inputs.image",
          "seed": "3.inputs.seed",
          "width": "5.inputs.width",
          "height": "5.inputs.height",
          "frames": "5.inputs.length",
          "outputNode": "8"
        }
      }
    }
  }
]
```

### 5.3. Schéma de `data/config.json`
```json
{
  "executionMode": "local",
  "colab": {
    "tunnelUrl": "https://xxxx-xx-xx.ngrok-free.app",
    "accountEmail": "user@gmail.com",
    "lastPing": null
  },
  "local": {
    "comfyUrl": "http://127.0.0.1:8188",
    "comfyRootPath": "C:/ComfyUI",
    "autoManageProcess": true
  },
  "api": {
    "providers": {
      "openai": { "apiKeyEnv": "OPENAI_API_KEY", "apiKey": null },
      "gemini": { "apiKeyEnv": "GEMINI_API_KEY", "apiKey": null },
      "fal": { "apiKeyEnv": "FAL_KEY", "apiKey": null }
    }
  },
  "compilerLlm": {
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "apiKeyEnv": "COMPILER_LLM_API_KEY",
    "apiKey": null
  },
  "defaultStoragePath": "outputs/"
}
```

---

## 6. Endpoints Locaux Principaux (FastAPI)

* `GET /api/health` : État du moteur actif (`colab`, `local` ComfyUI Headless ou `api`), latence et VRAM libre.
* `POST /api/config/execution-mode` : Bascule entre `"colab"`, `"local"` et `"api"` (refus `409 Conflict` si une tâche est en cours).
* `POST /api/local/comfy/start` & `POST /api/local/comfy/stop` : Lancement et arrêt du processus ComfyUI en arrière-plan.
* `GET /api/models` : Liste des modèles disponibles pour le moteur actif avec leurs `capabilities`.
* `POST /api/models/scan` : Scan de ComfyUI (`/object_info` et dossiers de poids) pour activer les modèles connus et détecter les LoRAs.
* `POST /api/models/custom` : Enregistrement d'un nouveau modèle/workflow via la modale *Add / Map Model*.
* `GET /api/loras` : Liste des LoRAs compatibles avec le `baseModel` demandé (`?baseModel=wan2.1`).
* `POST /api/loras` & `PATCH /api/loras/{id}` : Ajout/import ou modification d'un LoRA (nom, miniature, `baseModel`, `triggerWord`, `defaultWeight`).
* `POST /api/generate/media` : Lancement d'une génération (image, vidéo, audio, lip-sync, upscale, 3D) avec validation stricte des types de fichiers de référence et injection des `loras[]`.
* `GET /api/tasks/{task_id}/status` : Flux SSE de progression temps réel.
* `POST /api/tasks/{task_id}/cancel` : Annulation idempotente de la tâche en cours.
* `GET /api/generations`, `PATCH /api/generations/{id}/favorite`, `DELETE /api/generations/{id}`.
* `GET /api/brand-kits`, `POST /api/brand-kits`, `GET /api/projects`, `POST /api/projects`.
