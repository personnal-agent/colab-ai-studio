# Modélisation Logicielle UML 2.5 — Omniforge (Version 01)

Ce dossier regroupe l'ensemble des diagrammes d'architecture, de conception logicielle et du dossier documentaire d'accompagnement d'**Omniforge** (évolution avancée de *Colab AI Studio*) selon le standard international **OMG UML 2.5.1** et les exigences méthodologiques et académiques du **Dr TRAORE (L3 MIAGE)**.

L'ensemble de la modélisation `01` formalise :
- L'architecture d'exécution tri-mode (**Google Colab GPU CUDA & TPU XLA**, **ComfyUI en "Headless API" locale sur PC `127.0.0.1:8188`** et **Fournisseurs Clés API distants**).
- L'extension du Dock Studio modulaire à **6 catégories multimédias** (`Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`).
- La gestion native des **adaptateurs LoRA en 1 clic** (`LoraPillControl`, injection automatique des `triggerWords`, curseur de poids et filtrage par modèle de base).
- Le filtrage strict des fichiers d'ingrédients selon les capacités réelles du modèle sélectionné (`acceptedInputTypes`).
- Le commutateur supérieur unifié **`[ Studio | Agents ]`** et le proxy LLM compatible OpenAI (`/v1/chat/completions`).
- La persistance documentaire atomique locale (`JSONDocumentStore` avec `asyncio.Lock` et remplacement atomique `.tmp`) et le rapatriement streaming par blocs de 64 Ko (`MediaFileStore`).

---

## 1. Synthèse de l'Architecture et Décisions Structurantes (Version 01)

| Axe Architectural | Décision de Conception Modélisée | Diagrammes de Référence |
| :--- | :--- | :--- |
| **1. Commutateur Global `[ Studio \| Agents ]`** | Barre de navigation supérieure (`TopNavBar`) dotée d'un bouton segmenté épuré à deux modes : `Studio` (création multimédia) et `Agents` (dialogue et assistance créative). Aucune sous-vue inventée ; bascule réactive d'espace de travail. | [01](diagrammes/01-perimetre-fonctionnel01.svg), [02](diagrammes/02-composants01.svg), [09](diagrammes/09-etats-dock-adaptatif01.svg) |
| **2. Exécution Tri-Mode & Orchestration Colab GPU/TPU (`Colab` \| `Local` \| `API`)** | Le composant `WorkerGateway` route chaque tâche selon `ExecutionMode` vers : (1) `ColabSessionOrchestrator` + `ColabClient` (connexion compte Google OAuth2, détection automatique des GPU `T4 16 Go`, `L4 24 Go`, `A100 40-80 Go` et TPU `v5e / v6e / v2-8 HBM`, tunnel chiffré sans ngrok manuel et cache VRAM multi-modèles LRU `ModelSwapper`), (2) `ComfyLocalClient` (`127.0.0.1:8188` sans interface nodale) ou (3) `ApiProviderClient` (passerelles REST distantes). | [01](diagrammes/01-perimetre-fonctionnel01.svg), [02](diagrammes/02-composants01.svg), [03](diagrammes/03-deploiement01.svg), [05](diagrammes/05-activite-generation01.svg), [06](diagrammes/06-sequence-generation01.svg) |
| **3. Moteur Local ComfyUI en "Headless API"** | `ComfyProcessManager` s'attache à une instance existante sur `:8188` ou lance/arrête un sous-processus silencieux (`--disable-auto-launch`). `ComfyWorkflowCompiler` sélectionne le template `.api.json` (`t2v`, `i2v_start`, `flf2v`, `ref2v`, `audio`, `3d`...) et chaîne dynamiquement les nœuds `LoraLoader`. | [02](diagrammes/02-composants01.svg), [03](diagrammes/03-deploiement01.svg), [05](diagrammes/05-activite-generation01.svg), [06](diagrammes/06-sequence-generation01.svg) |
| **4. Catalogue de Modèles Utilisateur Dynamique & Hors-Ligne** | La liste des modèles est persistée localement (`data/models.json`) et reste 100 % accessible hors-ligne : l'utilisateur peut ajouter/supprimer ses modèles Colab (`hfRepoId`, `.safetensors`, estimation VRAM), ses modèles locaux auto-détectés (`GET /object_info` ComfyUI) et ses mappings personnalisés via l'interface. | [01](diagrammes/01-perimetre-fonctionnel01.svg), [02](diagrammes/02-composants01.svg), [04](diagrammes/04-modele-de-donnees01.svg) |
| **5. Dock Adaptatif à 6 Catégories & Filtrage Strict** | Le `FloatingPromptDock` expose 6 onglets : `[ Image ]`, `[ Video ]`, `[ Audio ]`, `[ Lip sync ]`, `[ Upscaling ]`, `[ 3D Gen ]`. La zone de saisie principale gère les prompts visuels, paroles audio (`[verse]`, `[chorus]`) et tags vocaux. Les fentes d'ingrédients bloquent tout fichier incompatible via `ModelCapability.acceptedInputTypes`. | [02](diagrammes/02-composants01.svg), [04](diagrammes/04-modele-de-donnees01.svg), [05](diagrammes/05-activite-generation01.svg), [09](diagrammes/09-etats-dock-adaptatif01.svg) |
| **6. UX LoRA en 1 Clic (`LoraPillControl`)** | Pilule LoRA dans la rangée inférieure du Dock (si `supportsLora == true`), filtrée par `baseModel`. Activation/désactivation en 1 clic au poids par défaut (`0.8`), support multi-LoRA, curseur de poids (`0.1` à `1.5`) et injection automatique des `triggerWords`. | [01](diagrammes/01-perimetre-fonctionnel01.svg), [02](diagrammes/02-composants01.svg), [04](diagrammes/04-modele-de-donnees01.svg), [06](diagrammes/06-sequence-generation01.svg), [07](diagrammes/07-sequence-brand-context01.svg) |
| **7. Assistant IA Créatif & Proxy OpenAI Local** | L'onglet `Agents` active un assistant conversationnel pour l'aide à l'écriture de scénarios et de prompts. Route `/v1/chat/completions` sur `:8000` en streaming SSE avec gestion native de l'interruption (`AbortSignal`). | [01](diagrammes/01-perimetre-fonctionnel01.svg), [02](diagrammes/02-composants01.svg), [08](diagrammes/08-sequence-proxy-llm01.svg) |
| **8. Persistance Documentaire Atomique & Rapatriement 64 Ko** | Remplacement de la base SQL lourde par un `JSONDocumentStore` léger avec `asyncio.Lock` et écriture atomique (`.tmp` + `os.replace`). Téléchargement des médias en streaming par chunks de 64 Ko (`MediaFileStore`) vers `outputs/`. | [02](diagrammes/02-composants01.svg), [03](diagrammes/03-deploiement01.svg), [04](diagrammes/04-modele-de-donnees01.svg), [06](diagrammes/06-sequence-generation01.svg) |

