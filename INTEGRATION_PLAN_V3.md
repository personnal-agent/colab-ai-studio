# Plan d'Intégration & Feuille de Route d'Ingénierie — Omniforge v3 (Mini Design Hybrid Studio)

Ce document formalise la feuille de route technique, la cartographie réseau déterministe et la stratégie d'implémentation pour unifier **Omniforge** (`colab-ai-studio`) et **Mini Design** (`mini-design-monorepo`) au sein d'une application desktop unifiée et autonome sous Electron 28+.

---

## 1. Synthèse Architecturale & Faisabilité

### 1.1 Verdict de Faisabilité : **OUI, 100 % FAISABLE**
L'intégration totale des deux environnements est non seulement possible, mais crée une synergie technique optimale :
1. **Mini Design** apporte la station de travail de conception de pointe : canevas infini WebGPU/2D, orchestrateur multi-agents Hilo (Leader, Planner, Coder), gestion de projet par base locale SQLite (`.hilo/index.sqlite` 46 tables), éditeur de timeline vidéo et protocoles de composition visuelle.
2. **Omniforge** apporte le moteur d'exécution et d'inférence multimédia haute performance : passerelle de génération 6 pôles (Image, Vidéo, Audio, Lip-sync, Upscaling, 3D Mesh), orchestration automatique de sessions GPU/TPU distantes sur Google Colab (sans clé payante), contrôle local ComfyUI Headless (`:8188`), gestion des adaptateurs LoRA (toggle 1-clic, curseurs repliables) et proxy LLM OpenAI standardisé (`/v1/chat/completions`).

