# 🎬 Colab AI Studio

> **Transformez un PC modeste en studio de création IA complet (Vidéo, Image, Lip Sync, LLM) grâce à une application locale React moderne, une inférence déportée sur Google Colab et un tunnel sécurisé.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Google Colab](https://img.shields.io/badge/Google_Colab-GPU_T4-F9AB00.svg?logo=googlecolab&logoColor=white)](https://colab.research.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Points Forts

* **Application Locale Réactive & Moderne (React + Vite + Tailwind CSS)** :
  * Développée sous forme de SPA ultra-légère avec primitives accessibles sans style (**Radix UI**) et icônes **Lucide React**.
  * Consommation mémoire minimale (< 50 Mo de RAM en production) taillée sur mesure pour rester fluide même sur un processeur double-cœur et 8 Go de RAM.
  * Aucun serveur Node.js requis en production : le bundle statique optimisé est directement distribué par le serveur FastAPI local.

* **Interface Pilotée par les Schémas d'API (*Schema-Driven UI*)** :
  * **Aucun modèle n'est codé en dur** : Les modèles présentés dans les captures de spécification sont des illustrations de référence. L'interface interroge dynamiquement l'endpoint `/api/models` et s'adapte en temps réel aux capacités déclarées par le worker Colab.
  * **Station de Commande Flottante Adaptative (*Floating Prompt Dock*)** :
    * 🎨 **Mode Image** : Conditionnement par référence visuelle (`Image refs`), ratios personnalisés (8:1 à 2:3), résolutions (1K, 2K, 4K), réglages de qualité et tirages multiples.
    * 🎬 **Mode Vidéo** : Plateau complet de conditionnement temporel (5 fentes : *Start frame*, *End frame*, *Image refs*, *Video refs*, *Audio refs*), durées, cadences d'images (24 à 60 fps) et bascule audio.
    * 🗣️ **Mode Lip Sync** : Synchronisation labiale guidée (visage source + piste vocale), styles d'élocution (*Stable* vs *Expressive*), ratios dédiés (16:9, 9:16, 1:1).
    * 🔍 **Sous-modes Retouche & Upscaling** : Contraction automatique du dock pour les modèles de rehaussement de résolution (Topaz Image & Video Upscale) avec sélection du facteur d'échelle (1.25x à 4x) et de la qualité.
    * 💬 **Mode Chat LLM** : Dès la sélection d'un modèle conversationnel, l'interface bascule en messagerie fluide avec streaming Markdown mot à mot.

* **Passerelle d'API Locale pour LLM** :
  * Expose un endpoint local `http://localhost:8000/v1/chat/completions` (100% compatible standard OpenAI) pour brancher vos modèles Colab dans n'importe quel outil externe (Cursor, Continue, LangChain, scripts Python).

* **Gestionnaire Dynamique de VRAM (*Model Swapper*)** :
  * Permet d'alterner proprement entre de gros modèles vidéo (ex. Wan 2.1, CogVideoX), des modèles d'image (SDXL, Wan 2.5), des modèles de lip-sync et des LLM (Llama 3, Mistral) sur un unique GPU T4 Colab (15 Go VRAM) sans dépassement de mémoire (*Out Of Memory*).

* **Rapatriement Local Automatique & Organisation par Dossiers Physiques Dédiés** :
  * Toutes les créations (vidéos `.mp4`, images `.png`) sont immédiatement transférées et sauvegardées sur votre disque dur local dès la fin du calcul pour éviter toute perte en cas de coupure de Colab.
  * Le gestionnaire de projets et collections `[📁]` permet de visualiser l'arborescence physique réelle et de définir un dossier de destination sur mesure : l'intégralité des médias associés y est alors stockée exclusivement, sans duplication dans le dossier par défaut.
  * Système bi-modal (Google Colab pour l'inférence déportée ou mode Local) configuré à l'installation selon les ressources disponibles.

---

## 🏗️ Architecture du Système

```
[ Machine Locale (PC) ]                           [ Tunnel Public ]                [ Google Colab ]
┌─────────────────────────────────────────┐       ┌──────────────┐          ┌──────────────────────────────┐
│ • Frontend React + Vite + Tailwind      │       │              │          │ • Worker GPU (Nvidia T4)     │
│   (Dock adaptatif, Radix UI, SSE)       │       │              │          │ • Fast Model Swapper (VRAM)  │
│ • Orchestrateur FastAPI local           │◄─────►│  ngrok / CF  │◄────────►│ • Pipelines Vidéo / Image    │
│ • Sauvegarde locale sur disque (outputs)│ HTTP  │    Tunnel    │   HTTP   │ • Modèles Lip sync & LLM     │
│ • Proxy API /v1/chat (OpenAI standard)  │       │              │          │ • Exécution asynchrone       │
└─────────────────────────────────────────┘       └──────────────┘          └──────────────────────────────┘
```

---

## 📚 Spécifications Détaillées du Projet

Le projet dispose d'une documentation technique et ergonomique complète :

* 📑 **[SPECIFICATION.md](SPECIFICATION.md)** : Spécifications fonctionnelles et techniques générales du système hybride (architecture, protocoles de communication, gestion VRAM).
* 🎨 **[UI_SPECIFICATION.md](UI_SPECIFICATION.md)** : Spécification ergonomique complète de l'interface utilisateur React (composants, flux de travail, contrat dynamique TypeScript pour `/api/models`, 24 captures existantes dont le Brand Kit et matrice des 16 captures complémentaires réservées).
* 📐 **[DESIGN_SPECIFICATION.md](DESIGN_SPECIFICATION.md)** : Charte graphique et tokens de Design System extraits des captures (palette chromatique, échelle typographique, espacements 4/8px, configuration `tailwind.config.js` et primitives Radix UI).

---

## 🚀 Démarrage Rapide

> [!NOTE]  
> **État du projet** : Le dépôt est actuellement en phase de cadrage et de modélisation (Phase 1). Les commandes ci-dessous documentent le protocole de déploiement et de lancement prévu pour les phases d'implémentation du code (Phases 2 et 3).

### 1. Sur la Machine Locale (PC) — *(Prévu en Phase 2 & 3)*

#### A. Backend FastAPI *(Phase 2)*
```bash
# 1. Cloner le dépôt
git clone https://github.com/personnal-agent/colab-ai-studio.git
cd colab-ai-studio

# 2. Créer un environnement virtuel Python
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances Python légères
pip install -r requirements.txt
```

#### B. Frontend React (Build de Production) *(Phase 3)*
```bash
# 4. Installer les dépendances et compiler l'interface React
cd frontend
npm install
npm run build
cd ..

# 5. Lancer le studio local
uvicorn app.main:app --reload --port 8000
```
L'interface sera accessible sur `http://localhost:8000`.

*(En développement frontend avec rechargement à chaud HMR, exécutez `npm run dev` dans le dossier `frontend` pour accéder à l'interface sur `http://localhost:5173`).*

---

### 2. Sur Google Colab (Worker GPU)

1. Ouvrez le notebook `colab_worker.ipynb` fourni dans Google Colab.
2. Choisissez un environnement d'exécution **GPU T4** (*Runtime > Change runtime type > T4 GPU*).
3. Renseignez votre token ngrok gratuit (ou utilisez le mode Cloudflare sans token).
4. Exécutez les cellules : une URL publique (ex. `https://xxxx.ngrok-free.app`) s'affiche.
5. Collez cette URL dans l'interface de votre studio local. La connexion est établie !

---

## 📂 Structure du Projet

```
colab-ai-studio/
├── README.md                  # Présentation générale et guide de démarrage
├── SPECIFICATION.md           # Spécifications fonctionnelles globales du système
├── UI_SPECIFICATION.md        # Spécifications détaillées de l'interface React & flux UI/UX
├── DESIGN_SPECIFICATION.md    # Tokens graphiques, typographie, couleurs & configuration Tailwind
├── requirements.txt           # Dépendances Python locales légères (FastAPI, uvicorn, requests)
├── colab_worker.ipynb         # Notebook de calcul GPU à exécuter sur Google Colab
├── ui-specifications/         # Dossier des 24 captures et maquettes de référence
├── data/                      # Base documentaire JSON (generations, brand_kits, projects, config)
├── frontend/                  # Application Monopage (SPA) React + Vite (Phase 3)
│   ├── src/
│   │   ├── components/        # Composants (FloatingPromptDock, MediaGrid, Popovers)
│   │   ├── hooks/             # Abonnements SSE (useTaskProgress) et statut Colab
│   │   ├── stores/            # Gestion d'état local réactive (studioStore)
│   │   └── types/api.ts       # Contrat d'interface TypeScript (/api/models, Tasks)
│   ├── package.json           # Dépendances React, Vite, Radix UI, Lucide
│   └── tailwind.config.js     # Thème personnalisé et tokens de design
├── app/                       # Orchestrateur local FastAPI (Phase 2)
│   ├── main.py                # Point d'entrée de l'API locale et distribution statique
│   ├── config.py              # Configuration du tunnel et gestionnaire de persistance JSON
│   ├── api/                   # Endpoints (/api/models, /api/generate, /v1/chat)
│   └── services/              # Client asynchrone Colab & rapatriement automatique
└── outputs/                   # Dossier de sauvegarde locale sécurisée des médias générés
```

---

## 📄 Licence

Ce projet est distribué sous licence [MIT](LICENSE).
