# Spécification Fonctionnelle & Ergonomique de l'Interface Utilisateur (UI/UX) — Omniforge

> **Statut documentaire — cible à implémenter.** Les documents numérotés décrivent l'évolution Omniforge ; ils ne prouvent pas sa disponibilité. Le code actuel accepte seulement `colab` et `local` via le contrat worker (`/infer`, `/tasks/{task_id}/status`, `/tasks/{task_id}/cancel`, `/files/{path}`). OAuth Colab automatique, TPU/LRU, ComfyUI direct, mode API, catalogue hors-ligne, LoRAs, audio/3D et validation `acceptedInputTypes` restent des objectifs. Voir [SPECIFICATION01.md](SPECIFICATION01.md#4-spécifications-des-3-moteurs-dexécution-colab--local--api) pour les écarts avec l'existant.

---

**Catalogue cible** : le sélecteur lit uniquement `data/models.json` ; scans Local et imports custom y écrivent via `JSONDocumentStore`. Les signatures de `known_models_catalog.json` servent de gabarits en lecture seule. Voir le contrat détaillé dans [SPECIFICATION01.md](SPECIFICATION01.md).

## 1. Vision & Principes Ergonomiques Directeurs

- **Fidélité Visuelle Trait pour Trait aux Maquettes (`ui-specifications/`)** :
  - L'interface DOIT reproduire à l'identique la géométrie, les espacements, les nuances de gris (`#F9FAFB`, `#EFEFEF`, `#EAECEF`, `#FFFFFF` translucide `backdrop-blur-xl`) et les composants des 24 captures de référence dans [`ui-specifications/`](./ui-specifications/).
  - **Zéro Emoji Clavier / Unicode dans l'UI** : Les emojis utilisés dans les schémas ASCII de ce document ont une valeur purement illustrative. Dans le code React (`frontend/src/`), **aucun emoji Unicode n'est toléré** : chaque icône est un tracé vectoriel SVG filaire (`stroke-width: 1.5` / `1.75`).
- **Habillage Décoratif Dès le Premier Lancement (*Zero Bare Empty State*)** :
  - Au démarrage de l'application (lorsqu'aucune génération personnelle n'existe encore) ou dans la vue `Explore`, l'interface n'affiche **jamais** une page vide ou un cadre en pointillés.
  - Elle présente immédiatement :
    1. Les **2 cartes bannières décoratives d'en-tête** (`Avatars — Keep characters consistent [View all]` et `Brand kit — Add logos, colors, fonts and assets to keep generations on-brand [Create new]`) illustrées par leurs vignettes photographiques/graphiques à droite (`ui-spec_image_model-selector.png`).
    2. Les **7 cartes illustratives de référence** sur fond `#EFEFEF` (`Image generated`, `Video generated`, `Audio generated`, `Upscaled image [4K]`, `Upscaled video [4K]`, `Lip sync`, plus `3D generated` dans la cible Omniforge, comme sur `ui-spec-page.jpg`) accompagnées d'une **galerie de créations décoratives haute esthétique** (portraits éditoriaux, affiches typographiques, visuels produits, scènes 3D, comme sur `ui-spec_image_model-selector.png` et `Brand01.png`).
    3. Les **puces d'inspiration de prompt** (`Surreal Dreamscape`, `Cyberpunk Alleyway`, `Enchanted Forest`) au-dessus du dock (`ui-spec_image_aspect-ratio.png`).