### 1.2 Topologie d'Exécution Cible & Cartographie des Ports

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            CONTENEUR DESKTOP ELECTRON UNIFIÉ (HÔTE PC)                           │
│                                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                    TopNavBar Globale & Commutateur de Mode Réactif                         │  │
│  │                              AppModeSwitch [ Studio | Agents ]                             │  │
│  └──────────────────────────────────────────────┬─────────────────────────────────────────────┘  │
│                                                 │                                                │
│                 ┌───────────────────────────────┴───────────────────────────────┐                 │
│                 ▼ (Mode Studio)                                                 ▼ (Mode Agents)  │
│  ┌──────────────────────────────────────────┐    ┌────────────────────────────────────────────┐  │
│  │       Vue Studio (Port :5173)            │    │       Vue Agents (Port :8001 / :8002)      │  │
│  │  • FloatingPromptDock (6 pôles)          │    │  • CanvasAreaV3 (WebGPU / Canvas2D)        │  │
│  │    - TabSelector & IngredientSlots       │    │    - LayerHierarchy & TransformControls    │  │
│  │    - LoraPillControl & ParameterPills    │    │  • TimelineVideoEditor (Keyframes/Tracks)  │  │
│  │  • MediaGallery & Visualiseurs           │    │  • HiloChatPanel (Dialogue Multi-Agents)   │  │
│  │    - CardGrid, AudioWaveform, ThreeJs    │    │  • OpenCode Agent Workspace UI             │  │
│  └────────────────────┬─────────────────────┘    └─────────────────────┬──────────────────────┘  │
│                       │                                                │                         │
│                       │ IStudioAPI (REST/SSE :8000)                    │ IWorkspaceProtocol      │
│                       ▼                                                ▼ (REST :8001 / WS :51491)│
│  ┌──────────────────────────────────────────┐         HTTP/SSE         ┌────────────────────────────┐  │
│  │      Backend FastAPI (:8000)             │◄─────────────────────────┤   Gateway NestJS (:51491)  │  │
│  │  • WorkerGateway & ColabOrchestrator     │   IInferenceService      │ • WorkspaceGuard & Auth    │  │
│  │  • ComfyWorkflowCompiler & LoRA loaders  │   (Délégation LLM &      │   TokenValidator (:45899)  │  │
│  │  • ModelSwapperLRU (Cache VRAM/HBM)      │    Médias 6 Pôles)       │ • SQLiteRepository (46 tab)│  │
│  │  • OpenAIProxy (/v1/chat/completions)    │                          │ • ContractEngine (canvas-  │  │
│  │  • JSONStoreLock & MediaFileStore64k     │                          │   discipline, anti-loop)   │  │
│  └────────────────────┬─────────────────────┘                          │ • MCPToolsRegistry & Host  │  │
│                       │                                                │   - mcp-tools-v3           │  │
│                       │                                                │   - bundled-plugins        │  │
│                       │                                                │   - clip-studio-export     │  │
│                       │                                                └────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────────────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼ «communicationPath»         ▼ «communicationPath»
┌─────────────────────────────────┐ ┌─────────────────────────────────┐
│ Worker Distant Google Colab VM  │ │ Moteur Local ComfyUI API        │
│ • PyTorch 2.4 / Torch-XLA       │ │ • Port Local :8188              │
│ • GPU T4 / L4 / A100            │ │ • Exécution silencieuse headless│
│ • TPU Google v5e / v6e          │ │ • Compilation .api.json         │
│ • Tunnel TLS Public Automatique │ │ • Chaînage de LoRA Loaders      │
└─────────────────────────────────┘ └─────────────────────────────────┘
```

---

## 2. Nomenclature Formelle des Ports Réseau & Contrats d'Échange

| Port Réseau | Transport / Protocole | Composant Source | Composant Destination | Description du Service & Contrat d'Interface |
| :---: | :---: | :--- | :--- | :--- |
| **`:5173`** | HTTP / WS (Vite HMR) | BrowserView 1 | SPA React Omniforge | Dev Server Vite distribuant la SPA Studio (React 18, Tailwind v3). |
| **`:8000`** | HTTP / REST / SSE | BrowserView 1 & NestJS Gateway | Backend Local FastAPI | Point d'entrée unique d'inférence multimodale, proxy standardisé `/v1/chat/completions` et flux SSE `/api/tasks/{task_id}/status`. |
| **`:8001`** | HTTP (Serveur Statique) | BrowserView 2 | Mini Design Workbench | Distribution des bundles désobfusqués et composants du canevas infini. |
| **`:8002`** | HTTP / WebSocket | Mini Design Workbench | Mini Design Local Service | Communication synchrone du Workbench avec les services de documents locaux. |
| **`:51491`** | HTTP / IPC / JSON-RPC | Workbench & Electron Main | Gateway NestJS Mini Design | Runtime des agents Hilo, supervision SQLite, middleware `WorkspaceGuard`, moteur de contrats et outils MCP. |
| **`:45899`** | HTTP / Auth Sécurisée | Electron Main & Scripts | Serveur d'Authentification NestJS | Validation du jeton `mini-design-local-token` et distribution des variables d'environnement. |
| **`:8188`** | HTTP / WebSocket | FastAPI Backend Local | ComfyUI Headless Local | Moteur local optionnel pour génération sur GPU physique disponible. |
| **Distant :8000** | HTTPS / WSS (Tunnel TLS) | FastAPI Backend Local | Worker Distant Colab | Acheminement chiffré des prompts et streaming des artefacts binaires lourds. |

---

## 3. Feuille de Route en 5 Phases d'Ingénierie Détaillée

### Phase 1 : Packaging Electron & Superviseur de Processus (`ElectronProcessOrchestrator`)
- **Objectif** : Transformer `colab-ai-studio` en conteneur desktop Electron supervisant les sous-processus locaux sans collision ni processus orphelins.
- **Tâches d'ingénierie** :
  1. Initialisation d'Electron 28+ dans la racine du projet avec support TypeScript strict.
  2. Implémentation de `electron/main.ts` :
     - `child_process.spawn('uvicorn', ['app.main:app', '--port', '8000', '--host', '127.0.0.1'])`.
     - `child_process.spawn('node', ['mini-design-src/packages/gateway/dist/main.js'], { env: { PORT: '51491', AUTH_PORT: '45899' } })`.
  3. Mise en place de sondes de santé HTTP synchronisées (`GET http://127.0.0.1:8000/health` et `GET http://127.0.0.1:51491/api/health`).
  4. Gestion sécurisée du cycle de vie : interception de `window-all-closed` et émission de signaux `SIGTERM` / `SIGKILL` avec purge des PIDs enfants.
