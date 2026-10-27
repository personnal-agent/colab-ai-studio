# Spécifications Graphiques & Design System (Tokens) — Omniforge

> **Statut documentaire — cible à implémenter.** Les documents numérotés décrivent l'évolution Omniforge ; ils ne prouvent pas sa disponibilité. Le code actuel accepte seulement `colab` et `local` via le contrat worker (`/infer`, `/tasks/{task_id}/status`, `/tasks/{task_id}/cancel`, `/files/{path}`). OAuth Colab automatique, TPU/LRU, ComfyUI direct, mode API, catalogue hors-ligne, LoRAs, audio/3D et validation `acceptedInputTypes` restent des objectifs. Voir [SPECIFICATION01.md](SPECIFICATION01.md#4-spécifications-des-3-moteurs-dexécution-colab--local--api) pour les écarts avec l'existant.

---

## 1. Philosophie Visuelle & Conformité Stricte aux Maquettes (`ui-specifications/`)

Le Design System d'**Omniforge** est calibré au pixel près sur les 24 captures officielles du dossier [`ui-specifications/`](./ui-specifications/) :
1. **Zéro Emoji Clavier / Unicode dans le Code React** :
   - Interdiction absolue d'insérer des caractères emoji (`🎨`, `🎬`, `🗣️`, `🔍`, `🪄`, `🔊`, `⚏`, `👄`, `📁`, `🔔`, `👤`, `🎛️`, `🧩`, `🧊`) dans le DOM.
   - Toutes les icônes sont des composants vectoriels SVG filaires (`lucide-react` ou SVG dédiés en `stroke-width: 1.5` à `1.75`, `stroke="currentColor"`).
2. **Surfaces Translucides & Nuances de Gris Chaudes** :
   - Le *Floating Prompt Dock* utilise un verre dépoli translucide (`bg-white/90 backdrop-blur-xl`) qui laisse deviner en douceur les créations de la galerie en arrière-plan (visible sur `ui-spec_image_aspect-ratio.png`, `Brand01.png`, `Brand02.png`).
   - Les fentes de conditionnement (`Start frame`, `Image refs`) et les cartes illustratives de la galerie (`Image generated`, `Video generated`) utilisent la teinte exacte `#EFEFEF` (et non un gris bleuté froid ou un blanc pur).
3. **Pilules de Paramètres Sans Bordure au Repos (*Ghost Pills*)** :
   - Contrairement à des boutons encadrés classiques, toutes les pilules de la rangée inférieure du dock (`Seedance 2.5`, `16:9`, `720p`, `5s`, `On`, `1`) n'ont **aucune bordure ni fond au repos** (`bg-transparent border-transparent text-[#4B5563]`), et prennent un fond gris doux `#EAECEF` avec texte `#111827` lorsqu'elles sont actives ou que leur menu est ouvert (`ui-spec_image_resolution.png`, `ui-spec_upscaling-video_quality.png`).
4. **Habillage Visuel Décoratif Initial (*Zero Bare Empty State*)** :
   - L'interface embarque des actifs visuels décoratifs pour les bannières `Avatars` et `Brand kit`, les 6+1 cartes illustratives vectorielles sur fond `#EFEFEF` et les cartes photographiques/éditoriales de démonstration afin que l'accueil soit visuellement identique aux captures dès la première seconde.

---

## 2. Palette de Couleurs Exacte (Calibrée sur `ui-specifications/`)