- **Switch Global `[ Studio | Agents ]`** : Commutateur segmenté sobre en barre supérieure permettant de basculer entre `Studio` et `Agents` (sans sous-écran superflu côté Studio).
- **Orchestration 100 % Backend des 3 Moteurs (`Colab` | `Local` | `API`)** :
  - **Google Colab (GPU & TPU)** : Connexion directe au **compte Google** (OAuth) depuis le popover `[👤]`. Le backend orchestre **automatiquement** l'allocation du runtime Colab (**GPU** : `T4 16 Go`, `L4 24 Go`, `A100 40/80 Go` ; **TPU** : `TPU v5e`, `TPU v6e`, `TPU v2-8` selon la capacité disponible sur le compte Google AI Pro) et le pont réseau chiffré — **dans ce parcours automatique, l'utilisateur n'a pas à lancer `ngrok` ni à copier-coller une URL ou un secret**.
    - **Accès automatique conditionnel** : projet autorisé sur l’allowlist de l’API Colab bêta, service `colaboratory.googleapis.com` activé et consentement OAuth `https://www.googleapis.com/auth/colaboratory`. Vérifier `runtimespecs.list` et `eligible: true` avant de proposer un accélérateur ; l’abonnement seul ne garantit pas GPU/TPU. Le backend renouvelle le proxy-token éphémère via `runtimes.get` avant `expireTime`, sans le montrer ni le journaliser. En cas d’accès refusé, de quota/accélérateur indisponible ou d’échec de renouvellement, afficher la cause et proposer le Colab manuel uniquement si l’URL `colab.tunnelUrl` et le secret effectif (`colab.secret` ou repli `COLAB_STUDIO_SECRET`) sont déjà configurés et le worker joignable ; sinon proposer uniquement le worker Local déjà configuré et joignable. Si aucun repli n’est prêt, afficher « Configuration requise » sans lancer de génération ni inventer un parcours de configuration automatique. Aucun basculement silencieux. Voir [SPECIFICATION01.md §4.1](SPECIFICATION01.md) pour le contrat et les sources API officielles.
  - **Local (PC)** : Exécution en arrière-plan via **ComfyUI Headless API (`:8188`)** sans jamais exposer le graphe de nœuds.
  - **API** : Exécution via les clés API configurées par l'utilisateur.
- **Catalogue de Modèles Personnalisable & Disponible Hors-Ligne — cible non implémentée** :
  - La liste des modèles n'est **jamais codée en dur** dans le code Python : elle est stockée dans `data/models.json` sur le PC local, reste consultable même lorsque Colab est déconnecté, et permet à l'utilisateur d'**ajouter ou retirer librement ses propres modèles** (Hugging Face `repo_id` / Safetensors pour Colab, modèles connus auto-détectés ou workflows `.api.json` mappés pour Local, ou endpoints API).

---

## 2. Disposition Spatiale de l'Écran (Layout Global — Conforme à `ui-spec-page.jpg` & `ui-spec_image_model-selector.png`)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [◧] Image & Video                    [ Studio | Agents ]                  [▶ Ask]  [📁]  [🔔]  [👤] │
│     Explore   History                                                                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────────────┐ │
│ │ Avatars                        [Visuels déco]│  │ Brand kit                      [Visuels déco]│ │
│ │ Keep characters consistent        [View all] │  │ Add logos, colors, fonts...     [Create new] │ │
│ └──────────────────────────────────────────────┘  └──────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 Search images, videos, audio, lip syncs, and 3D                                             │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ [ + Image ]  [ + Video ]  [ + Audio ]  [ + Lip sync ]  [ + 3D ]                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ GRILLE DE LA GALERIE (CRÉATIONS UTILISATEUR + CARTES DÉCORATIVES AU PREMIER LANCEMENT) :           │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌─────────────────────┐ │
│ │      [SVG Image]     │ │      [SVG Video]     │ │      [SVG Audio]     │ │              [4K]   │ │
│ │   Image generated    │ │   Video generated    │ │   Audio generated    │ │   Upscaled image    │ │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘ └─────────────────────┘ │
│                                                                                                    │
│            ┌──────────────────────────────────────────────────────────────────────────┐            │
│            │ [≡+ Surreal Dreamscape]  [≡+ Cyberpunk Alleyway]  [≡+ Enchanted Forest]  │            │
│            │ ┌────────────────────────────────────────────────────┐   [@ Brand Kit]   │            │
│            │ │ [Image] [Video] [Audio] [Lip sync] [Upscaling] [3D]│                   │            │
│            │ └────────────────────────────────────────────────────┘                   │            │
│            │ [Start frame]  [End frame]  [Image refs]  [Video refs]  [Audio refs]     │            │
│            │ Describe your video or reference by using @...                           │            │
│            │ 🎞 Seedance 2.5   🧩 LoRA   ▭ 16:9   ⤢ 720p   ◷ 5s   🔊 On   ⬦ 1   ✦ On   [52 left] [↑]│
│            └──────────────────────────────────────────────────────────────────────────┘            │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Barre Supérieure, Navigation & Bannières Décoratives