- **Critère de validation (DoD)** :
  - Lancement via `npm run electron:dev`.
  - Les ports `:8000`, `:51491` et `:45899` répondent avec statut 200 en moins de 5 secondes.
  - Fermeture de la fenêtre principale : zéro processus Node.js ou Python subsistant dans le gestionnaire des tâches.

---

### Phase 2 : Interface Unifiée Multi-Vues & Commutateur `[ Studio | Agents ]`
- **Objectif** : Faire coexister les 1,3M de lignes désobfusquées de Mini Design et la SPA Omniforge dans la même fenêtre native avec 0ms de latence de bascule.
- **Tâches d'ingénierie** :
  1. Configuration du `MultiViewWindowManager` avec deux instances `BrowserView` :
     - `viewStudio` : attachée à `http://127.0.0.1:5173`.
     - `viewAgents` : attachée à `http://127.0.0.1:8001`.
  2. Intégration du composant `AppModeSwitch` dans la `TopNavBar` Omniforge.
  3. Routage IPC bidirectionnel via `NativeIPCBridge` :
     - Envoi de l'événement `'switch-mode'` avec payload `{ mode: 'Studio' | 'Agents' }`.
     - Permutation atomique des vues via `win.setTopBrowserView()`.
  4. Isolation stricte des contextes (`contextIsolation: true`, `sandbox: false` contrôlé).
- **Critère de validation (DoD)** :
  - Bascule instantanée entre Studio et Agents en moins de 16 ms (1 frame à 60 fps).
  - Aucune fuite de mémoire après 100 permutations consécutives (profiling Chromium).

---

### Phase 3 : Passerelle d'Inférence, Proxy LLM & Streaming SSE
- **Objectif** : Découpler Mini Design des services cloud fermés payants (MiniMax) et raccorder l'ensemble des agents au moteur d'inférence unifié d'Omniforge.
- **Tâches d'ingénierie** :
  1. Redirection du client LLM Mini Design (`packages/gateway/src/llm/`) :
     - Base URL fixée sur `http://127.0.0.1:8000/v1`.
     - Utilisation de `OpenAIProxy` (`/v1/chat/completions`) avec relai SSE en streaming continu.
     - Gestion des interruptions de streaming via `AbortSignal`.
  2. Implémentation de l'`OmniforgeInferenceDelegatorAdapter` dans NestJS :
     - Traduction de la requête de conception en tâche multimédia `POST http://127.0.0.1:8000/api/generate/media`.
     - Écoute du bus d'événements `/api/tasks/{task_id}/status` pour relayer la progression (pourcentage, étape de meshing/sampling) vers la barre d'état du canevas.
  3. Validation des contraintes de contrats :
     - Vérification de `canvas-discipline` et `anti-loop guard` par le `ContractEngine`.
     - Vérification des ingrédients d'entrée selon `capabilities.acceptedInputTypes`.
- **Critère de validation (DoD)** :
  - Une invite textuelle dans le chat Hilo déclenche l'inférence via FastAPI `:8000`.
  - Les tokens sont affichés en direct dans l'interface sans saccade.
  - La génération d'un maillage 3D produit un `.glb` stocké et injecté sur le canevas.

---

### Phase 4 : Persistance Partagée, Transaction SQLite & Synchronisation des Fichiers
- **Objectif** : Assurer l'accès partagé et cohérent aux assets entre Omniforge et Mini Design.
- **Tâches d'ingénierie** :
  1. Unification des répertoires de sortie :
     - Streaming des binaires par fragments de 64 Ko via `MediaFileStore64k` vers `outputs/` et `.hilo/resources/`.
     - Verrouillage des écritures JSON sur `data/*.json` via `JSONStoreLock` (`asyncio.Lock`).
  2. Enregistrement transactionnel SQLite :
     - `SQLiteRepository` exécute l'insertion atomique dans la table `resource_v3` (.hilo/index.sqlite, 46 tables) lors de chaque fin de tâche réussie.
     - Rollback automatique en cas d'échec d'écriture disque.
  3. Intégration du bouton "Injecter dans le Canevas" sur les cartes de la `MediaGallery`.
- **Critère de validation (DoD)** :
  - Tout média créé dans le Studio apparaît instantanément dans la palette d'assets du Workbench.
  - Zéro corruption de fichier ou blocage de base SQLite (`database is locked`) sous concurrence.