| Token Sémantique | Code Hexadécimal / RGBA | Classe Tailwind / CSS | Utilisation Concrète dans les Maquettes |
| :--- | :--- | :--- | :--- |
| `surface-canvas` | `#F9FAFB` | `bg-[#F9FAFB]` | Arrière-plan général de la page (`ui-spec-page.jpg`). |
| `surface-card` | `#FFFFFF` | `bg-white` | Barre de recherche, bannières `Avatars` & `Brand kit`, modales. |
| `surface-dock-glass` | `rgba(255, 255, 255, 0.90)` | `bg-white/90 backdrop-blur-xl` | Surface translucide dépolie du *Floating Prompt Dock*. |
| `surface-slot` | `#EFEFEF` | `bg-[#EFEFEF]` | Fentes `Start frame` / `Image refs`, rail des onglets `Image/Video`, et fond des 7 cartes illustratives, dont `Image generated` et `3D generated`. |
| `surface-slot-hover` | `#E6E6E8` | `hover:bg-[#E6E6E8]` | Survol d'une fente de conditionnement. |
| `surface-pill-open` | `#EAECEF` | `bg-[#EAECEF]` | Fond d'une pilule de paramètre inférieure lorsque son menu est ouvert (`1K`, `2:3`, `Fast`). |
| `surface-pill-hover` | `#F3F4F6` | `hover:bg-[#F3F4F6]` | Survol d'une pilule de paramètre inférieure ou d'un item de menu. |
| `surface-quota-pill` | `#F3F4F6` | `bg-[#F3F4F6]` | Conteneur pilule `52 left` accolé au bouton d'envoi noir `↑`. |
| `surface-overlay` | `rgba(0, 0, 0, 0.35)` | `bg-black/35 backdrop-blur-[2px]` | Voile d'arrière-plan des modales Brand Kit (`Brand02.png`). |
| `text-primary` | `#111827` | `text-[#111827]` | Titres principaux, onglet actif, valeur de pilule ouverte, noms de modèles. |
| `text-secondary` | `#4B5563` | `text-[#4B5563]` | Pilules de paramètres au repos, libellés des fentes `Start frame`, descriptions. |
| `text-muted` | `#6B7280` | `text-[#6B7280]` | Onglets inactifs (`Image`, `Video`), en-têtes de menus déroulants (`Aspect ratio`, `Resolution`). |
| `text-placeholder` | `#6B7280` | `text-[#6B7280]` | Placeholder `Describe your video or reference by using @...` et recherche. |
| `action-primary` | `#111827` | `bg-[#111827] text-white` | Bouton circulaire d'envoi `↑`, boutons `[ Continue ]`, `[ + Add ]`, `[ Use this brand kit ]`. |
| `border-default` | `#E5E7EB` | `border-[#E5E7EB]` | Bordure de la barre de recherche, des puces `+ Image`, des bannières et des menus. |
| `border-dock` | `rgba(0, 0, 0, 0.08)` | `border-black/[0.08]` | Contour subtil du dock flottant et des popovers surélevés. |
| `badge-beta` | `#F3F4F6` / `#374151` | `bg-[#F3F4F6] text-[#374151]` | Badge `Beta` et badges de coût/vitesse (`426`, `1,212/s`). |
| `badge-warning` | `#FEF3C7` / `#B45309` | `bg-[#FEF3C7] text-[#B45309]` | Badge `! Slower than usual` (`ui-spec_image_model-selector.png`). |
| `badge-new` | `#EEF2FF` / `#4338CA` | `bg-[#EEF2FF] text-[#4338CA]` | Badge `New` (`Ruby New` dans `ui-spec_video_model-selector.png`). |
| `dot-notification` | `#2563EB` | `bg-[#2563EB]` | Pastille bleue sur l'icône cloche de notification (`ui-spec-page.jpg`). |
| `status-colab` | `#3B82F6` | `bg-blue-500` | Anneau/pastille indiquant le runtime Google Colab actif. |
| `status-local` | `#10B981` | `bg-emerald-500` | Anneau/pastille indiquant ComfyUI Headless local actif. |
| `status-api` | `#6366F1` | `bg-indigo-500` | Anneau/pastille indiquant le mode Clés API actif. |

---

## 3. Table de Correspondance Vectorielle des Icônes (Zéro Emoji)

Chaque icône visible sur les captures `ui-specifications/` doit être implémentée avec son composant SVG exact :