*Captures de référence :* [`ui-spec-page.jpg`](./ui-specifications/ui-spec-page.jpg), [`ui-spec_image_model-selector.png`](./ui-specifications/ui-spec_image_model-selector.png)

### 3.1. Bloc Gauche & Sous-Navigation
- **Bouton Volet / Favoris (`PanelLeft` / `Star` SVG)** : Icône carrée à bords arrondis (`w-8 h-8`) à gauche du titre `Image & Video`.
- **Titre `Image & Video`** : Typographie `20px`/`24px` (`font-semibold text-[#111827]`).
- **Onglets de Sous-Navigation `Explore` | `History`** :
  - **`Explore`** : Affiche les bannières décoratives (`Avatars`, `Brand kit`), les créations de démonstration décoratives et les cartes illustratives des pôles lorsque l'utilisateur débute ou explore les capacités du studio.
  - **`History`** : Filtre la galerie uniquement sur l'historique personnel des générations enregistrées dans `data/generations.json` (avec filtre favoris).
- **Switch Global `[ Studio | Agents ]`** : Commutateur segmenté sur piste `#EFEFEF` avec segment actif blanc `#FFFFFF` ombré.

### 3.2. Bannières Décoratives d'Accès Rapide (`Avatars` & `Brand kit`)
Présentes en haut de la vue `Explore` (`ui-spec_image_model-selector.png`, `ui-spec_video_model-selector.png`) :
1. **Carte `Avatars`** :
   - Titre `Avatars`, sous-titre `Keep characters consistent`, bouton pilule blanc bordé `[ View all ]`, et illustrations de portraits cohérents sur la moitié droite.
2. **Carte `Brand kit`** :
   - Titre `Brand kit`, sous-titre `Add logos, colors, fonts and assets to keep generations on-brand`, bouton pilule blanc bordé `[ Create new ]` (ouvre directement la modale de création Brand Kit `Brand02.png`), et collage visuel décoratif (packaging, nuancier, logo `NITRO`) sur la moitié droite.

### 3.3. Bloc Droit (Aide, Projets, Notifications, Compte & Moteur)
- **Bouton Pilule `[▶ Ask]`** : Pilule bordée `bg-white border-[#E5E7EB]` avec icône triangle/play multicolore SVG + texte `Ask`.
- **Bouton Projets & Dossiers (`Folder` SVG)** : Bouton icône `w-9 h-9 rounded-full border border-[#E5E7EB] bg-white`. Gère les projets (`outputs/projects/<id>/` ou chemin isolé `storagePath`).
- **Bouton Notifications (`Bell` SVG)** : Bouton icône `w-9 h-9 rounded-full border border-[#E5E7EB] bg-white` avec pastille bleue (`#2563EB`) en cas de notification active.
- **Avatar Compte & Sélecteur de Moteur (`[👤]`)** :
  - Cercle avatar (`w-9 h-9 rounded-full`) avec anneau de statut. Un clic ouvre le popover de pilotage du moteur (`Colab` | `Local` | `API`) :
    1. **Onglet `Colab` (Connexion Compte Google, Choix GPU / TPU & Orchestration Automatique)** :
       - **Aucun champ d'URL ngrok/Cloudflare ni de `worker_secret` manuel**.
       - Si non connecté : bouton **`[ Se connecter avec Google ]`** (flux OAuth2 Google / Colab géré par le backend).
       - Si connecté : affiche la photo et l'email du compte Google, le palier détecté (`Free` / `Colab Pro` / `Google AI Pro`), le solde d'**unités de calcul (*Compute Units*)**, le **sélecteur d'accélérateur cible (GPU & TPU)** (`Auto — Meilleur dispo`, `GPU : NVIDIA A100 40/80 Go`, `GPU : NVIDIA L4 24 Go`, `GPU : Tesla T4 16 Go`, `TPU : Google TPU v5e / v6e`, `TPU : TPU v2-8 64 Go HBM` selon les capacités réelles du compte), la **vraie capacité mémoire VRAM (GPU) ou HBM (TPU) détectée dynamiquement** (ex. `8.4 Go / 40.0 Go VRAM — A100` ou `12.0 Go / 64.0 Go HBM — TPU v5e`), le temps de session et un bouton `Démarrer / Arrêter le Runtime`.
    2. **Onglet `Local` (ComfyUI Headless `:8188`)** :
       - État du moteur ComfyUI en tâche de fond (`Running` / `Stopped`), bouton `Start / Stop`, chemin local `comfyRootPath`, jauge VRAM réelle du GPU PC, bouton `Purger VRAM` et bouton `Scanner les modèles locaux`.
    3. **Onglet `API`** :
       - Gestion sécurisée des clés API des fournisseurs externes.