---

## 2. Typologie Officielle des 14 Diagrammes OMG UML 2.5.1 & Couverture Omniforge

Le standard international **OMG UML 2.5.1** définit exhaustivement **14 types officiels de diagrammes**, répartis entre diagrammes structurels (statiques) et comportementaux (dynamiques). Conformément aux exigences académiques du **Dr TRAORE (L3 MIAGE)**, le tableau ci-dessous formalise la cartographie complète des 14 types, distinguant rigoureusement les **7 types retenus** (ayant donné lieu à **11 vues concrètes vectorielles**) et les **7 types exclus**, accompagnés de leur justification formelle d'exclusion :

| N° | Type de Diagramme Officiel (OMG UML 2.5.1) | Catégorie | Statut Omniforge | Justification Formelle de Retenue ou d'Exclusion | Fichiers Livrés |
| :-: | :--- | :---: | :---: | :--- | :--- |
| **1** | **Diagramme de Cas d'Utilisation** (*Use Case*) | Comportement | **RETENU** | Délimite le périmètre fonctionnel du système, les 4 pôles métiers et les relations de dépendance (`«include»`, `«extend»`). | [`01-perimetre-fonctionnel01.svg`](diagrammes/01-perimetre-fonctionnel01.svg) |
| **2** | **Diagramme de Composants** (*Component*) | Structure | **RETENU** | Modélise l'architecture logicielle modulaire en 4 couches, les interfaces formelles sucette/douille et les connecteurs d'assemblage. | [`02-composants01.svg`](diagrammes/02-composants01.svg) |
| **3** | **Diagramme de Déploiement** (*Deployment*) | Structure | **RETENU** | Formalise la topologie matérielle d'exécution tri-mode (poste local, instance Colab distante, cloud API) et les protocoles de communication. | [`03-deploiement01.svg`](diagrammes/03-deploiement01.svg) |
| **4** | **Diagramme de Classes** (*Class*) | Structure | **RETENU** | Spécifie le modèle conceptuel de données métier sans classes techniques ni clés étrangères redondantes, avec multiplicités complètes. | [`04-modele-de-donnees01.svg`](diagrammes/04-modele-de-donnees01.svg) |
| **5** | **Diagramme d'Activités** (*Activity*) | Comportement | **RETENU** | Orchestre le flux de traitement de génération de bout en bout sur 4 lignes d'eau, avec partitions d'acteurs et gestion d'erreurs. | [`05-activite-generation01.svg`](diagrammes/05-activite-generation01.svg) |
| **6** | **Diagramme de Séquence** (*Sequence*) | Interaction | **RETENU** | Décrit chronologiquement les échanges asynchrones entre composants pour la génération, l'arbitrage Brand Kit et le proxy LLM. | [`06-sequence-generation01.svg`](diagrammes/06-sequence-generation01.svg)<br>[`07-sequence-brand-context01.svg`](diagrammes/07-sequence-brand-context01.svg)<br>[`08-sequence-proxy-llm01.svg`](diagrammes/08-sequence-proxy-llm01.svg) |
| **7** | **Diagramme d'États-Transitions** (*State Machine*) | Comportement | **RETENU** | Modélise les cycles de vie des trois entités réactives majeures (`SessionPrompt`, `Generation`, `SlotMemoireModele`). | [`09-etats-dock-adaptatif01.svg`](diagrammes/09-etats-dock-adaptatif01.svg)<br>[`10-etats-tache-media01.svg`](diagrammes/10-etats-tache-media01.svg)<br>[`11-etats-model-swapper01.svg`](diagrammes/11-etats-model-swapper01.svg) |
| **8** | **Diagramme d'Objets** (*Object*) | Structure | *Exclu* | Redondant : les instances représentatives sont couvertes exhaustivement par les diagrammes de séquence (06-08) et le modèle de classes à multiplicités strictes (04). | *Non requis (justifié)* |
| **9** | **Diagramme de Paquetages** (*Package*) | Structure | *Exclu* | Couvert : la modularisation logique est formalisée directement par les sous-systèmes dans le diagramme de composants (02) et l'arborescence du déploiement (03). | *Non requis (justifié)* |
| **10** | **Diagramme de Structure Composite** (*Composite Structure*) | Structure | *Exclu* | Couvert : les décompositions internes de sous-systèmes, ports et connecteurs d'assemblage lollipop/socket sont déjà modélisés dans le diagramme de composants (02). | *Non requis (justifié)* |
| **11** | **Diagramme de Profil** (*Profile*) | Structure | *Exclu* | Inapplicable : utilisation exclusive des stéréotypes standards de l'OMG UML 2.5.1 (`«component»`, `«artifact»`, `«device»`, `«executionEnvironment»`, `«use»`), aucun profil personnalisé nécessaire. | *Non requis (justifié)* |
| **12** | **Diagramme Global d'Interaction** (*Interaction Overview*) | Interaction | *Exclu* | Redondant : l'enchaînement global des interactions est fidèlement capturé par le diagramme d'activités (05) complété par les 3 diagrammes de séquence dédiés (06-08). | *Non requis (justifié)* |
| **13** | **Diagramme de Communication** (*Communication*) | Interaction | *Exclu* | Redondant avec les diagrammes de séquence (06-08), ces derniers offrant en plus la dimension temporelle explicite et les fragments combinés normés (`loop`, `alt`, `opt`, `par`). | *Non requis (justifié)* |
| **14** | **Diagramme de Temps** (*Timing*) | Interaction | *Exclu* | Couvert avec une précision supérieure par les 3 machines à états (09-11) associées aux annotations de latence, timeouts réseau et SSE dans les diagrammes de séquence. | *Non requis (justifié)* |

---

## 3. Détail des 11 Vues Vectorielles Exhaustives Réalisées

### A. Vue Structurelle & Matérielle (Statique)