---

### Phase 5 : Durcissement Matériel Hôte, Fallback WebGPU & Validation End-to-End
- **Objectif** : Garantir des performances optimales sur la configuration cible de l'utilisateur (Intel Core i7-6600U @ 2.60GHz, 16 Go RAM, GPU Intel HD Graphics 520).
- **Tâches d'ingénierie** :
  1. Profilage de l'empreinte mémoire totale hôte :
     - Electron Main (~60 Mo) + Studio View (~45 Mo) + Agents View (~120 Mo) + FastAPI (~75 Mo) + NestJS (~95 Mo) = ~395 Mo RAM.
     - Vérification stricte du plafond : l'ensemble reste sous la barre des 450 Mo RAM au repos.
  2. Validation du fallback WebGPU :
     - Détection des capacités graphiques au montage du canevas.
     - Bascule automatique vers le moteur `Canvas2DFallback` si WebGPU n'est pas supporté par le pilote Intel HD Graphics 520, préservant 60 fps sur le manipulateur de calques.
  3. Déport systématique des calculs lourds :
     - Modèles de diffusion vidéo et 3D strictement exécutés sur Google Colab ou ComfyUI Headless, interdisant tout chargement local saturant les cœurs CPU i7.
- **Critère de validation (DoD)** :
  - Parcours complet d'une session de création (Prompt Studio $\rightarrow$ LoRA $\rightarrow$ Génération Colab $\rightarrow$ Bascule Agents $\rightarrow$ Rendu Canevas) avec fluidité constante et température CPU maîtrisée.

---

## 4. Matrice de Gestion des Risques & Atténuations

| Risque Identifié | Impact | Probabilité | Stratégie d'Atténuation Validée |
| :--- | :---: | :---: | :--- |
| **Incompatibilité build Vite sur les 1,3M lignes Mini Design** | Critique | Haute | **Architecture Electron Multi-View (BrowserView)** : le runtime pré-packagé s'exécute dans son environnement naturel sans tentative de re-bundle destructif. |
| **Collision de ports réseau locaux** | Modéré | Faible | Détection dynamique de disponibilité au boot d'Electron avec attribution de secours et injection d'environnement. |
| **Saturation mémoire RAM sur l'hôte (16 Go)** | Élevé | Moyenne | Déport obligatoire de l'inférence lourde sur Colab Cloud (GPU T4/A100) ; FastAPI reste bridé à moins de 80 Mo de RAM. |
| **Conflits d'accès concurrent à SQLite** | Faible | Faible | Mode WAL (*Write-Ahead Logging*) activé sur `.hilo/index.sqlite` ; la Gateway NestJS centralise l'accès en écriture exclusive. |
| **Crash pilote WebGPU sur GPU Intel HD 520** | Modéré | Moyenne | Maintien du composant `Canvas2DFallback` avec détection automatique du contexte `navigator.gpu`. |

---

## 5. Livrables et Diagrammes Associés

1. **Feuille de Route d'Ingénierie** : Ce document (`INTEGRATION_PLAN_V3.md`).
2. **Dossier de Modélisation UML 2.5.1 v3** : `.modelisation/logiciel/README02.md`.
3. **Diagrammes Vectoriels Pure SVG v3 Remédiés** :
   - [`02-composants02.svg`](.modelisation/logiciel/diagrammes/02-composants02.svg) : Architecture des composants, polarité sucette/douille corrigée, connecteurs front/back et sous-composants détaillés.
   - [`03-deploiement02.svg`](.modelisation/logiciel/diagrammes/03-deploiement02.svg) : Déploiement physique axonométrique 3D, ligne continue `«communicationPath»`, PIDs et ports.
   - [`05-activite-generation02.svg`](.modelisation/logiciel/diagrammes/05-activite-generation02.svg) : Flux d'activité avec résolution du flux LLM (anti-trou noir), nœud de fusion «MergeNode» et validation des ingrédients.
   - [`06-sequence-inference02.svg`](.modelisation/logiciel/diagrammes/06-sequence-inference02.svg) : Séquence d'inférence, fragment loop normé avec cartouche pentagonal, sens requête GET/SSE corrigé et sous-barres réflexives.
