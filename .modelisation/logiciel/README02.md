# Modélisation Logicielle UML 2.5 — Omniforge & Mini Design (Version 02 / v3)

Ce dossier documente l'architecture logicielle cible de la **Version 3 d'Omniforge**, concrétisant l'unification avec la station de conception **Mini Design** (`mini-design-monorepo`) sous un conteneur desktop unique Electron, selon les exigences normatives de l'**OMG UML 2.5.1** et les critères méthodologiques du **Dr. TRAORE (L3 MIAGE)**.

---

## 1. Référentiel Méthodologique & Matrice Complète des 14 Diagrammes UML 2.5.1

Conformément à la spécification officielle **OMG Unified Modeling Language (UML) version 2.5.1** (§ 6.8 - *UML Diagram Taxonomy*) et aux enseignements académiques du **Dr. TRAORE**, le métamodèle UML structure l'expression des systèmes selon deux grands axes orthogonaux : les **Diagrammes Structurels** (statiques) et les **Diagrammes Comportementaux** (dynamiques, dont les diagrammes d'interaction).

Dans le cadre du projet Omniforge v3, les 14 diagrammes canoniques de la norme ont été audités et classifiés selon leur apport opérationnel et leur pertinence architecturale :

### Tableau Matriciel Formel des 14 Diagrammes de la Norme OMG UML 2.5.1