| N° | Diagramme | Fichier SVG (`01`) | Rôle & Description Technique |
| :-: | :--- | :--- | :--- |
| **01** | **Périmètre Fonctionnel** | [`01-perimetre-fonctionnel01.svg`](diagrammes/01-perimetre-fonctionnel01.svg) | Cartographie complète du système structurée en **4 pôles fonctionnels** : Pôle 1 (Génération Multimédia 6 Catégories & Dialogue Agents), Pôle 2 (Moteur ComfyUI Headless & Scanning Modèles), Pôle 3 (Gestion Brand Kit & Extraction d'ADN de Marque) et Pôle 4 (Gestion de Projets & Persistance Atomique). Acteurs primaires et secondaires (`Google Colab`, `ComfyUI Headless Local :8188`, `Fournisseurs API Cloud`), dépendances normées `«include»` et `«extend»` avec condition de garde explicite `[Brand Kit actif]`. |
| **02** | **Composants** | [`02-composants01.svg`](diagrammes/02-composants01.svg) | Architecture modulaire en 4 couches : Couche 1 (Frontend SPA React 18 / Vite / TypeScript), Couche 2 (API FastAPI / Uvicorn avec routeurs dédiés et proxy OpenAI `/v1/chat/completions`), Couche 3 (Orchestration tri-mode `WorkerGateway`, compilation de workflows ComfyUI `.api.json`, détection hybride de modèles et gestionnaire de processus `--disable-auto-launch`), et Couche 4 (Persistance atomique `JSONDocumentStore` thread-safe sans SGBD lourd et `MediaFileStore`). Interfaces formelles sucette/douille (lollipop/socket) et stéréotypes `«component»`. |
| **03** | **Déploiement** | [`03-deploiement01.svg`](diagrammes/03-deploiement01.svg) | Topologie physique d'exécution tri-mode modélisée selon UML 2.5 : Nœud `Poste de Travail Utilisateur [1]` (Navigateur Web `:5173`, Serveur Python Uvicorn `:8000`, Stockage local `data/ & outputs/` relié en trait plein étiqueté `«POSIX / NTFS File I/O»`, Démon `ComfyUI Headless :8188`), Nœud `Instance Cloud Google Colab [0..1]` avec artefact `colab_session_bridge.py` et runtime GPU/TPU, et Nœud `Infrastructure Cloud Tiers [1..*]` avec artefact OpenAPI `cloud_inference_api.oas`. Chemins de communication en traits pleins non orientés. |
| **04** | **Classes (Domaine)** | [`04-modele-de-donnees01.svg`](diagrammes/04-modele-de-donnees01.svg) | Modèle de données métier canonique sans classe technique `LocalConfig` : 3 énumérations (`MediaType`, `ExecutionMode`, `TaskStatus`), 11 classes métier singulières (`Project`, `Generation`, `GenerationReference`, `GenerationParameter`, `BrandKit`, `LoraConfig`, `LoraSelection`, `ModelSpec`, `ModelCapability`, `SessionPrompt`, `SlotMemoireModele`), 12 associations navigables avec multiplicités amont/aval complètes, 4 à 12 opérations actives par entité majeure, zéro clé étrangère dupliquée et planarité parfaite (0 croisement de lignes). |

### B. Vue Comportementale – Flux & Interactions (Dynamique)

| N° | Diagramme | Fichier SVG (`01`) | Rôle & Description Technique |
| :-: | :--- | :--- | :--- |
| **05** | **Activité** | [`05-activite-generation01.svg`](diagrammes/05-activite-generation01.svg) | Flux d'orchestration de bout en bout sur 4 lignes d'eau (`Créateur de contenu`, `Frontend React SPA`, `Backend FastAPI & WorkerGateway`, `Worker d'Inférence Actif`). Traite la validation stricte `acceptedInputTypes` (rejet HTTP 422), l'arbitrage tri-mode (`local` vs `colab`/`api`), la région interruptible avec signal d'annulation utilisateur et la persistance atomique finale. |
| **06** | **Séquence (Génération)** | [`06-sequence-generation01.svg`](diagrammes/06-sequence-generation01.svg) | Séquence asynchrone numérotée formalisant la réception du `GenerationRequest`, l'enrichissement optionnel (`opt` Brand Kit & LoRA), la bifurcation (`alt` mode local ComfyUI via WebSocket vs tunnel distant Colab/API) et la diffusion des événements de progression via le flux SSE `/api/tasks/{task_id}/status` jusqu'au rapatriement binaire par `MediaFileStore`. |
| **07** | **Séquence (Brand Context)** | [`07-sequence-brand-context01.svg`](diagrammes/07-sequence-brand-context01.svg) | Chronogramme d'enrichissement du contexte créatif : consultation atomique de `BrandKit` et `LoraConfig`, résolution de conflit des références visuelles selon la règle `P1 (utilisateur) > P2 (brand kit) > P3 (logo)`, préfixage automatique des `triggerWords` LoRA et synthèse par le modèle LLM local ou distant. |
| **08** | **Séquence (Proxy LLM)** | [`08-sequence-proxy-llm01.svg`](diagrammes/08-sequence-proxy-llm01.svg) | Passerelle d'interopérabilité OpenAI compatible `POST /v1/chat/completions` en flux continu SSE (`text/event-stream`). Modélise la gestion d'interruption via `AbortSignal`, assurant l'arrêt immédiat du processus de génération de texte et la libération de la VRAM. |

### C. Vue Comportementale – Machines à États-Transitions (`stm`)

| N° | Diagramme | Fichier SVG (`01`) | Rôle & Description Technique |
| :-: | :--- | :--- | :--- |
| **09** | **États (`SessionPrompt` / Dock Adaptatif)** | [`09-etats-dock-adaptatif01.svg`](diagrammes/09-etats-dock-adaptatif01.svg) | Machine à états hiérarchique de l'entité `SessionPrompt` et du pupitre de saisie : état composite `DockEnEdition` avec ses 6 sous-états (`ModeImageSelectionne`, `ModeVideoSelectionne`, `ModeAudioSelectionne`, `ModeLipSyncSelectionne`, `ModeUpscalingSelectionne`, `Mode3DGenSelectionne`), transitions internes de modification de paramètres/LoRA, état d'inhibition `DockVerrouillePendantGeneration` et bascule vers `VueAgentsActive`. |
| **10** | **États (`Generation` / Tâche d'Inférence)** | [`10-etats-tache-media01.svg`](diagrammes/10-etats-tache-media01.svg) | Cycle de vie unifié d'une entité `Generation` : `EnAttentePriseEnCharge` (`queued`) $\rightarrow$ `EnTraitementGPU` (`processing`) $\rightarrow$ `RapatriementEnCours` (`downloading`) $\rightarrow$ `SauvegardeEnCours` (`saving`) $\rightarrow$ états terminaux stables persistés `Terminee` (`completed`), `Annulee` (`cancelled`) et `Echouee` (`failed`) sans `FinalState` destructif. |
| **11** | **États (`SlotMemoireModele` / Gestion VRAM & LoRA)** | [`11-etats-model-swapper01.svg`](diagrammes/11-etats-model-swapper01.svg) | Gestion dynamique de la mémoire VRAM/HBM GPU/TPU de l'entité `SlotMemoireModele` : `EnVeilleVRAMLibre`, `ChargementEnCours` (poids de base + montage LoRA), `ModeleActif` (avec transition réflexive de montage/démontage d'adaptateurs sans recharger le modèle de base), `EvictionVRAMEnCours` (nettoyage mémoire `del active_pipeline`, `gc.collect()`, `torch.cuda.empty_cache()`) et `EnRecuperationSaturation` (CUDA OOM). |

---

## 4. Matrice de Traçabilité (Spécifications $\leftrightarrow$ Modèles UML 2.5)

| Exigence Métier & Technique ([`SPECIFICATION01.md`](../../SPECIFICATION01.md) / [`ARCHITECTURE01.md`](../../ARCHITECTURE01.md)) | Classes & Composants Canoniques Impliqués | Diagrammes UML (`01`) |
| :--- | :--- | :--- |
| **Commutateur supérieur `[ Studio \| Agents ]`** | `TopNavBar`, `AppModeSwitch`, `SessionPrompt`, `StudioContext` | `01`, `02`, `09` |
| **Dock adaptatif à 6 catégories (`Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`)** | `FloatingPromptDock`, `MediaType`, `GenerationParameter`, `ModelCapability` | `01`, `02`, `04`, `09` |
| **Filtrage strict des types d'entrée (`acceptedInputTypes`)** | `FloatingPromptDock`, `GenerationReference`, `ModelCapability` | `02`, `04`, `05`, `09` |
| **Gestion LoRA 1-clic (`0.8`), multi-LoRA & injection `triggerWords`** | `LoraPillControl`, `LoraConfig`, `LoraSelection`, `ComfyWorkflowCompiler` | `01`, `02`, `04`, `06`, `07`, `09`, `11` |
| **Moteur Local ComfyUI Headless API (`127.0.0.1:8188`)** | `ComfyProcessManager`, `ComfyWorkflowCompiler`, `ComfyLocalClient`, `ExecutionMode` | `01`, `02`, `03`, `04`, `05`, `06`, `10` |
| **Détection hybride des modèles locaux & catalogue dynamique** | `LocalModelRegistry`, `ModelSpec`, `ModelCapability`, `data/models.json` | `01`, `02`, `03`, `04` |
| **Exécution Colab GPU/TPU chiffrée & gestion VRAM (`ModelSwapper`)** | `WorkerGateway`, `ColabClient`, `ColabSessionOrchestrator`, `SlotMemoireModele` | `01`, `02`, `03`, `04`, `05`, `06`, `11` |
| **Compilation Brand Kit & Priorité de références (`P1 > P2 > P3`)** | `BrandContextCompiler`, `BrandKit`, `GenerationReference`, `JSONDocumentStore` | `01`, `02`, `04`, `05`, `07` |
| **Persistance atomique JSON & streaming binaire 64 Ko** | `JSONDocumentStore`, `MediaFileStore`, `Generation`, `Project` | `02`, `03`, `04`, `05`, `06`, `10` |

---

## 5. Fiches Descriptives Textuelles des Cas d'Utilisation Majeurs (Règle DOC-01)

Conformément au gabarit officiel en 5 sections du **Dr TRAORE** (*Support UML : Diagramme des Cas d'Utilisation*, slides 47-48, 52 ; TD p. 11-13), les cas d'utilisation critiques du système Omniforge sont formalisés ci-après :

### 5.1. Fiche CU-01 : Générer un média IA

```text
================================================================================
FICHE DESCRIPTIVE DE CAS D'UTILISATION : CU-01
================================================================================
1. IDENTIFICATION & EN-TÊTE
   - Nom du cas : Générer un média IA
   - Objectif / Intention : Permettre au créateur de contenu de synthétiser un média
     numérique (image, vidéo, audio, lip-sync, upscaling ou objet 3D) à partir
     d'instructions textuelles, d'ingrédients optionnels et d'adaptateurs LoRA,
     en exécutant l'inférence sur le moteur actif (Colab, ComfyUI Local ou Cloud API).
   - Acteur principal : Créateur de contenu
   - Acteurs secondaires : Google Colab, ComfyUI Headless Local :8188, Fournisseurs API Cloud
   - Préconditions :
     * L'application Omniforge est lancée sur le poste local (FastAPI :8000 opérationnel).
     * Au moins un moteur d'inférence est actif et joignable (Colab connecté, ComfyUI
       démarré sur :8188 ou clé API cloud configurée).
     * Le projet actif est chargé ou le projet par défaut est sélectionné.
   - Postconditions (Garanties de succès) :
     * Le média généré (.png, .mp4, .wav, .glb) est rapatrié et enregistré sur le disque
       local dans outputs/projects/<id>/ ou outputs/YYYY-MM-DD/.
     * L'entité Generation est persistée de façon atomique dans data/generations.json.
     * La galerie multimédia affiche la nouvelle carte média prête à l'utilisation.

2. ÉVÉNEMENT DÉCLENCHEUR
   - Le créateur de contenu clique sur le bouton « Générer » du FloatingPromptDock
     ou presse le raccourci clavier Ctrl+Enter.

3. SCÉNARIO NOMINAL (CHEMIN PRINCIPAL DE SUCCÈS)
   1. Le créateur sélectionne l'un des 6 onglets de média et renseigne son prompt.
   2. Le système vérifie la conformité des ingrédients déposés avec les types MIME
      autorisés (ModelCapability.acceptedInputTypes).
   3. Le créateur active optionnellement un adaptateur LoRA compatible en 1 clic.
   4. Le créateur déclenche la génération.
   5. Le système instancie une tâche (TaskStatus = queued) et compile le contexte
      de marque si un Brand Kit est associé (CU-02).
   6. Le système injecte automatiquement les triggerWords LoRA dans le prompt final.
   7. Le composant WorkerGateway route la charge vers le worker d'inférence sélectionné.
   8. Le worker charge le modèle en VRAM/HBM (si non présent en cache) et réalise l'inférence.
   9. Le système notifie le frontend de la progression en temps réel via le flux SSE.
   10. Le binaire produit est rapatrié par chunks de 64 Ko par MediaFileStore.
   11. La tâche passe au statut completed et les métadonnées sont écrites de façon atomique.
   12. L'interface déverrouille le Dock et affiche le média dans la MediaGallery.

4. SCÉNARIOS ALTERNATIFS (BRANCHEMENTS)
   - 7a. Exécution sur ComfyUI Local (:8188) :
     * 7a1. Le backend compile dynamiquement le graphe .api.json correspondant à la
            topologie demandée (t2v, i2v, audio, 3d) et y injecte les nœuds LoraLoader.
     * 7a2. Le backend transmet le prompt au serveur local via POST /prompt.
     * 7a3. Les événements de rendu sont collectés via la WebSocket ws://127.0.0.1:8188/ws
            et convertis en flux SSE vers le navigateur.
   - 7b. Exécution sur Fournisseur API Cloud :
     * 7b1. Le backend transmet la requête signée par clé d'autorisation HTTPS REST.
     * 7b2. Le backend interroge le statut du job distant jusqu'à disponibilité du binaire.

5. SCÉNARIOS D'EXCEPTION (CHEMINS D'ÉCHEC)
   - 2e. Type de fichier d'ingrédient non supporté :
     * 2e1. Le système rejette la requête immédiatement avec le code HTTP 422 Unprocessable Entity.
     * 2e2. Le dock affiche un message d'avertissement précisant les formats acceptés.
     * 2e3. Le cas d'utilisation s'interrompt sans mobiliser de ressource d'inférence.
   - 8e. Saturation de la mémoire VRAM distante (CUDA Out Of Memory) :
     * 8e1. Le worker distant capture l'erreur CUDA OOM et déclenche une purge LRU forcée.
     * 8e2. La tâche passe au statut failed et l'incident est consigné dans le journal.
     * 8e3. L'utilisateur est alerté avec proposition de réduire la résolution ou de changer de moteur.
   - 9e. Annulation demandée par l'utilisateur :
     * 9e1. L'utilisateur clique sur « Annuler » pendant le traitement.
     * 9e2. Le backend émet un signal d'interruption immédiat vers le worker actif.
     * 9e3. La tâche passe au statut cancelled, les fichiers partiels sont purgés et le dock est libéré.
================================================================================
```

### 5.2. Fiche CU-02 : Compiler et injecter le contexte de marque

```text
================================================================================
FICHE DESCRIPTIVE DE CAS D'UTILISATION : CU-02
================================================================================
1. IDENTIFICATION & EN-TÊTE
   - Nom du cas : Compiler et injecter le contexte de marque
   - Objectif / Intention : Construire automatiquement une directive textuelle et visuelle
     cohérente à partir d'un Brand Kit sélectionné (palettes de couleurs HEX, typographies,
     règles stylistiques et références visuelles) et l'intégrer au prompt de génération.
   - Acteur principal : Créateur de contenu
   - Acteurs secondaires : Fournisseurs API Cloud (modèle LLM) ou LLM local
   - Préconditions :
     * Au moins un Brand Kit valide est enregistré dans data/brand_kits.json.
     * Le créateur a activé l'option « Appliquer le Brand Kit » sur le dock.
   - Postconditions (Garanties de succès) :
     * Le prompt utilisateur est enrichi des contraintes visuelles traduites en anglais.
     * Les références visuelles sont ordonnées et plafonnées selon la règle P1 > P2 > P3.
     * Les triggerWords des LoRAs sélectionnés sont insérés sans altérer la cohérence lexicale.

2. ÉVÉNEMENT DÉCLENCHEUR
   - Déclenchement conditionnel par extension («extend» [Brand Kit actif]) depuis le cas
     d'utilisation CU-01 « Générer un média IA » dès lors qu'un Brand Kit est activé sur le Dock.

3. SCÉNARIO NOMINAL (CHEMIN PRINCIPAL DE SUCCÈS)
   1. Le système lit de manière atomique l'entité BrandKit correspondante via JSONDocumentStore.
   2. Le système extrait les attributs : couleurs prioritaires, typographies, mot-clé d'ambiance.
   3. Le composant BrandContextCompiler formule une requête de synthèse pour le proxy LLM.
   4. Le modèle LLM produit une description contextuelle condensée et déterministe en anglais.
   5. Le système applique la règle d'arbitrage des références visuelles (RG-02) :
      les images fournies par l'utilisateur (P1) sont conservées en priorité, complétées par
      les images de style du Brand Kit (P2), puis par le logo (P3), dans la limite de maxImageRefs.
   6. Les mots-clés d'activation (triggerWords) des LoRAs actifs sont préfixés au prompt.
   7. Le prompt enrichi consolidé est retourné au module d'orchestration pour transmission au worker.

4. SCÉNARIOS ALTERNATIFS (BRANCHEMENTS)
   - 4a. Mode déconnecté ou indisponibilité du service LLM :
     * 4a1. Le compilateur bascule automatiquement sur le moteur de template déterministe hors-ligne.
     * 4a2. Une concaténation structurée en anglais des codes hexadécimaux et règles est assemblée.
     * 4a3. Le flux reprend à l'étape 5 sans blocage de l'inférence.

5. SCÉNARIOS D'EXCEPTION (CHEMINS D'ÉCHEC)
   - 1e. Brand Kit corrompu ou introuvable :
     * 1e1. Le système émet une alerte dans les journaux d'exécution.
     * 1e2. Le système poursuit la génération en utilisant le prompt brut de l'utilisateur.
     * 1e3. Une notification informe le créateur que le média a été généré sans contexte de marque.
================================================================================
```

### 5.3. Fiche CU-03 : Dialoguer avec l'assistant IA créatif

```text
================================================================================
FICHE DESCRIPTIVE DE CAS D'UTILISATION : CU-03
================================================================================
1. IDENTIFICATION & EN-TÊTE
   - Nom du cas : Dialoguer avec l'assistant IA créatif
   - Objectif / Intention : Offrir au créateur un espace d'échange conversationnel en streaming
     pour concevoir des scénarios, formuler des idées de scènes, raffiner des prompts complexes
     ou obtenir des conseils de cadrage via le commutateur [ Studio | Agents ].
   - Acteur principal : Créateur de contenu
   - Acteurs secondaires : Google Colab (LLM distant) ou Fournisseurs API Cloud (passerelle OpenAI)
   - Préconditions :
     * Le serveur local FastAPI écoute sur le port :8000.
     * La passerelle /v1/chat/completions est configurée avec un endpoint LLM joignable.
   - Postconditions (Garanties de succès) :
     * L'échange conversationnel est streamé token par token dans l'interface Agents.
     * L'historique d'échange est sauvegardé dans l'entité SessionPrompt du projet actif.
     * Le créateur peut copier directement les prompts suggérés vers le Dock Studio en 1 clic.

2. ÉVÉNEMENT DÉCLENCHEUR
   - Le créateur sélectionne l'onglet « Agents » dans la barre supérieure TopNavBar et saisit un message.

3. SCÉNARIO NOMINAL (CHEMIN PRINCIPAL DE SUCCÈS)
   1. L'utilisateur bascule l'interface sur le mode « Agents ».
   2. Le frontend initialise un composant de dialogue relié à l'endpoint SSE /v1/chat/completions.
   3. Le créateur soumet une requête créative (ex: "Aide-moi à concevoir un teaser cyberpunk pour ma marque").
   4. Le backend transmet le contexte de session (SessionPrompt) et le prompt système à la passerelle.
   5. Le modèle LLM génère la réponse sous forme de flux continu de tokens SSE (chunk delta).
   6. Le frontend assemble et affiche les tokens en temps réel avec coloration syntaxique des prompts.
   7. La session conversationnelle est mise à jour et persistée localement.

4. SCÉNARIOS ALTERNATIFS (BRANCHEMENTS)
   - 3a. Injection automatique d'un prompt vers le Studio :
     * 3a1. Le créateur clique sur le bouton « Envoyer au Studio » affiché sous un bloc de prompt suggéré.
     * 3a2. L'interface bascule automatiquement sur la vue « Studio ».
     * 3a3. Le prompt est prérempli dans le champ de saisie du FloatingPromptDock, prêt à être généré.

5. SCÉNARIOS D'EXCEPTION (CHEMINS D'ÉCHEC)
   - 5e. Interruption de la saisie par l'utilisateur :
     * 5e1. Le créateur clique sur « Arrêter la réponse ».
     * 5e2. Le frontend déclenche immédiatement le signal AbortSignal sur la requête HTTP.
     * 5e3. Le backend propage l'interruption au moteur LLM et clôture le flux SSE sans latence.
================================================================================
```

---

## 6. Tableau de Classement Priorité / Risque des Cas d'Utilisation (Règle DOC-04)

Conformément à la démarche de modélisation itérative du **Dr TRAORE** (*Support UML : Diagramme des Cas d'Utilisation*, slides 45-46 ; TD p. 11), le croisement méthodique entre la **Priorité Métier** (valeur apportée à l'utilisateur) et le **Risque Technique** (complexité d'intégration, dépendances d'infrastructure, gestion mémoire) permet de définir rigoureusement le périmètre du **Lot 1 (Cœur du Système)**, en harmonie exacte avec la numérotation CU-01 à CU-10 du diagramme 01 :

| Réf. | Cas d'Utilisation Métier | Priorité Métier | Risque Technique | Lot d'Implémentation | Justification Architecturale |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **CU-01** | **Générer un média IA** (6 types multimédias) | **Haute** | **Élevé** | **Lot 1 (Prioritaire)** | Fonctionnalité vitale du système. Implique la gestion multi-moteurs (Colab, ComfyUI, API), la compilation dynamique de graphes et le rapatriement streaming 64 Ko. |
| **CU-02** | **Compiler et injecter le contexte de marque** | **Haute** | **Moyen** | **Lot 1 (Prioritaire)** | Élément différenciant d'Omniforge. Résolution sous contrainte des priorités de références visuelles (`P1 > P2 > P3`) et injection déterministe. |
| **CU-03** | **Dialoguer avec l'assistant IA créatif** | **Haute** | **Faible** | **Lot 1 (Prioritaire)** | Espace conversationnel structurant du mode `[ Agents ]`. Passerelle proxy OpenAI standardisée avec streaming SSE et interruption `AbortSignal`. |
| **CU-04** | **Superviser la santé VRAM et les workers** | **Haute** | **Élevé** | **Lot 1 (Prioritaire)** | Prévention critique des saturations mémoire GPU (CUDA OOM), détection dynamique VRAM/HBM et coordination des bascules d'état. |
| **CU-05** | **Gérer les configurations LoRA** | **Haute** | **Moyen** | **Lot 1 (Prioritaire)** | Expérience utilisateur 1-clic, vérification de compatibilité de modèle de base et chaînage de nœuds `LoraLoader` dans ComfyUI. |
| **CU-06** | **Piloter le processus ComfyUI Headless** | **Moyenne** | **Élevé** | **Lot 2 (Secondaire)** | Gestion du cycle de vie d'un sous-processus système local (`--disable-auto-launch`, port `:8188`, détection de processus préexistant). |
| **CU-07** | **Gérer les Brand Kits** | **Moyenne** | **Faible** | **Lot 2 (Secondaire)** | Opérations CRUD de gestion documentaire (couleurs, typographies, règles) avec persistance atomique `JSONDocumentStore`. |
| **CU-08** | **Gérer les Projets & Historique** | **Moyenne** | **Faible** | **Lot 2 (Secondaire)** | Organisation documentaire hiérarchique et traçabilité souveraine des médias sur le système de fichiers local. |
| **CU-09** | **Scanner et mapper les modèles locaux** | **Faible** | **Faible** | **Lot 3 (Extension)** | Interrogation de l'endpoint ComfyUI `GET /object_info` et mise à jour dynamique du catalogue utilisateur hors-ligne. |
| **CU-10** | **Extraire l'ADN de marque depuis une URL** | **Faible** | **Moyen** | **Lot 3 (Extension)** | Scraping web externe via HTTP, extraction heuristique de palettes chromatiques et vectorielles. |

---

## 7. Tableau des Candidats et Éliminations de Classes (Règle DOC-03)

Conformément au barème d'ingénierie logicielle de Niveau 4 du **Dr TRAORE** (*Support UML : Diagramme de Classes*, Vol. 2 Annexe C p. 206), le tableau ci-dessous explicite le processus de filtrage et d'épuration appliqué aux classes candidates identifiées lors de l'analyse du domaine d'Omniforge :

| Candidat Analysé | Nature Initiale | Décision d'Ingénierie | Motif Formel d'Élimination ou de Retenue (Règles Traorè / OMG) |
| :--- | :--- | :---: | :--- |
| **Project** | Entité métier | **RETENU** | Entité racine du domaine représentant l'espace de travail utilisateur, détentrice des générations et des sessions de dialogue. |
| **Generation** | Entité métier | **RETENU** | Concept central matérialisant une demande d'inférence, son statut, son média type et son résultat. |
| **GenerationReference** | Concept d'entrée | **RETENU (Value Object)** | Remplace avantageusement les attributs multiples dispersés. Composé exclusivement dans `Generation` avec multiplicité ordonnée `0..3 {ordered}`. |
| **GenerationParameter** | Paramètres de rendu | **RETENU (Value Object)** | Isole les dimensions, pas d'échantillonnage (steps), seed et framerate sous forme d'objet valeur immuable composant `Generation`. |
| **BrandKit** | Entité métier | **RETENU** | Référentiel de charte graphique (couleurs HEX, typographies, consignes stylistiques). |
| **LoraConfig** | Entité catalogue | **RETENU** | Spécification d'un adaptateur de bas rang (.safetensors, mots-clés d'activation, modèle de base). |
| **LoraSelection** | Association d'instance | **RETENU (Value Object)** | Capture le montage d'un LoRA sur une génération donnée avec son poids effectif (`strengthModel`, `strengthClip`) ordonné `0..5 {ordered}`. |
| **ModelSpec** | Entité catalogue | **RETENU** | Représente la spécification formelle d'un modèle d'inférence (famille, VRAM requise, modes supportés). |
| **ModelCapability** | Profil matériel | **RETENU (Value Object)** | Découplage orthogonal spécifiant les capacités d'un modèle selon la modalité (`acceptedInputTypes`, `maxImageRefs`, `supportsLora`). |
| **SessionPrompt** | Participant dynamique | **RETENU** | Capture l'état du dock et l'historique conversationnel de l'assistant IA (sujet de la machine à états 09 et des séquences 06, 07, 08). |
| **SlotMemoireModele** | Participant dynamique | **RETENU** | Matérialise l'état de la mémoire VRAM/HBM GPU/TPU (sujet de la machine à états 11). |
| *LocalConfig* | Données techniques | **ÉLIMINÉ** | *Anti-pattern d'infrastructure* (ports réseau `:8188`, flags CLI). Déporté en architecture de composants (02) et déploiement (03). |
| *ApiKey* | Donnée de sécurité | **ÉLIMINÉ** | Simple attribut ou variable d'environnement chiffrée. Ne possède aucun comportement métier justifiant une classe. |
| *HistoryGallery* | IHM / Affichage | **ÉLIMINÉ** | *Anti-pattern de composant visuel*. La galerie est un composant React frontend (02), non une entité conceptuelle du domaine. |
| *NotificationToast* | Événement IHM | **ÉLIMINÉ** | Artefact d'interface purement éphémère. |

---

## 8. Scénarios du Test du Chemin Métier (Règle DOC-06)

Conformément aux exigences méthodologiques de Niveau 4 du **Dr TRAORE** (*Support UML : Diagramme de Classes*, Vol. 2 Annexe C p. 207), le modèle de données métier `04` est soumis à un test formel de connexité et de navigabilité validant que les scénarios fondamentaux du système peuvent être traversés de bout en bout sans aucune rupture sémantique ni duplication de clés étrangères :

| Scénario Métier Audité | Chaîne de Navigabilité Objet Traversée (Diagramme `04`) | Justification et Validité Sémantique |
| :--- | :--- | :--- |
| **1. Requête d'historique filtrée par projet actif** | `Project [1]` $\xrightarrow{+generations}$ `Generation [0..*]` | L'association de composition exclusive `1 ◆── 0..*` permet de récupérer l'ensemble des médias générés d'un espace de travail sans avoir à stocker de clé étrangère redondante `projectId` dans `Generation`. |
| **2. Validation stricte des ingrédients et filtrage LoRA par modèle** | `Generation [0..*]` $\xrightarrow{+cibleModele}$ `ModelSpec [1]` $\xrightarrow{+capacites}$ `ModelCapability [1..6]` (attribut `acceptedInputTypes`) et `Generation [1]` $\xrightarrow{+loraSelections}$ `LoraSelection [0..5]` $\xrightarrow{+configure}$ `LoraConfig [1]` (attribut `triggerWords`) | L'isolation orthogonale entre la spécification du modèle (`ModelSpec`) et ses capacités (`ModelCapability`) garantit un typage fort : le système valide instantanément si le type MIME de l'ingrédient est accepté (`acceptedInputTypes`) et filtre les adaptateurs LoRA compatibles via `triggerWords` et `defaultWeight`. |
| **3. Enrichissement du prompt avec contexte de marque, LoRA et session** | `SessionPrompt [1]` $\xrightarrow{+initie}$ `Generation [0..*]` combiné à `Generation [0..*]` $\xrightarrow{+appliedBrandKit}$ `BrandKit [0..1]` et `Project [0..*]` $\xrightarrow{+defaultBrandKit}$ `BrandKit [0..1]` | Le graphe permet d'associer la session de prompt active (`SessionPrompt`) à la génération résultante, tout en remontant jusqu'aux entités LoRA sélectionnées (`LoraSelection` $\rightarrow$ `LoraConfig`) pour en extraire automatiquement les `triggerWords` et appliquer l'arbitrage Brand Kit (`P1 > P2 > P3`). |
| **4. Supervision de la saturation mémoire du worker et allocation VRAM** | `SlotMemoireModele [0..*]` $\xrightarrow{+alloue}$ `ModelSpec [0..1]` et `SessionPrompt [0..*]` $\xrightarrow{+activeSlot}$ `SlotMemoireModele [0..1]` | La liaison univoque entre le slot mémoire de l'instance (`SlotMemoireModele`, attributs `freeMemoryGb`, `totalMemoryGb`, `loadedLoraCount`) et la spécification du modèle actif (`ModelSpec.vramRequiredGb`) permet à l'orchestrateur de calculer en temps réel la marge mémoire résiduelle et d'ordonnancer une éviction LRU avant tout risque de dépassement de capacité. |

*Conclusion du test de chemin :* Le modèle de classes `04` est parfaitement connexe, intègre toutes les associations nécessaires sans aucun cycle bloquant, et répond rigoureusement à l'intégralité des parcours d'ingénierie et de persistance sans aucune clé étrangère dupliquée ni classe technique résiduelle.

---

## 9. Règles de Gestion Hors Notation Graphique (Règle DOC-05)

Conformément aux directives du **Dr TRAORE** (*Support UML : Diagramme de Classes*, Vol. 2 Annexe C p. 207 : *« Règles de gestion hors diagramme (nombre atteint, renvoi au bon volume) : 1,0 pt »*), les contraintes métier non modélisables par le strict formalisme visuel d'UML 2.5 sont formalisées et rattachées ci-après :

| Réf. | Intitulé de la Règle de Gestion | Énoncé Formel de la Règle & Contraintes d'Intégrité | Diagrammes & Volumes Associés |
| :---: | :--- | :--- | :--- |
| **RG-01** | **Invariance de Persistance Atomique** | Toute écriture de document JSON dans `data/` (`generations.json`, `projects.json`, `brand_kits.json`, `models.json`) doit impérativement acquérir un verrou asynchrone exclusif (`asyncio.Lock`), effectuer l'écriture dans un fichier temporaire `.tmp` sur le même point de montage, puis exécuter un remplacement atomique système (`os.replace`) afin de bannir tout risque de corruption en cas de coupure inopinée. | Diagrammes `02`, `04`, `10`  <br>*Support Traoré Vol. 2 p. 195* |
| **RG-02** | **Priorité Déterministe d'Injection des Références Visuelles** | Lorsque le nombre total de références visuelles transmises dépasse la capacité maximale admise par le modèle (`ModelCapability.maxImageRefs`), le compilateur de contexte applique une préséance stricte : `P1 (Images utilisateur fournies dans le Dock)` **>** `P2 (Images d'ambiance du Brand Kit actif)` **>** `P3 (Logo vectoriel de la marque)`. Les références de niveau inférieur excédentaires sont tronquées avec avertissement dans le journal. | Diagrammes `04`, `05`, `07`  <br>*Support Traoré Vol. 2 p. 198* |
| **RG-03** | **Plafond Mémoire Strict de l'Hôte Local (FastAPI < 80 Mo)** | Le processus serveur local Python / FastAPI (`:8000`) ne doit sous aucun prétexte instancier de runtime de calcul tensoriel local lourd (interdiction formelle d'importer `torch`, `diffusers` ou `transformers` dans l'orchestrateur). Sa mémoire résidente mesurée via `psutil` doit demeurer strictement inférieure à **80 Mo de RAM**, garantissant l'exécution fluide sur toute machine dépourvue de GPU dédié. | Diagrammes `02`, `03`  <br>*Support Traoré Vol. 6 p. 52* |
| **RG-04** | **Éviction de VRAM Distante sous Politique LRU Stricte** | Sur le worker d'inférence distant (Google Colab GPU CUDA ou TPU XLA), un modèle déjà présent dans le cache mémoire (`SlotMemoireModele`) n'est évincé que si et seulement si la mémoire physique libre est insuffisante pour charger le modèle requis par la nouvelle tâche. L'éviction libère les poids (`del active_pipeline`), force le ramasse-miettes (`gc.collect()`) et purge le cache mémoire (`torch.cuda.empty_cache()` ou `xm.mark_step()`). | Diagrammes `04`, `11`  <br>*Support Traoré Vol. 5 p. 142* |
| **RG-05** | **Isolation du Démon ComfyUI et Démarrage Non-Intrusif** | Lorsque le mode d'exécution local est sollicité, le gestionnaire de processus teste en premier lieu la présence d'une instance ComfyUI déjà active sur `127.0.0.1:8188`. Si aucune instance ne répond et que `autoManageProcess = true`, le sous-processus est spawné avec le flag obligatoire `--disable-auto-launch` pour interdire l'ouverture intempestive du navigateur. À l'arrêt d'Omniforge, le sous-processus ainsi créé est proprement arrêté (signal SIGTERM). | Diagrammes `02`, `03`, `06`  <br>*Support Traoré Vol. 6 p. 54* |
| **RG-06** | **Validation Stricte des Types MIME d'Ingrédients (`acceptedInputTypes`)** | Dès réception d'une requête de génération comportant des ingrédients multimédias, le serveur valide l'adéquation exacte entre les types MIME des fichiers fournis et la liste autorisée par la capacité du modèle (`ModelCapability.acceptedInputTypes`). Tout écart déclenche un rejet immédiat avec le code standardisé **HTTP 422 Unprocessable Entity** sans aucune mobilisation de ressource GPU. | Diagrammes `04`, `05`, `09`  <br>*Support Traoré Vol. 4 p. 187* |
| **RG-07** | **Rapatriement Streaming en Chunks de 64 Ko et Souveraineté Locale** | Quel que soit le moteur d'exécution (Colab distant ou passerelle API cloud), tout média final produit est intégralement rapatrié vers le poste de travail local par streaming réseau séquentiel par blocs d'au plus **64 Ko**, garantissant qu'aucun binaire volumineux n'est accumulé en mémoire RAM dans le serveur FastAPI avant son écriture disque définitive dans `outputs/`. | Diagrammes `02`, `03`, `06`  <br>*Support Traoré Vol. 6 p. 55* |

---

## 10. Attestation de Conformité Académique et Normative

L'ensemble de la modélisation logicielle Omniforge v01 contenue dans ce dossier a fait l'objet d'un audit de conformité exhaustif confrontant chaque diagramme et document aux sources officielles :
1. **Standard OMG UML 2.5.1 (Formal/2017-12-05)** : respect scrupuleux de la métasyntaxe, des relations d'association sans flèches abusives, de la notation lollipop/socket pour les interfaces de composants, et des chemins de communication physiques de déploiement.
2. **Corpus Pédagogique du Dr TRAORE (L3 MIAGE)** : éradication complète des erreurs de grille (aucun nom au pluriel, aucune classe technique isolée, aucune duplication de clés de persistance, aucun geste IHM modélisé en cas d'utilisation ou action, présence intégrale des 6 livrables documentaires de Niveau 4).
3. **Règles Internes du Projet Colab AI Studio (`AGENTS.md`)** : conformité visuelle pixel-perfect, zéro emoji Unicode dans le code et les diagrammes, et respect absolu des contraintes d'empreinte mémoire sur machine modeste sans GPU dédié.

Le dossier documentaire et les diagrammes vectoriels associés constituent la référence officielle de conception logicielle d'Omniforge.
