# 🎬 Colab AI Studio

> **Transformez un PC modeste en studio de création IA complet (Vidéo, Image, LLM) grâce à l'inférence déportée sur Google Colab et un tunnel ngrok.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Google Colab](https://img.shields.io/badge/Google_Colab-GPU_T4-F9AB00.svg?logo=googlecolab&logoColor=white)](https://colab.research.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🌟 Points Forts

* **Interface Adaptative en temps réel** :
  * 🎨 **Mode Studio Image & Vidéo** : Barre de prompt avancée avec contrôles complets (*Start frame*, *End frame*, *Image/Video/Audio refs*, ratios d'aspect, résolution 1080p, durées, commutateurs d'amélioration).
  * 💬 **Mode Chat LLM** : Dès la sélection d'un modèle textuel, les contrôles vidéo s'effacent au profit d'un chat conversationnel fluide avec streaming de tokens.
* **Passerelle d'API Locale pour LLM** :
  * Expose un endpoint local `http://localhost:8000/v1/chat/completions` (100% compatible standard OpenAI) pour brancher vos modèles Colab dans n'importe quel outil externe (Cursor, Continue, LangChain, scripts Python).
* **Gestionnaire Dynamique de VRAM (*Model Swapper*)** :
  * Permet d'alterner proprement entre de gros modèles vidéo (ex. Wan 2.1, CogVideoX), des modèles d'image (SDXL, Wan 2.5) et des LLM (Llama 3, Mistral) sur un unique GPU T4 Colab (15 Go VRAM) sans dépassement de mémoire (*Out Of Memory*).
* **Rapatriement Local Automatique** :
  * Toutes les créations (vidéos `.mp4`, images `.png`) sont immédiatement transférées et sauvegardées sur votre disque dur local dès la fin du calcul, pour ne rien perdre en cas de coupure de Colab.
* **Ultra-Léger pour le PC** :
  * Développé pour tourner avec fluidité même sur un processeur double-cœur et moins de 100 Mo de RAM.

---

## 🏗️ Architecture du Système

```
[ Ton PC Local ]                          [ Tunnel Public ]                [ Google Colab ]
┌──────────────────────────────┐          ┌──────────────┐          ┌──────────────────────────────┐
│ • IHM Studio & Chat          │          │              │          │ • Worker GPU (Nvidia T4)     │
│ • Orchestrateur FastAPI      │ ◄──────► │ ngrok / CF   │ ◄──────► │ • Fast Model Swapper (VRAM)  │
│ • Sauvegarde locale (outputs)│   HTTP   │    Tunnel    │   HTTP   │ • Pipelines Diffusers / LLM  │
│ • Proxy API /v1/chat         │          │              │          │ • Exécution asynchrone       │
└──────────────────────────────┘          └──────────────┘          └──────────────────────────────┘
```

Pour les spécifications complètes et détaillées, consultez le fichier [SPECIFICATION.md](SPECIFICATION.md).

---

## 🚀 Démarrage Rapide

### 1. Sur la Machine Locale (PC)

```bash
# 1. Cloner le dépôt
git clone https://github.com/personnal-agent/colab-ai-studio.git
cd colab-ai-studio

# 2. Créer un environnement virtuel Python
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances légères
pip install -r requirements.txt

# 4. Lancer le studio local
uvicorn app.main:app --reload --port 8000
```
L'interface est accessible immédiatement sur `http://localhost:8000`.

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
├── SPECIFICATION.md       # Spécifications fonctionnelles et techniques complètes
├── README.md              # Documentation du projet
├── .gitignore             # Fichiers ignorés par Git
├── requirements.txt       # Dépendances locales légères (FastAPI, uvicorn, requests, etc.)
├── colab_worker.ipynb     # Notebook à exécuter sur Google Colab
├── app/
│   ├── main.py            # Point d'entrée du serveur FastAPI local
│   ├── config.py          # Paramètres et état de la connexion
│   ├── api/               # Routes API (proxy, tâches, modèles)
│   ├── services/          # Client de synchronisation avec Colab & téléchargement
│   └── static/            # Interface web (HTML5, Tailwind, JS réactif)
└── outputs/               # Dossier de sauvegarde automatique des médias générés
```

---

## 📄 Licence

Ce projet est distribué sous licence [MIT](LICENSE).