| N° | Catégorie OMG | Nom Normatif du Diagramme | Statut dans la Modélisation v3 | Fichier Associé / Motif Formel d'Exclusion (Dr. TRAORE) |
| :-: | :--- | :--- | :---: | :--- |
| **1** | **Comportemental** | **Diagramme de Cas d'Utilisation** (*Use Case Diagram*) | **Reconduit par Héritage** | [`01-perimetre-fonctionnel.svg`](diagrammes/01-perimetre-fonctionnel.svg) : Définit les acteurs (Créateur, Designer IA, Colab Cloud) et les frontières du système unifié. |
| **2** | **Structurel** | **Diagramme de Composants** (*Component Diagram*) | **Mis à jour v3 (Remédié)** | [`02-composants02.svg`](diagrammes/02-composants02.svg) : Modélise les 5 sous-systèmes, connecteurs lollipop/socket, plugins MCP, contrats et sous-composants à granularité fine. |
| **3** | **Structurel** | **Diagramme de Déploiement** (*Deployment Diagram*) | **Mis à jour v3 (Remédié)** | [`03-deploiement02.svg`](diagrammes/03-deploiement02.svg) : Nœuds physiques axonométriques 3D, artefacts, protocoles réseau, PIDs réels et cartographie des ports. |
| **4** | **Structurel** | **Diagramme de Classes / Données** (*Class Diagram*) | **Reconduit par Héritage** | [`04-modele-de-donnees.svg`](diagrammes/04-modele-de-donnees.svg) : Schéma relationnel SQLite (46 tables) et modèles de documents JSON (`models.json`, `generations.json`). |
| **5** | **Comportemental** | **Diagramme d'Activités** (*Activity Diagram*) | **Mis à jour v3 (Remédié)** | [`05-activite-generation02.svg`](diagrammes/05-activite-generation02.svg) : 5 partitions d'activité, résolution complète du flux LLM (anti-trou noir), nœud de fusion «MergeNode», validation de contrats et ingrédients. |
| **6** | **Comportemental (Interaction)** | **Diagramme de Séquence** (*Sequence Diagram*) | **Mis à jour v3 (Remédié)** | [`06-sequence-inference02.svg`](diagrammes/06-sequence-inference02.svg) : Séquence d'inférence, fragment loop normé avec cartouche pentagonal, sens GET/SSE corrigé, sous-barres réflexives. |
| **7** | **Comportemental (Interaction)** | **Diagramme de Séquence (Brand Context)** | **Reconduit par Héritage** | [`07-sequence-brand-context.svg`](diagrammes/07-sequence-brand-context.svg) : Injection du contexte de marque et des profils colorimétriques dans les prompts de génération. |
| **8** | **Comportemental (Interaction)** | **Diagramme de Séquence (Proxy LLM)** | **Reconduit par Héritage** | [`08-sequence-proxy-llm.svg`](diagrammes/08-sequence-proxy-llm.svg) : Déroulement du relai standardisé `/v1/chat/completions` avec détection d'interruption (`AbortSignal`). |
| **9** | **Comportemental** | **Diagramme d'États-Transitions** (*State Machine*) | **Reconduit par Héritage** | [`09-etats-dock-adaptatif.svg`](diagrammes/09-etats-dock-adaptatif.svg) & [`10-etats-tache-media.svg`](diagrammes/10-etats-tache-media.svg) : Cycle de vie du dock multimodal et automate d'état des tâches asynchrones (`PENDING`, `RUNNING`, `DONE`). |
| **10** | **Structurel** | **Diagramme d'Objets** (*Object Diagram*) | **Exclu Formellement** | **Justification académique (Dr. TRAORE)** : Les instanciations dynamiques et configurations d'objets à l'exécution sont intégralement illustrées dans les diagrammes de séquence et d'états. Un diagramme d'objets statique figerait des topologies éphémères sans gain sémantique. |
| **11** | **Structurel** | **Diagramme de Structure Composite** (*Composite Structure*) | **Exclu Formellement** | **Justification académique (Dr. TRAORE)** : La décomposition interne des composants, leurs ports d'interaction et leurs connecteurs d'assemblage (lollipop / socket) sont déjà formalisés au plus haut niveau de rigueur dans le diagramme de composants v3 (§ 11.2 OMG). |
| **12** | **Structurel** | **Diagramme de Paquetages** (*Package Diagram*) | **Exclu Formellement** | **Justification académique (Dr. TRAORE)** : L'organisation logique des espaces de noms coïncide rigoureusement avec les frontières des 5 sous-systèmes du conteneur Electron et des packages du monorepo Mini Design. L'introduire séparément créerait une redondance purement descriptive. |
| **13** | **Comportemental (Interaction)** | **Diagramme de Communication** (*Communication Diagram*) | **Exclu Formellement** | **Justification académique (Dr. TRAORE)** : Isomorphe au diagramme de séquence sur le plan sémantique, mais dénué de la dimension temporelle explicite. Le diagramme de séquence est nettement supérieur pour exprimer le streaming SSE continu et les barres d'activation. |
| **14** | **Comportemental (Interaction)** | **Diagramme de Temps / Chronogramme** (*Timing Diagram*) & **Diagramme Global d'Interaction** (*Interaction Overview*) | **Exclus Formellement** | **Justification académique (Dr. TRAORE)** : Le système n'obéit pas à des contraintes de temps réel dur (hard real-time déterministe en nanosecondes) mais à une boucle d'événements asynchrone non-bloquante. Le séquencement global est parfaitement représenté par les fragments combinés (`loop`, `alt`) du diagramme de séquence. |

---

## 2. Synthèse Architecturale de la Version 3

L'intégration v3 concrétise la fusion technique des deux stations :
1. **Omniforge (`colab-ai-studio`)** :
   - Conteneur desktop Electron supervisant l'ensemble du cycle de vie des processus.
   - Barre de navigation supérieure unifiée (`TopNavBar & AppModeSwitch`) avec bascule instantanée sans rechargement `[ Studio | Agents ]`.
   - Dock flottant adaptatif de génération 6 pôles multimédias (Image, Vidéo, Audio, Lip-sync, Upscaling, 3D Mesh).
   - Gestionnaire d'adaptateurs LoRA (toggle 1-clic, curseurs repliables, chaînage ComfyUI).
   - Proxy LLM compatible OpenAI standardisé (`/v1/chat/completions`) servant de moteur conversationnel universel pour les agents.
   - Orchestration des workers distants sur Google Colab (GPU NVIDIA T4/L4/A100, TPU Google v5e/v6e via PyTorch & `torch_xla`) et locaux via ComfyUI Headless (`:8188`).