| Élément d'Interface | Capture de Référence | Icône SVG (`lucide-react` ou SVG dédié) | Style & Dimensions |
| :--- | :--- | :--- | :--- |
| Bouton barre latérale gauche | `ui-spec-page.jpg` | `PanelLeft` | `w-4 h-4 stroke-[1.75] text-[#374151]` dans bouton `w-8 h-8 rounded-lg border border-[#E5E7EB]` |
| Bouton `[▶ Ask]` | `ui-spec-page.jpg` | Triangle Play multicolore SVG dédié | `w-3.5 h-3.5` + texte `Ask` (`text-xs font-semibold text-[#111827]`) |
| Bouton Projets `[📁]` | `ui-spec-page.jpg` | `Folder` | `w-4 h-4 stroke-[1.75] text-[#111827]` |
| Bouton Notifications `[🔔]` | `ui-spec-page.jpg` | `Bell` + point `#2563EB` | `w-4 h-4 stroke-[1.75] text-[#111827]` |
| Fente `Start frame` / `End frame` / `Image refs` | `ui-spec_video.png` | `Image` (cadre montagne + soleil) | `w-[18px] h-[18px] stroke-[1.6] text-[#4B5563]` |
| Fente `Video refs` & Pilule Modèle Vidéo | `ui-spec_video.png` | `Film` (pellicule cinéma carrée) | `w-[18px] h-[18px] stroke-[1.6] text-[#4B5563]` |
| Fente `Audio refs` & Carte `Audio generated` | `ui-spec-page.jpg` | `AudioLines` (5 barres verticales d'onde) | `w-[18px] h-[18px] stroke-[1.75] text-[#4B5563]` |
| Carte `Lip sync` | `ui-spec-page.jpg` | SVG Lèvres + 2 arcs d'onde sonore à droite | `w-12 h-12 stroke-[1.75] text-[#4B5563]` |
| Carte `Upscaled image` | `ui-spec-page.jpg` | `Maximize2` (double flèche diagonale `⤢`) + badge `4K` | `w-10 h-10 stroke-[1.75] text-[#4B5563]` |
| Pilule Modèle Lip Sync | `ui-spec_lip-sync.png` | `UserPlus` / `UserSparkles` | `w-4 h-4 stroke-[1.75] text-[#4B5563]` |
| Pilule `[LoRA]` | `UI_SPECIFICATION01.md` | `Layers2` / `Sparkles` | `w-3.5 h-3.5 stroke-[1.75]` |
| Pilule Format (`16:9`, `2:3`) | `ui-spec_image.png` | Rectangle SVG aux proportions du ratio | `w-3.5 h-3.5 stroke-[1.6] text-[#4B5563]` |
| Pilule Résolution (`720p`, `1K`, `1080p`) | `ui-spec_image_resolution.png` | Cadre en pointillés avec flèche diagonale | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Qualité (`High`, `Fast`) | `ui-spec_upscaling-video_quality.png` | `Tag` (étiquette inclinée) | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Durée (`5s`) | `ui-spec_video.png` | `Clock` | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Audio (`On`) | `ui-spec_video.png` | `Volume2` | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Talking Style (`Stable`) | `ui-spec_lip-sync_talking-style.png` | `Radio` / `Podcast` | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Tirages (`1` à `4`) | `ui-spec_image_generations.png` | `Layers` (losanges empilés) | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Enhance (`On`) | `ui-spec_video.png` | `WandSparkles` | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Facteur d'Échelle (`2x`) | `ui-spec_upscaling-video_scale.png` | `ZoomIn` (loupe avec `+`) | `w-3.5 h-3.5 stroke-[1.6]` |
| Pilule Frame Rate (`Same as source`) | `ui-spec_upscaling-video_frame-rate.png` | Bobine de film circulaire SVG | `w-3.5 h-3.5 stroke-[1.6]` |
| Bouton Suggestions / Options Dock (`[≡+]`) | `Brand01.png`, `ui-spec_lip-sync.png` | `ListPlus` / 3 lignes avec étoile `✦` | `w-4 h-4 stroke-[1.6] text-[#4B5563]` |

---

## 4. Dimensions & Gabarits des Composants Clés

### 4.1. Cartes Bannières Décoratives d'En-tête (`Avatars` & `Brand kit`)
- **Grille** : `grid grid-cols-1 md:grid-cols-2 gap-4 mb-5` (affichée sous les onglets `Explore | History`).
- **Carte** : `h-[132px] rounded-2xl bg-white border border-[#E5E7EB] p-5 flex items-center justify-between overflow-hidden shadow-sm`.
- **Colonne gauche** : titre `text-base font-semibold text-[#111827]`, description `text-xs text-[#6B7280] max-w-[240px] mt-1`, bouton d'action `mt-3 h-8 px-3.5 rounded-full border border-[#E5E7EB] bg-white text-xs font-semibold text-[#111827] hover:bg-[#F9FAFB]`.
- **Colonne droite** : collage décoratif de 2 à 3 vignettes aux coins arrondis (`rounded-xl object-cover`).

### 4.2. Menus Déroulants des Pilules (`DropdownMenuContent`)
Comme visible sur `ui-spec_image_aspect-ratio.png`, `ui-spec_image_resolution.png` et `ui-spec_upscaling-video_quality.png` :
- **Conteneur** : `min-w-[140px] p-1.5 rounded-2xl bg-white border border-black/[0.08] shadow-[0_12px_28px_-4px_rgba(0,0,0,0.12)]`.
- **Titre de section interne** (`Aspect ratio`, `Resolution`, `Generations`, `Talking style`, `Quality`, `Upscale`, `Frame rate`) : `px-3 py-1.5 text-[12px] font-medium text-[#6B7280]`.
- **Item de menu** : `px-3 py-2 rounded-xl text-[13px] font-medium text-[#111827] hover:bg-[#F3F4F6] flex items-center justify-between gap-4 cursor-pointer`.
- **Item sélectionné** : fond `bg-[#F3F4F6]` (ex. `Stable` dans `ui-spec_lip-sync_talking-style.png`, `2x` dans `ui-spec_upscaling-video_scale.png`) avec coche SVG `Check` (`w-3.5 h-3.5 text-[#111827]`) alignée à droite.