---

## 4. Barre de Recherche & Puces de Filtrage Rapide

*Captures de référence :* [`ui-spec-page.jpg`](./ui-specifications/ui-spec-page.jpg), [`ui-spec_image_aspect-ratio.png`](./ui-specifications/ui-spec_image_aspect-ratio.png)

- **Champ de Recherche Pleine Largeur** : Conteneur `h-11 w-full rounded-xl border border-[#E5E7EB] bg-white px-3.5 flex items-center gap-2.5` avec icône loupe SVG (`#9CA3AF`) et placeholder `Search images, videos, and lip syncs` (`text-sm text-[#6B7280]`).
- **Rangée de Puces de Filtrage Sous la Recherche** :
  - Placées **sur une ligne dédiée juste en dessous du champ de recherche**, alignées à gauche (`flex items-center gap-2 mt-2.5`).
  - Pilules compactes : `+ Image`, `+ Video`, `+ Audio`, `+ Lip sync`, `+ 3D` (`h-7 px-2.5 rounded-lg border border-[#E5E7EB] bg-white text-xs font-medium text-[#374151] hover:bg-[#F3F4F6]`).

---

## 5. Grille de la Galerie, Cartes Décoratives Initiales & Types de Médias

*Captures de référence :* [`ui-spec-page.jpg`](./ui-specifications/ui-spec-page.jpg), [`ui-spec_image_model-selector.png`](./ui-specifications/ui-spec_image_model-selector.png), [`Brand01.png`](./ui-specifications/Brand01.png)

