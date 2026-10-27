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
│                       ▼                                                ▼ (HTTP/JSON-RPC :51491)│
│  ┌──────────────────────────────────────────┐         HTTP/SSE         ┌────────────────────────────┐  │
│  │      Backend FastAPI (:8000)             │◄─────────────────────────┤   Gateway NestJS (:51491)  │  │
│  │  • WorkerGateway & ColabOrchestrator     │   IInferenceService      │ • WorkspaceGuard / Validator    │  │
│  │  • ComfyWorkflowCompiler & LoRA loaders  │   (Délégation LLM &      │   Client Auth séparé :45899  │  │
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
| **`:51491`** | HTTP / JSON-RPC | Workbench & Electron Main | Gateway NestJS Mini Design | Runtime des agents Hilo, supervision SQLite, middleware `WorkspaceGuard`, moteur de contrats et outils MCP. |
| **`:45899`** | HTTP / Auth Sécurisée | Electron Main & Scripts | Auth NestJS, processus séparé supervisé par Electron | Validation du jeton `mini-design-local-token` et distribution des variables d'environnement. |
| **`:8188`** | HTTP / WebSocket | FastAPI Backend Local | ComfyUI Headless Local | Moteur local optionnel pour génération sur GPU physique disponible. |
| **Distant :8000** | HTTPS / WSS (Tunnel TLS) | FastAPI Backend Local | Worker Distant Colab | Acheminement chiffré des prompts et streaming des artefacts binaires lourds. |

---

**Endpoint canonique cible `IWorkspaceProtocol`** : `http://127.0.0.1:51491` (HTTP/JSON-RPC de la Gateway). Le port `8001` sert uniquement les fichiers du Workbench ; `8002` appartient au service de documents locaux. Aucun WebSocket Gateway n'est supposé disponible sans contrat explicite. L'IPC Electron est un transport de processus distinct, sans port HTTP. Ces interfaces Mini Design sont à vérifier lors de l'intégration.

**Propriété des processus cible** : Auth est un processus NestJS distinct de la Gateway, démarré et arrêté par `ElectronProcessOrchestrator`. Le `TokenValidator` de la Gateway est un client de ce service, pas son serveur. Le Local Service est également un enfant obligatoire d’Electron pour le workspace ; ni Auth ni Local Service ne sont supposés démarrés implicitement par la Gateway. Les points d’entrée Mini Design doivent être résolus depuis ses manifestes et vérifiés avant intégration ; ce dépôt ne fournit pas encore ces exécutables.

**Configuration d'exécution commune cible** : Electron construit un objet `runtimeEndpoints` unique, contenant les URL effectives de Studio, FastAPI, Workbench, Local Service, Gateway et Auth, après réservation des ports. Les valeurs du tableau sont des défauts. Après un repli, cet objet est transmis aux processus (configuration de démarrage) et aux BrowserViews (pont IPC limité aux URL publiques locales). Les sondes et tous les clients HTTP/LLM FastAPI lisent les mêmes URL ; les exemples à ports fixes ci-dessous désignent les valeurs par défaut.

## 3. Feuille de Route en 5 Phases d'Ingénierie Détaillée

### Phase 1 : Packaging Electron & Superviseur de Processus (`ElectronProcessOrchestrator`)
- **Objectif** : Transformer `colab-ai-studio` en conteneur desktop Electron supervisant les sous-processus locaux sans collision ni processus orphelins.
- **Tâches d'ingénierie** :
  1. Initialisation d'Electron 28+ dans la racine du projet avec support TypeScript strict.
  2. Implémentation de `electron/main.ts` :
     - `child_process.spawn('uvicorn', ['app.main:app', '--port', new URL(runtimeEndpoints.fastapi).port, '--host', '127.0.0.1'])`.
     - `child_process.spawn('node', ['mini-design-src/packages/gateway/dist/main.js'], { env: { ...process.env, PORT: new URL(runtimeEndpoints.gateway).port, AUTH_URL: runtimeEndpoints.auth } })`.
     - Résoudre `authEntryPoint` et `localServiceEntryPoint` depuis les manifestes Mini Design, puis démarrer explicitement `child_process.spawn('node', [authEntryPoint], { env: { ...process.env, PORT: new URL(runtimeEndpoints.auth).port, HOST: '127.0.0.1' } })` et `child_process.spawn('node', [localServiceEntryPoint], { env: { ...process.env, PORT: new URL(runtimeEndpoints.localService).port, HOST: '127.0.0.1' } })`. Adapter ces options aux contrats de lancement vérifiés ; aucun état prêt si un chemin ou une option reste indéterminé. Enregistrer séparément chaque enfant et son URL liée ; la Gateway consomme `AUTH_URL`, sans lancer un second Auth.
     - Electron réserve les ports et transmet leurs valeurs effectives à tous les enfants ; une collision ou un échec de bind entraîne l’arrêt du groupe en cours de démarrage, puis une nouvelle attribution cohérente avant relance.
  3. Mise en place de sondes de santé HTTP synchronisées : `GET new URL('/api/health', runtimeEndpoints.fastapi)`, `GET new URL('/api/health', runtimeEndpoints.gateway)`, `GET new URL('/api/health', runtimeEndpoints.auth)` et `GET new URL('/api/health', runtimeEndpoints.localService)`. La route FastAPI existe ; les routes Gateway/Auth/Local Service restent à vérifier ou ajouter avant l’intégration. Les ports 8000, 51491, 45899 et 8002 ne sont que les défauts du tableau. Aucun état « prêt » ne doit être émis avant la réussite des quatre sondes sur leurs URL effectives.
  4. Gestion sécurisée du cycle de vie : interception de `window-all-closed` et émission de `SIGTERM`, attente bornée puis `SIGKILL` si nécessaire pour FastAPI, Gateway, Auth et Local Service (et leurs descendants). Toute sortie inattendue d’Auth ou du Local Service révoque l’état prêt, bloque les actions dépendantes et déclenche l’arrêt supervisé ; vérifier la libération de leurs ports avant redémarrage.
- **Critère de validation (DoD)** :
  - Lancement via `npm run electron:dev`.
  - Les quatre routes `/api/health` construites à partir de `runtimeEndpoints.fastapi`, `runtimeEndpoints.gateway`, `runtimeEndpoints.auth` et `runtimeEndpoints.localService` répondent avec statut 200 en moins de 5 secondes, y compris après repli sur collision. Tester séparément le démarrage sans collision avec les ports par défaut `:8000`, `:51491`, `:45899`, `:8002`. Tester aussi échec de bind, arrêt et crash d’Auth/Local Service : aucun état prêt et aucun enfant orphelin.
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
     - Prévoir le streaming par fragments de 64 Ko via `MediaFileStore64k` ; le téléchargement actuel accumule le binaire entier. Respecter le dossier résolu par `MediaFileStore` (`storagePath` exclusif ou `outputs/`) ; la table `resource_v3` de `.hilo/index.sqlite` indexe ce chemin sans dupliquer le fichier.
     - Écritures JSON via `JSONDocumentStore` et son verrou `asyncio.Lock` ; aucun accès JSON direct.
  2. Protocole de cohérence fichiers/SQLite à implémenter (pas de transaction atomique commune aux deux supports) :
     - **Propriétaire unique du protocole cible : FastAPI**. Electron garantit une seule instance FastAPI pour un workspace (verrou OS de session détenu jusqu’à l’arrêt effectif ; seconde instance refusée). Dans cette instance, un coordinateur sérialise chaque clé `(workspaceId, generationId, artifactId)` depuis le streaming jusqu’à la notification, y compris reprise et nettoyage. Toutes les écritures média passent par l’extension cible de `MediaFileStore` ; le journal durable passe par `JSONDocumentStore`, avec synchronisation du fichier et de son répertoire avant publication à garantir dans l’extension cible. La Gateway ne publie, ne rejoue et ne supprime aucun fichier.
     - NestJS reste le seul écrivain SQLite : FastAPI lui demande via une opération HTTP/JSON-RPC cible idempotente de valider `resource_v3` (contrainte UNIQUE sur la clé), puis interroge le résultat par clé après timeout. Une réponse incertaine interdit tout nettoyage : NestJS doit fournir un état terminal durable `committed` ou `aborted`, sérialisé par clé et `operationId`. Un abort confirmé interdit toute insertion tardive de cette opération ; l’absence momentanée de ligne ne prouve pas un abandon. Ce contrat reste à définir et tester ; un verrou `asyncio.Lock` seul n’est pas une coordination inter-processus. Le verrou OS de workspace, détenu par FastAPI même si Electron s’arrête, doit empêcher tout chevauchement entre ancien coordinateur et reprise.
     - Réserver un nom temporaire unique par création exclusive (`O_CREAT | O_EXCL`), puis écrire le flux dans ce fichier du même dossier que la destination, vérifier taille/intégrité, fermer et synchroniser le fichier avant publication. Les lecteurs ignorent les temporaires et les opérations non validées.
     - Journaliser durablement l’intention avec clé, `operationId`, chemins, digest SHA-256, taille et identité du temporaire (volume + identifiant fichier). Publier par une primitive atomique **no-replace** : `os.link(temporaire, destination)` sur le même système de fichiers, qui échoue avec `FileExistsError` si la destination existe ; synchroniser le répertoire avant de retirer le lien temporaire, puis le synchroniser de nouveau. Aucun enchaînement `exists()` puis `os.replace()` n’est admissible. Si les liens physiques ne sont pas supportés, conserver l’opération en échec et le temporaire pour reprise, sans repli écrasant. Le `MediaFileStore` actuel utilise `os.replace` : une nouvelle opération de publication no-replace reste à implémenter et tester.
     - **Durabilité par plateforme, prérequis de livraison** : la cible multiplateforme conserve l’exigence de reprise après crash, mais elle ne sera annoncée que pour les couples OS/système de fichiers dont la synchronisation du fichier **et du répertoire** est implémentée et vérifiée. L’aide actuelle ne synchronise le répertoire que sur POSIX ; elle ne démontre aucune garantie équivalente sous Windows. Définir un adaptateur natif Windows et sa garantie, puis tester les interruptions aux deux synchronisations et au COMMIT sur Windows avant d’y activer cette publication durable. `os.fsync` sur le fichier seul ne remplace pas cette validation du répertoire. En l’absence d’adaptateur ou de capacité vérifiée, bloquer ce mode de publication avant création du fichier final, conserver le temporaire journalisé et signaler un environnement non pris en charge ; aucun repli no-replace ou de durabilité silencieusement affaibli. Ce prérequis reste à implémenter et à valider, aucune preuve Windows n’est fournie ici.
     - En cas de destination existante, refuser la collision par défaut. Une reprise ne réutilise un fichier que si journal, clé, `operationId`, identité du fichier et digest vérifié prouvent qu’il provient de cette opération ; ne pas suivre de lien symbolique. Ensuite seulement, demander à NestJS l’insertion transactionnelle `resource_v3` avec le chemin final, la clé et le digest. Notifier les vues après COMMIT confirmé ; la galerie attend aussi la validation du journal avant d’exposer l’artefact.
     - Avant publication, un échec récupérable conserve le temporaire identifié dans le journal pour reprise ; seul un abandon explicite de l’opération supprime son temporaire. Après publication, seul un état `aborted` terminal confirmé par NestJS autorise le nettoyage compensatoire par FastAPI du seul fichier créé par cette opération (journal/clé/operationId, identité et digest à vérifier de nouveau ; fichier remplacé ou modifié laissé intact ; sans garantie d’exclusion des écritures concurrentes dans ce dossier, ne pas supprimer le chemin final et conserver une entrée à réconcilier) ; si le nettoyage échoue, conserver une entrée à réconcilier. Aucun fichier préexistant n'est supprimé.
     - Après COMMIT, une reprise retrouve la ressource via la clé et termine le journal/les notifications sans nouvel insert ni suppression du média validé. Après crash entre publication no-replace et COMMIT, FastAPI reprend seul le journal sous le verrou de workspace et interroge l’index via NestJS : finaliser une ressource validée ou nettoyer l'orphelin de l'opération. Un replay vérifie chemin et intégrité puis réutilise la ressource.
     - Tester les interruptions après chaque étape, les doubles demandes et tentatives de seconde instance, les replays, les collisions de destination, le remplacement externe avant nettoyage, les timeouts NestJS/COMMIT et les échecs SQLite/disque avant de déclarer la cohérence garantie.
  3. Intégration du bouton "Injecter dans le Canevas" sur les cartes de la `MediaGallery`.
- **Critère de validation (DoD)** :
  - Tout média créé dans le Studio apparaît instantanément dans la palette d'assets du Workbench.
  - Zéro corruption de fichier ou blocage de base SQLite (`database is locked`) sous concurrence.

---

### Phase 5 : Durcissement Matériel Hôte, Fallback WebGPU & Validation End-to-End
- **Objectif** : Garantir des performances optimales sur la configuration cible de l'utilisateur (Intel Core i7-6600U @ 2.60GHz, 16 Go RAM, GPU Intel HD Graphics 520).
- **Tâches d'ingénierie** :
  1. Profilage de l'empreinte mémoire totale hôte :
     - Electron Main (~60 Mo) + Studio View (~45 Mo) + Agents View (~120 Mo) + FastAPI (~75 Mo) + NestJS (~95 Mo) = ~395 Mo RAM sans ComfyUI ; avec ComfyUI au repos (~140 Mo supplémentaires), total estimé ~535 Mo. Ces estimations excluent les modèles chargés et doivent être mesurées sur l’ensemble des sous-processus, dont Auth et Local Service.
     - Le scénario sans ComfyUI vise le plafond de 450 Mo RAM au repos ; le scénario avec ComfyUI (~535 Mo estimés hors modèles) le dépasse et ne doit pas être déclaré conforme à ce plafond. Valider les deux scénarios séparément ; aucune mesure réelle n’est fournie ici.
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
| **Collision de ports réseau locaux** | Modéré | Faible | Détection au boot, réservation du port et publication de toute attribution de secours dans `runtimeEndpoints`. Electron, BrowserViews, sondes de santé et clients FastAPI/LLM consomment cette même configuration avant de se connecter ; aucun consommateur ne conserve le port initial. |
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