2. **Mini Design (`mini-design-monorepo`)** :
   - Station de conception visuelle avancée (`Workbench UI`).
   - Moteur graphique bi-mode de canevas infini : rendu matériel WebGPU 60 fps avec bascule automatique de sécurité en Canvas2D haute fidélité pour le CPU Intel i7 / GPU intégré HD Graphics 520.
   - Orchestration multi-agents autonomes Hilo (Leader, Planner, Coder, Stylist) dialoguant via le volet conversationnel.
   - Séquenceur temporel multipiste pour le montage vidéo et l'animation de calques.
   - Persistance relationnelle robuste sous SQLite (`.hilo/index.sqlite`, 46 tables, mode WAL).

### Tableau des Décisions Structurantes v3

| Axe Architectural | Décision de Conception Modélisée | Diagrammes de Référence |
| :--- | :--- | :--- |
| **1. Conteneur Desktop Unifié** | Electron 28+ encapsule l'ensemble du système dans une fenêtre native. Le composant `ElectronProcessOrchestrator` supervise le cycle de vie des deux backends locaux en sous-processus discrets. | [`02`](diagrammes/02-composants02.svg), [`03`](diagrammes/03-deploiement02.svg) |
| **2. Navigation & Commutateur `[ Studio \| Agents ]`** | Le composant `TopNavBar` expose un bouton segmenté natif :<br>• `Studio` : active la SPA réactive Omniforge (BrowserView 1).<br>• `Agents` : active instantanément le Workbench et le canevas infini de Mini Design (BrowserView 2) via permutation z-index sans rechargement ni perte d'état. | [`02`](diagrammes/02-composants02.svg), [`06`](diagrammes/06-sequence-inference02.svg) |
| **3. Coexistence Double-Backend Supervisée** | Maintien en parallèle de deux backends légers spécialisés :<br>• `FastAPI` (Python `:8000`) : inférence multimodale, Colab GPU/TPU, ComfyUI, proxy OpenAI standardisé.<br>• `Gateway NestJS` (Node.js `:51491`) : canevas, WorkspaceGuard, sessions, SQLite et MCP. | [`02`](diagrammes/02-composants02.svg), [`03`](diagrammes/03-deploiement02.svg) |
| **4. Délégation d'Inférence Découplée** | La Gateway NestJS remplace ses requêtes cloud MiniMax propriétaires par des appels locaux :<br>• LLM agents Hilo $\rightarrow$ `POST http://127.0.0.1:8000/v1/chat/completions` (streaming SSE).<br>• Génération média $\rightarrow$ `POST http://127.0.0.1:8000/api/generate/media`. | [`05`](diagrammes/05-activite-generation02.svg), [`06`](diagrammes/06-sequence-inference02.svg) |
| **5. Persistance Partagée & Enregistrement Atomique** | Tout média généré par Omniforge est déposé dans `outputs/` et immédiatement indexé dans la table `resource_v3` de la base `.hilo/index.sqlite` pour injection directe sur le canevas WebGPU. | [`02`](diagrammes/02-composants02.svg), [`05`](diagrammes/05-activite-generation02.svg) |

---

## 3. Cartographie Complète des Diagrammes Remédiés v3