### 5.1. État Initial & Galerie Décorative (*Zero Bare Empty State*)
Lorsque l'application démarre sans génération utilisateur (ou dans l'onglet `Explore`), la grille affiche deux strates complémentaires :
1. **Cartes Illustratives des Pôles sur Fond `#EFEFEF`** (exactement comme sur `ui-spec-page.jpg`) :
   - Cartes rectangulaires `rounded-2xl bg-[#EFEFEF] border border-black/[0.04] aspect-[16/10]` centrant une grande icône vectorielle SVG en gris anthracite (`#4B5563`, `stroke-width: 1.75`) et son libellé (`15px font-medium text-[#111827]`) :
     - `Image generated` (icône cadre montagne/soleil)
     - `Video generated` (icône cercle lecture)
     - `Audio generated` (icône barres d'onde acoustique verticales)
     - `Upscaled image` (icône double flèche diagonale d'agrandissement + badge d'angle supérieur droit `[4K]` bordé `#374151`)
     - `Upscaled video` (icône cercle lecture + badge d'angle supérieur droit `[4K]`)
     - `Lip sync` (icône lèvres parlantes avec ondes sonores latérales)
     - `3D generated` (icône cube isométrique vectoriel + badge `[GLB]`)
2. **Créations Décoratives d'Inspiration (*Showcase Cards*)** (comme sur `ui-spec_image_model-selector.png` et `Brand01.png`) :
   - Cartes visuelles haute définition pré-embarquées illustrant la qualité studio (portrait triptyque éditorial, affiche gouttes de pluie `-20% OFF`, photographie macro beauté `UMBERLY`, carte menu illustrée `ESPRESSO & BREW`, rendu produit 3D).
   - Cliquer sur une carte décorative permet d'inspecter son prompt et ses paramètres et de cliquer sur **`Remix`** pour pré-remplir immédiatement le *Floating Prompt Dock*.

### 5.2. Comportement des Cartes Générées
- Aperçu HD, lecture vidéo muette au survol, lecteur d'onde sonore pour l'audio, rotation interactive pour la 3D, bouton favori SVG et ouverture de la modale d'inspection plein format avec bouton **Remix** et export local (`storagePath`, `outputs/projects/<id>/` ou `outputs/YYYY-MM-DD/`).

---

## 6. Station de Commande Flottante (*Floating Prompt Dock*)

*Captures de référence :* [`ui-spec_video.png`](./ui-specifications/ui-spec_video.png), [`ui-spec_image.png`](./ui-specifications/ui-spec_image.png), [`ui-spec_lip-sync.png`](./ui-specifications/ui-spec_lip-sync.png), [`ui-spec_image_aspect-ratio.png`](./ui-specifications/ui-spec_image_aspect-ratio.png)

### 6.1. Puces d'Inspiration de Prompt (Au-dessus des Onglets)
- Lorsque la zone de prompt est vide et reçoit le focus (comme sur `ui-spec_image_aspect-ratio.png`), une rangée horizontale de puces de suggestions apparaît en haut du dock :
  - Pilules `h-8 px-3 rounded-full bg-white border border-[#E5E7EB] text-xs font-medium text-[#111827] flex items-center gap-1.5 shadow-sm` avec l'icône SVG `ListSparkles` (`≡+`) : ex. `Surreal Dreamscape`, `Cyberpunk Alleyway`, `Enchanted Forest`.

### 6.2. Rail des 6 Onglets de Catégorie & Bouton `@ Brand Kit`
- **Rail d'Onglets (`TabsList`)** :
  - Piste gris très doux `bg-[#EFEFEF] p-1 rounded-[14px] inline-flex items-center gap-0.5`.
  - 6 onglets : `Image`, `Video`, `Audio`, `Lip sync`, `Upscaling`, `3D Gen`.
  - **Onglet actif** : pilule blanche `bg-white text-[#111827] font-semibold shadow-sm rounded-[10px] px-3.5 py-1.5 text-[13px]`.
  - **Onglet inactif** : `bg-transparent text-[#6B7280] hover:text-[#111827] font-medium px-3.5 py-1.5 text-[13px]`.
- **Bloc Droit de l'En-tête du Dock** :
  - Conteneur `bg-[#F4F4F5] p-1 rounded-[14px] inline-flex items-center gap-1` accueillant :
    - La pilule blanche **`@ Brand Kit`** (`bg-white border border-[#E5E7EB] rounded-[10px] px-3 py-1 text-xs font-semibold text-[#111827] flex items-center gap-1.5`).
    - Le bouton carré d'options/suggestions (`w-7 h-7 rounded-[10px] bg-white border border-[#E5E7EB] flex items-center justify-center` avec icône `×` ou `ListSparkles` `≡+` selon l'état, exactement comme sur `ui-spec_image.png` et `Brand01.png`).

### 6.3. Fentes de Conditionnement (`ReferenceSlot`) & Validation Stricte des Formats
- **Style visuel exact (`ui-spec_video.png`)** :
  - Tuiles rectangulaires `w-[104px] h-[74px] rounded-2xl bg-[#EFEFEF] hover:bg-[#E6E6E8] transition-colors flex flex-col items-center justify-center gap-1.5 cursor-pointer`.
  - Icône SVG centrale (`w-[18px] h-[18px] text-[#4B5563] stroke-[1.6]`) au-dessus du libellé (`text-[12px] font-medium text-[#4B5563]`).
- **Fentes par mode** :
  - `Video` : `Start frame`, `End frame`, `Image refs`, `Video refs`, `Audio refs`.
  - `Image` : `Image refs`.
  - `Audio` : `Audio refs` (timbre à cloner / audio source), `Video refs` (vidéo à sonoriser pour Video-to-SFX / Foley).
  - `Lip sync` : `Face ref` (image/vidéo portrait), `Audio ref` (voix).
  - `Upscaling` : fente média source (image ou vidéo).
  - `3D Gen` : `Image refs` (1 à 4 vues d'un objet), `Mesh ref` (`.glb`, `.obj`, `.fbx` à rigger/animer).
- **Blocage automatique des fichiers incompatibles (`acceptedInputTypes`)** : **contrat cible à implémenter** : `acceptedInputTypes` accepte des classes (`image`, `video`, `audio`, `mesh`), des MIME exacts (`image/png`) ou génériques (`image/*`), et des extensions (`.glb`, `.obj`, `.fbx`). Normaliser casse, espaces et extension (point initial), puis comparer MIME et extension à une table partagée de formats connus. Si `File.type` est vide ou générique, résoudre le type par l'extension ; ne pas rejeter un `.glb` valide pour son seul MIME vide. Une classe correspond aux formats connus de cette classe ; un MIME générique ne couvre que son préfixe. Si aucun critère ne correspond, refuser le dépôt avec une explication. Le serveur doit vérifier le type réel et les capacités avant soumission (422 prévu), sans faire confiance au MIME client.

### 6.4. Rangée Inférieure de Pilules Sans Bordure (*Ghost Parameter Pills*)
Comme visible sur `ui-spec_video.png`, `ui-spec_image.png` et `ui-spec_image_resolution.png` :
- **Style au repos** : **aucune bordure** (`bg-transparent border-transparent text-[#4B5563] hover:bg-[#F3F4F6] hover:text-[#111827] h-8 px-2.5 rounded-lg text-[13px] font-medium inline-flex items-center gap-1.5`).
- **Style ouvert / actif** : fond gris doux `bg-[#EAECEF] text-[#111827] font-semibold rounded-lg` (voir pilule `1K` ouverte dans `ui-spec_image_resolution.png` ou `2:3` dans `ui-spec_image_aspect-ratio.png`).
- **Icônes SVG exactes par pilule (Zéro Emoji)** :
  - **Modèle (`ModelSelectorPopover`)** : icône `Film` (pellicule) en Vidéo, `Image` (cadre paysage) en Image, `AudioWaveform` en Audio, `UserSparkles` en Lip sync, `Box` en 3D + nom du modèle.
  - **LoRA (`LoraPillControl`)** : icône `Layers2` / `Puzzle` SVG + `LoRA` (ou `LoRA · N` quand $N$ LoRAs sont activés). Affichée uniquement si `capabilities.supportsLora === true`.
  - **Format (`AspectRatioControl`)** : icône rectangle proportionnel SVG + ratio (`16:9`, `2:3`, `9:16`, `1:1`, etc.).
  - **Résolution (`ResolutionControl`)** : icône cadre d'agrandissement à coins pointillés SVG + résolution (`720p`, `1080p`, `1K`, `2K`, `4K`).
  - **Qualité (`QualityControl`)** : icône étiquette losange (`Tag` SVG) + qualité (`High`, `Fast`, `Precise`).
  - **Durée (`DurationControl`)** : icône horloge (`Clock` SVG) + durée (`5s`, `10s`, ou curseur `range`).
  - **Audio Natif (`AudioToggleControl`)** : icône haut-parleur (`Volume2` SVG) + `On` / `Off`.
  - **Style d'Élocution (`TalkingStyleControl`)** : icône onde d'antenne (`Radio` SVG) + `Stable` / `Expressive`.
  - **Tirages Parallèles (`GenerationsCountControl`)** : icône losanges superposés (`Layers` SVG) + `1` à `4`.
  - **Amélioration de Prompt (`PromptEnhanceControl`)** : icône baguette étoilée (`WandSparkles` SVG) + `On` / `Off`.
  - **Pilules spécifiques `Audio` & `3D Gen`** : affichées dynamiquement selon `capabilities` (Sous-mode `[Voice | Music | SFX]`, Voix, `[Vocal | Instrumental]`, Résolution 3D `256/384/512`, Polycount, `[PBR On/Off]`, `[Tri/Quad]`, Squelette/Animation, Format `.GLB/.FBX`).
- **Badge de Capacité Restante & Bouton d'Envoi (`↑`)** :
  - À l'extrême droite de la barre inférieure (`ui-spec_image.png`, `Brand01.png`), un conteneur pilule `bg-[#F3F4F6] rounded-full pl-3 pr-1 py-1 flex items-center gap-2` regroupe l'indicateur de capacité/quota restant (ou VRAM libre) et le bouton rond noir `w-9 h-9 rounded-full bg-[#111827] text-white flex items-center justify-center` avec la flèche montante SVG `↑`.

---

## 7. Sélecteur de Modèles & Gestionnaire de Liste Utilisateur (`ModelSelectorPopover`)

*Captures de référence :* [`ui-spec_image_model-selector.png`](./ui-specifications/ui-spec_image_model-selector.png), [`ui-spec_video_model-selector.png`](./ui-specifications/ui-spec_video_model-selector.png), [`ui-spec_lip-sync_model-selector.png`](./ui-specifications/ui-spec_lip-sync_model-selector.png)

1. **En-tête du Popover** :
   - Champ de recherche `Search all models...` (`bg-[#F3F4F6] rounded-lg h-9 px-3 text-xs`) à gauche + sélecteur segmenté de catégorie (`Image | Video | Audio | Lip sync | Upscaling | 3D`) à droite.
   - Rangée de puces de filtrage rapide par tags sous la recherche : `Realistic`, `Upscaling`, `Editing`, `Audio`, `Fast`, `Low Cost` (`rounded-md border border-[#E5E7EB] px-2 py-0.5 text-[11px] font-medium text-[#374151]`).
2. **Cartes de Modèles dans la Liste** :
   - Vignette icône/logo carrée `w-10 h-10 rounded-xl bg-[#F3F4F6]` à gauche.
   - Titre du modèle en gras (`text-sm font-semibold text-[#111827]`), badges de statut (`Beta` sur fond `#F3F4F6`, `New` sur fond `#EEF2FF`, `! Slower than usual` sur fond ambre `#FEF3C7` texte `#B45309`, badge de coût/VRAM `426` / `14 GB`), et description sur une ligne (`text-xs text-[#6B7280]`).
3. **Gestion Dynamique de la Liste par l'Utilisateur (Ajout / Suppression — Zéro Liste Figée)** :
   - L'utilisateur n'est **jamais bloqué** sur une liste figée dans le code Python :
     - **Bouton `[ + Add Model ]`** en bas du sélecteur permettant d'ajouter un modèle :
       - **Pour `Colab`** : saisie de l'identifiant Hugging Face (`hf_repo_id`, ex. `Wan-AI/Wan2.1-T2V-14B-Diffusers`), URL de poids `.safetensors` / Civitai, ou chemin Google Drive, choix de la catégorie et des `capabilities` (avec estimation automatique de la VRAM requise via `hf-mem`).
       - **Pour `Local` (ComfyUI Headless)** : auto-détection immédiate des modèles connus présents dans ComfyUI + onglet **`Add / Map Custom Workflow`** permettant de déposer un fichier `workflow_api.json` et de mapper ses nœuds (`prompt`, `seed`, `dimensions`, `startFrame`, `endFrame`, `references`, `outputNode`).
     - **Action `Remove / Hide` sur chaque modèle** : l'utilisateur peut retirer n'importe quel modèle qu'il n'utilise pas ou réinitialiser les modèles par défaut.
     - **Disponibilité 100 % Hors-Ligne — cible non implémentée** : le catalogue est lu depuis `data/models.json` sur le PC local ; même si Colab ou ComfyUI est éteint, l'utilisateur peut parcourir, configurer et modifier sa liste de modèles.
