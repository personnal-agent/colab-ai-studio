# Spécifications Fonctionnelles & Techniques — Colab AI Studio

## 1. Vision du Projet

**Colab AI Studio** est un système hybride conçu pour transformer une machine locale modeste (ex. Intel Core i5, 8 Go de RAM, pas de GPU dédié) en une station de travail IA avancée, en déportant l'ensemble des calculs lourds (inférence vidéo, image et LLM) sur le GPU distant de Google Colab via un tunnel sécurisé (**ngrok** ou **Cloudflare Tunnels**).

Le système se compose de trois éléments majeurs :
1. **Un backend local ultra-léger (FastAPI)** : Consommation mémoire minimale (< 80 Mo de RAM), servant de tour de contrôle, d'orchestrateur de tâches, de cache local de médias et de proxy API.
2. **Une interface web studio adaptative** : Une IHM moderne qui s'adapte en temps réel selon le type de modèle sélectionné (Mode Studio Vidéo/Image vs Mode Chat LLM).
3. **Un worker GPU distant (Google Colab)** : Un serveur de calcul capable de gérer l'allocation VRAM dynamique (*Model Swapper*) pour faire cohabiter modèles vidéo/image et modèles de langage au sein d'une même session GPU.

---

## 2. Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               MACHINE LOCALE (PC)                               │
│                                                                                 │
│   ┌───────────────────────────┐         ┌───────────────────────────────────┐   │
│   │     Interface Web (UI)    │ <=====> │      Backend Local (FastAPI)      │   │
│   │                           │  HTTP   │                                   │   │
│   │  • Mode Studio Vidéo/Image│   SSE   │  • Gestionnaire d'état & configs  │   │
│   │  • Mode Chat LLM          │         │  • Rapatriement auto des médias   │   │
│   │  • Sélecteur de modèles   │         │  • Proxy API OpenAI standard      │   │
│   └───────────────────────────┘         └─────────────────┬─────────────────┘   │
└───────────────────────────────────────────────────────────┼─────────────────────┘
                                                            │ Requêtes HTTP /
                                                            │ Tunnel ngrok
                                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             INFRASTRUCTURE DISTANTE                             │
│                                                                                 │
│                       ┌───────────────────────────────┐                         │
│                       │   Relais Public ngrok / CF    │                         │
│                       └───────────────┬───────────────┘                         │
│                                       │                                         │
│                                       ▼                                         │
│                       ┌───────────────────────────────┐                         │
│                       │   Google Colab (Worker GPU)   │                         │
│                       │                               │                         │
│                       │  • Serveur FastAPI distant    │                         │
│                       │  • Gestionnaire VRAM (Swap)   │                         │
│                       │  • Pipeline Vidéo (Wan/Cog)   │                         │
│                       │  • Pipeline Image (SDXL/Flux) │                         │
│                       │  • Moteur LLM (Transformers)  │                         │
│                       └───────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Spécifications de l'Interface Utilisateur (UI/UX)

L'interface bascule dynamiquement selon la nature du modèle actif sélectionné dans la barre d'outils.

### 3.1. Mode Studio Vidéo & Image

Inspiré des plateformes professionnelles de génération générative (type Wan 2.5 / CogVideoX / Runway) :

* **Barre d'outils supérieure d'actions rapides** :
  * `Start frame` : Téléversement d'une image de début pour l'interpolation.
  * `End frame` : Téléversement d'une image de fin pour guider la trajectoire vidéo.
  * `Image refs` : Injection d'une ou plusieurs images de référence (IP-Adapter / conditionnement visuel).
  * `Video refs` : Référence de mouvement ou style vidéo.
  * `Audio refs` : Piste audio de synchronisation si applicable.
* **Zone de saisie principale** :
  * Zone de texte riche pour la description du prompt avec autocomplétion des déclencheurs (`@...`).
* **Barre de réglages inférieurs (Pill Controls)** :
  * **Sélecteur de modèle** : Badge dynamique (ex. `Wan 2.5 Image`, `Wan 2.1 Video`, `CogVideoX-2B`, `SDXL-Turbo`).
  * **Aspect Ratio** : Menu déroulant rapide (`16:9`, `9:16`, `1:1`, `4:3`, `21:9`).
  * **Résolution** : Choix rapide (`720p`, `1080p`).
  * **Durée** : Sélection de la temporalité (`3s`, `5s`, `10s`).
  * **Audio** : Commutateur `On` / `Off`.
  * **Batch** : Nombre d'itérations simultanées.
  * **Enhancement** : Activer/désactiver l'optimisation automatique du prompt.
  * **Bouton d'envoi** : Déclencheur avec état actif/inactif selon la connexion au worker.
* **Suivi de génération & Galerie** :
  * Barre de progression en temps réel (pourcentage, étape en cours, temps estimé restant).
  * Galerie locale intégrant un lecteur vidéo HTML5 avec prévisualisation immédiate et téléchargement en un clic.