### 3.1 Diagramme de Composants (`02-composants02.svg`)
- **Périmètre Logique** : Modélise l'architecture découpée en 5 sous-systèmes principaux et un écosystème d'extensions :
  1. **Conteneur Desktop Unifié (Electron 28+)** :
     - `ElectronProcessOrchestrator` : superviseur de processus, gestion du cycle de vie des backends (`spawn`, healthchecks, SIGTERM propre, redémarrage automatique en cas de crash).
     - `MultiViewWindowManager` : gestionnaire multi-vues (`BrowserView`), bascule instantanée sans latence ni fuite mémoire, isolation stricte du contexte.
     - `NativeIPCBridge` : pont bidirectionnel `contextBridge` exposant l'API sécurisée `window.electronAPI`.
  2. **Vue 1 : Omniforge Studio UI (React 18 / Vite 5)** :
     - `TopNavBar & AppModeSwitch` : commutateur segmenté, moniteur de statut moteur en temps réel.
     - `FloatingPromptDock` décomposé en 4 sous-composants : `TabSelector` (6 pôles), `IngredientSlots` (filtrage strict selon `capabilities.acceptedInputTypes`), `LoraPillControl & ParameterPills` (toggle 1-clic LoRA à poids 0.8, paramètres CFG/steps), `CanvasExportTrigger`.
     - `MediaGallery & AssetSynchronizer` décomposé en 4 sous-composants : `CardGrid` (7 types de cartes), `AudioWaveformPlayer` (visualiseur de spectre audio), `ThreeJsViewer` (visionneuse 3D orbitale WebGL pour `.glb` et `.obj`), `FolderWatcher` (synchronisation atomique).
  3. **Vue 2 : Mini Design Workbench UI (WebGPU / Canvas2D / Agents Hilo)** :
     - `CanvasAreaV3` décomposé en 4 sous-composants : `WebGPURenderer` (pipeline 60 fps), `Canvas2DFallback` (fallback sécurisé pour GPU intégré HD 520), `LayerHierarchy` (arbre hiérarchique de calques, blend modes), `TransformControls` (manipulateurs magnétiques et contraintes d'échelle/rotation).
     - `TimelineVideoEditor` : séquenceur multipiste, keyframes, transitions.
     - `HiloChatPanel` : interface de dialogue multi-agents (Leader, Planner, Coder), streaming SSE, déclenchement d'outils de canevas.
  4. **Backend Local FastAPI (:8000 · Python 3.10+)** :
     - `WorkerGateway & ColabOrchestrator` : routage tri-mode (Colab, ComfyUI, API), cycle asynchrone des tâches, tunnel public TLS distant.
     - `ComfyWorkflowCompiler & ModelSwapperLRU` : compilation des graphes `.api.json`, ordonnanceur de cache mémoire VRAM/HBM pour prévenir les erreurs de saturation mémoire (OOM).
     - `OpenAIProxy (/v1/chat/completions)` : proxy universel pour agents Hilo, streaming chunk SSE, gestion d'interruption `AbortSignal`.
     - `JSONStoreLock & MediaFileStore64k` : écritures atomiques sécurisées par `asyncio.Lock`, streaming binaire par fragments de 64 Ko vers `outputs/`.
  5. **Gateway NestJS (:51491 · Node.js)** :
     - `WorkspaceGuard & TokenValidator` : sécurisation des mutations de documents via validation du jeton local `mini-design-local-token`.
     - `OmniforgeInferenceDelegatorAdapter` : traducteur de contrats pour aiguiller les générations vers FastAPI (:8000).
     - `SQLiteRepository & ContractEngine` : persistance sous `.hilo/index.sqlite` (46 tables, migrations 0001 à 0019), validation des contrats `canvas-discipline` et `anti-loop guard`.
     - `MCPToolsRegistry & OpenCodePluginHost` : hébergement des plugins et outils d'extension (`mcp-tools-v3`, `bundled-plugins`, `clip-studio-export`).
- **Conformité Normative OMG UML 2.5.1 (§ 11.2)** :
  - **Correction de la polarité lollipop/socket** : `FastAPI` (:8000) **FOURNIT** l'interface `IInferenceService` (cercle plein/sucette à $x=1055$), et `NestJS` (:51491) **REQUIERT** cette interface (socket/demi-cercle concave ouvert vers la gauche englobant la boule).
  - Nouveaux connecteurs formels : `IStudioAPI` (REST/SSE :8000) reliant la Studio UI (socket) à FastAPI (lollipop), et `IWorkspaceProtocol` (REST :8001 / WS) reliant le Workbench UI (socket) à la Gateway NestJS (lollipop).

### 3.2 Diagramme de Déploiement (`03-deploiement02.svg`)
- **Périmètre Topologique** :
  - Nœud matériel hôte `«device» Poste de Travail Utilisateur` (Windows 11 Pro, Intel Core i7-6600U, 16 Go RAM).
  - Nœud matériel distant `«device» Worker Distant Google Colab` (VM Linux Cloud, GPU NVIDIA T4/L4/A100 ou TPU Google v5e/v6e).
- **Conformité Normative OMG UML 2.5.1 (§ 19.2)** :
  - **Représentation 3D en perspective axonométrique** : Les deux nœuds matériels physiques sont modélisés sous forme de parallélépipèdes 3D conformes à la norme avec faces supérieure et latérale en polygones ombrés.
  - **Liaison de communication continue** : Le lien réseau HTTPS/WSS distant entre FastAPI et le Worker Colab est tracé en **ligne continue pleine** stéréotypée `«communicationPath»` (OMG § 19.2.4), éliminant les pointillés non réglementaires.
  - **Environnement de stockage requalifié** : L'environnement de persistance passif est requalifié formellement en `«executionEnvironment» SQLite Embedded Engine & OS Storage`.
  - **Identification précise des processus et empreintes mémoires réelles** :
    * Electron Main Process : PID 14208, ~60 Mo RAM.
    * Vue Studio (BrowserView 1) : PID 18920, ~45 Mo RAM.
    * Vue Agents (BrowserView 2) : PID 19452, ~120 Mo RAM.
    * FastAPI Local Backend : PID 22104, ~75 Mo RAM.
    * Gateway NestJS : PID 24316, ~95 Mo RAM.
    * ComfyUI Headless Local : PID 28540, ~140 Mo RAM (base sans modèle lourd en RAM).
    * Colab Remote Server : PID 1142, allocation VRAM 16/24/40 Go déportée sans impact sur l'hôte.
    * **Bilan global hôte** : $\approx 395\text{ Mo}$ de RAM au repos, strictement inférieur au plafond de sécurité de $450\text{ Mo}$.

### 3.3 Diagramme d'Activités (`05-activite-generation02.svg`)
- **Périmètre Opérationnel** : Orchestration complète d'un prompt utilisateur depuis le mode `[Agents]`.
- **Conformité Normative OMG UML 2.5.1 (§ 15.3)** :
  - **Levée du trou noir critique du flux LLM** : L'action 5A (`Appeler /v1/chat/completions`) est désormais reliée par une arête de flux continue vers l'action `Streaming tokens vers chat Hilo` sur la partition du Workbench, laquelle converge ensuite vers le nœud de fusion terminal avant le nœud final d'activité (`ActivityFinalNode`).
  - **Insertion du nœud de fusion «MergeNode»** : Un losange formel `«MergeNode»` est inséré à la convergence des branches d'exécution GPU (Colab GPU et ComfyUI local) avant d'attaquer l'action de rapatriement binaire (Action 6).
  - **Sous-actions de contrôle et validation intégrées** :
    * `TokenValidator` : vérification du jeton local `mini-design-local-token`.
    * `ContractEngine` : vérification formelle de la discipline de calques (`canvas-discipline`) et garde anti-bouclage (`anti-loop`).
    * `Valider Ingrédients` : validation stricte des entrées selon `capabilities.acceptedInputTypes` (prompt, image initiale, masque, audio).
    * `Insertion Atomique dans resource_v3` : transaction SQLite avec rollback automatique en cas d'erreur disque.

### 3.4 Diagramme de Séquence (`06-sequence-inference02.svg`)
- **Périmètre Temporel** : Chronologie détaillée des interactions et synchronisations multi-processus.
- **Conformité Normative OMG UML 2.5.1 (§ 17.6 & § 17.8)** :
  - **Correction du sens de la requête de polling/progression** : Le message 10 `GET /api/tasks/{task_id}/status` est dirigé du client demandeur (`NestJSGateway`, $x=1162$) vers le serveur fournisseur (`FastAPI Backend`, $x=1513$), suivi du message SSE poussé `10b: event: task_progress(45%)` en retour de FastAPI vers NestJS.
  - **Fragment combiné loop normé** : Le fragment de streaming des tokens SSE est délimité par un rectangle extérieur en trait continu plein, surmonté à gauche de son cartouche pentagonal officiel `loop [Tokens en streaming SSE]`.
  - **Barre d'activation ajoutée sur le Workbench** : Ajout d'une `ExecutionSpecification` sur la ligne de vie `MiniDesignWorkbench` lors de la réception du message 2 `attachBrowserView(MiniDesignView)`.
  - **Sous-barres réflexives imbriquées** : Matérialisation de sous-barres d'activation décalées lors des auto-appels internes (transaction SQLite sur la Gateway et rendu WebGPU/Canvas2D sur le Workbench).
  - **Réception formalisée sur l'Utilisateur** : Ouverture d'une barre d'activation sur la ligne de vie Utilisateur lors de la notification visuelle finale (message 14).

---

## 4. Nomenclature Formelle et Cartographie des Ports Réseau

Tous les composants de la Version 3 communiquent via des canaux réseau strictement isolés et déterministes sur l'interface locale de bouclage (`127.0.0.1`) ou via des tunnels chiffrés :

| Port Réseau | Protocole / Transport | Composant Source | Composant Cible | Rôle & Nature du Trafic |
| :---: | :---: | :--- | :--- | :--- |
| **`:5173`** | HTTP / WS (Vite HMR) | Navigateur / BrowserView 1 | SPA React Omniforge | Interface utilisateur du Studio Omniforge (dock 6 pôles, LoRA, galerie). |
| **`:8000`** | HTTP / SSE / REST | BrowserView 1 & NestJS Gateway | FastAPI Local Backend | API unifiée d'inférence multimodale, proxy standardisé `/v1/chat/completions` et flux SSE `/api/tasks/{task_id}/status`. |
| **`:8001`** | HTTP (Static Serve) | Navigateur / BrowserView 2 | Mini Design Workbench | Distribution des bundles désobfusqués et assets de la station Mini Design. |
| **`:8002`** | HTTP / WS | Mini Design Workbench | Mini Design Local Service | Communication interne entre le Workbench et le gestionnaire de workspace local. |
| **`:51491`** | HTTP / JSON-RPC / IPC | Workbench UI & Electron Main | Gateway NestJS Mini Design | Runtime des agents Hilo, supervision SQLite, middleware `WorkspaceGuard`, moteur de contrats et outils MCP. |
| **`:45899`** | HTTP / Local Auth | Electron Main & Scripts | NestJS Local Auth Server | Serveur de synchronisation, injection des configurations et validation du jeton `mini-design-local-token`. |
| **`:8188`** | HTTP / WebSocket | FastAPI Backend Local | ComfyUI Headless | Moteur d'inférence local optionnel (exécution de graphes compilés `.api.json` et chargement de LoRAs). |
| **Distant :8000** | HTTPS / WSS (Tunnel TLS) | FastAPI Backend Local | Worker Colab Distant | Acheminement sécurisé des prompts et rapatriement des binaires lourds (GPU T4/A100 ou TPU Google v5e/v6e). |

---

## 5. Synthèse des Éléments d'Extensibilité : Skills, MCP & Plugins

L'architecture v3 est conçue pour accueillir de nouveaux outils sans altérer le cœur d'exécution :
1. **Outils MCP (`mcp-tools-v3`)** :
   - Exécutés sous le contrôle du `MCPToolsRegistry` au sein de la Gateway NestJS.
   - Permettent aux agents Hilo de manipuler directement l'arbre des calques, d'ajuster les transformations vectorielles et de déclencher des opérations de rendu.
2. **Plugins Pré-packagés (`bundled-plugins`)** :
   - Hébergés dans l'`OpenCodePluginHost`.
   - Fournissent des fonctionnalités de palettes chromatiques harmonisées, de métriques de lisibilité et de validation stylistique.
3. **Passerelles d'Export Métier (`clip-studio-export`)** :
   - Assurent l'interopérabilité avec les logiciels de création professionnels tiers (Clip Studio Paint, Photoshop) en sérialisant calques raster, masques et métadonnées vectorielles.