### 3.2. Mode Chat LLM & Passerelle API

Dès qu'un modèle de langage est sélectionné (ex. `Llama-3-8B`, `Mistral-7B`, `Qwen-2.5-7B`) :

* **Masquage complet des contrôles vidéo/image** : L'interface se reconfigure instantanément en vue de messagerie conversationnelle.
* **Fenêtre de Chat interactive** :
  * Historique des échanges, rendu Markdown complet, coloration syntaxique des blocs de code.
  * Streaming mot à mot des réponses (*Server-Sent Events*).
  * Contrôle des hyperparamètres (Temperature, Top-P, System Prompt).
* **Bandeau d'Information d'Endpoint API (Intégration externe)** :
  * Affichage clair de l'URL locale d'inférence :  
    `http://localhost:8000/v1/chat/completions`
  * Format 100% compatible avec l'API OpenAI.
  * Exemples d'intégration prêts à copier pour intégrer ce LLM dans Cursor, Continue.dev, scripts Python (`openai.OpenAI(base_url=...)`), ou requêtes cURL.

---

## 4. Spécifications du Backend Local (FastAPI)

Le backend est conçu pour être minimaliste, asynchrone et résistant aux coupures.

### 4.1. Responsabilités
1. **Orchestration des requêtes** : Faire l'interface entre l'IHM et l'URL ngrok du Colab distant.
2. **Surveillance de la connexion** : Ping périodique du serveur distant pour vérifier la disponibilité de la session GPU.
3. **Persistance & Rapatriement automatique** :
   * Dès qu'une vidéo ou image est générée sur Colab, le backend local télécharge immédiatement le binaire dans le dossier local `outputs/` et enregistre les métadonnées dans SQLite.
   * Prévient toute perte de données en cas de déconnexion inopinée de Colab.
4. **Proxy API LLM** : Exposition de la route `/v1/chat/completions` pour permettre à d'autres logiciels du PC d'exploiter le GPU Colab.

### 4.2. Endpoints Locaux Principaux
* `GET /api/health` : État du backend et de la liaison Colab.
* `POST /api/config/colab-url` : Mise à jour de l'URL publique ngrok active.
* `GET /api/models` : Liste des modèles disponibles (classés par catégorie : `video`, `image`, `llm`).
* `POST /api/models/switch` : Ordre de changement de modèle envoyé à Colab.
* `POST /api/generate/media` : Lancement d'une tâche de génération vidéo/image.
* `GET /api/tasks/{task_id}/status` : Polling ou flux SSE de progression.
* `GET /api/gallery` : Liste des créations archivées localement.
* `POST /v1/chat/completions` : Endpoint d'API LLM compatible OpenAI.

---

## 5. Spécifications du Worker Distant (Google Colab)

### 5.1. Gestion Dynamique de la VRAM (*Model Swapper*)
Comme le GPU Colab gratuit (Nvidia T4 - 15-16 Go VRAM) ne peut pas héberger simultanément un modèle vidéo et un LLM :
* **Protocole d'éviction mémoire** :
  ```python
  def unload_current_model():
      global active_model, active_pipeline
      if active_pipeline is not None:
          del active_pipeline
          active_pipeline = None
      if active_model is not None:
          del active_model
          active_model = None
      gc.collect()
      torch.cuda.empty_cache()
      torch.cuda.ipc_collect()
  ```
* **Chargement à la demande** :
  * Le worker charge uniquement les poids nécessaires pour la tâche courante.
  * Notification de progression du chargement vers le backend local.

### 5.2. Asynchronisme & Prévention des Timeouts
* La génération de vidéos pouvant nécessiter plusieurs minutes, l'exécution s'effectue dans un thread d'arrière-plan avec génération d'un identifiant de tâche (`task_id`).
* Des callbacks de progression (étape $N$ sur $Total$) mettent à jour l'état de la tâche, consultable à tout moment par l'orchestrateur local.

---

## 6. Plan d'Implémentation & Jalons

* **Phase 1 : Socle & Spécifications**
  * Architecture, README, spécifications, initialisation Git & publication GitHub.
* **Phase 2 : Backend Local & IHM Réactive**
  * Serveur FastAPI local avec stockage SQLite.
  * Interface HTML/Tailwind dynamique (bascule automatique Studio Vidéo vs Chat LLM).
* **Phase 3 : Worker Colab & Gestionnaire VRAM**
  * Script / Notebook Colab prêt à l'emploi.
  * Serveur d'inférence avec swapper VRAM et tunnel ngrok.
* **Phase 4 : Intégration de Bout en Bout & Tests**
  * Validation des générations d'images/vidéos avec rapatriement local.
  * Validation du streaming LLM et de la passerelle d'API locale.
