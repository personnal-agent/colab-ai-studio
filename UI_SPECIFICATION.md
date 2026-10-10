# Spécification Fonctionnelle & Ergonomique de l'Interface Utilisateur (UI/UX) — Colab AI Studio

---

## 1. Vision & Architecture Ergonomique Globale

L'interface de **Colab AI Studio** est un studio de création visuelle et multimodale par intelligence artificielle, conçu pour offrir une ergonomie fluide et hautement réactive sur machine locale.

### 1.1. Principes Ergonomiques Directeurs
- **Poste de Commande Flottant Unifié (*Floating Prompt Dock*)** : Tout le pilotage créatif (prompt, fentes de conditionnement, modèle, réglages de format et déclenchement) est regroupé dans un dock flottant ancré au centre inférieur de la fenêtre.
- **Quatre Pôles de Création Dédiés** :
  1. 🎨 **Image** : Génération d'images fixes guidée par prompt et images de référence.
  2. 🎬 **Vidéo** : Génération cinématique avec contrôle temporel (images clés début/fin, références de mouvement et audio).
  3. 🗣️ **Lip Sync** : Animation et synchronisation labiale (visage source et piste vocale).
  4. 🔍 **Upscaling** : Pôle autonome de rehaussement de résolution (image et vidéo jusqu'à 4K).
- **Interface Pilotée par Schéma Dynamique (*Schema-Driven*)** : Les intitulés `MODEL-NAME` et descriptions sont alimentés dynamiquement par le catalogue de modèles disponibles sur le backend. L'interface adapte instantanément ses contrôles aux capacités du modèle actif.
- **Zéro Décalage de Mise en Page (*Zero Layout Shift*)** : Hauteurs et espacements calibrés pour éviter toute secousse visuelle lors de la bascule de mode.

---

## 2. Disposition Spatiale de l'Écran (Layout Global)

*Capture de référence :* `ui-spec-page.jpg`

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [★] Image & Video                                                [▶ Ask] [📁] [🔔] [👤] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔍 Search images, videos, and lip syncs               [ + Image ] [ + Video ] [ + Lip ] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ GRILLE DE CONTENU (MOSAÏQUE DYNAMIQUE DES CRÉATIONS) :                                 │
│ [🖼 Image generated]   [▶ Video generated]   [🔊 Audio generated]   [4K ⤢ Upscaled img] │
│ [4K ▶ Upscaled vid]   [👄 Lip sync]         [🖼 Image generated]   [🖼 Image generated]│
│                                                                                        │
│          ┌──────────────────────────────────────────────────────────────┐              │
│          │ DOCK FLOTTANT : [ Image ] [ Video ] [ Lip sync ] [ Upscale ] │ [@ Brand Kit]│
│          │ [Start frame] [End frame] [Image refs] [Video] [Audio]       │              │
│          │ Describe your video or reference by using @...               │              │
│          │ [MODEL-NAME] [16:9] [720p] [5s] [🔊 On] [⚏ 1] [🪄 On]   [↑]  │              │
│          └──────────────────────────────────────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Barre Supérieure & Contrôles Globaux

*Capture de référence :* `ui-spec-page.jpg`

### 3.1. Bloc Gauche (Favoris & Titre)
- **Bouton Étoile Favoris `[★]`** : Bascule la galerie pour n'afficher **exclusivement que les générations marquées en favoris**. Un second clic rétablit le flux complet.
- **Titre de la Page `Image & Video`** : Identifie l'espace de travail actif dans l'application.

### 3.2. Bloc Droit (Outils & Compte)
- **Bouton Pilule `[▶ Ask]`** : Centre d'assistance, Foire Aux Questions (FAQ) et journal des versions (*Release Notes*). Ouvre un volet latéral d'aide intégrée (paramètres, mémoire VRAM, formats).
- **Bouton Dossier Projets & Collections `[📁]`** : Explorateur de stockage physique et gestionnaire de projets/collections.
  - Ouvre un volet d'exploration visuelle parcourant l'arborescence des dossiers réels sur disque avec raccourci direct (*Ouvrir dans l'Explorateur / Finder*).
  - **Stratégie de Stockage des Projets & Collections** :
    - *Emplacement standard par défaut* : Le projet est créé en sous-dossier direct dans l'arborescence de l'application (`outputs/projects/<id>/`).
    - *Emplacement personnalisé sur mesure* : L'utilisateur peut spécifier lors de la création un chemin physique sur mesure (`storagePath`).
    - *Règle d'isolation absolue* : Lorsqu'un dossier personnalisé est spécifié pour un projet, **toutes les créations associées sont stockées exclusivement dans cet emplacement**, sans aucune duplication dans le dossier local par défaut.
- **Bouton Cloche `[🔔]`** : Centre de notifications (générations terminées en arrière-plan, alertes de connexion Colab, avertissements VRAM).
- **Indicateur de Mode & Compte Distant `[👤]` (Avatar / Pastille circulaire)** :
  - *Mode Google Colab (Calcul Déporté)* : Avatar du compte connecté avec pastille active. Clic : popover affichant les crédits Colab restants (*Compute Units*), l'état du serveur, l'usage RAM/VRAM en direct, le GPU alloué (Tesla T4) et le temps de session restant.
  - *Mode Local (Calcul sur Machine Hôte)* : Rond complet en gris neutre uniforme (`#9CA3AF`), clic inactif.
  - *Note d'évolution* : Bascule dynamique à chaud suivie dans l'issue [#2](https://github.com/personnal-agent/colab-ai-studio/issues/2).

---

## 4. Recherche Globale & Filtres de Flux

*Capture de référence :* `ui-spec-page.jpg`

- **Champ de Recherche** : Barre horizontale pleine largeur avec icône loupe `🔍`, placeholder `Search images, videos, and lip syncs`. Filtrage temps réel par prompt, modèle, date ou mots-clés.
- **Puces d'Inclusion Rapide** : Trois boutons pilules `+ Image`, `+ Video`, `+ Lip sync`. Filtres cumulatifs instantanés modifiant l'affichage de la galerie.

---

## 5. Grille de la Galerie & Types de Cartes Média

*Capture de référence :* `ui-spec-page.jpg`

La galerie présente les créations générées sous forme de cartes standardisées :
1. **Carte Image (`Image generated`)** : Icône paysage `[🖼]`, aperçu HD, zoom doux et prompt tronqué au survol.
2. **Carte Vidéo (`Video generated`)** : Icône lecture `[▶]`, prévisualisation vidéo automatique en boucle muette au survol.
3. **Carte Audio (`Audio generated`)** : Icône acoustique `[🔊]`, lecteur compact avec spectrogramme au survol.
4. **Carte Image Agrandie (`Upscaled image`)** : Icône diagonale `[⤢]`, badge d'angle `4K` (super-résolution).
5. **Carte Vidéo Agrandie (`Upscaled video`)** : Icône lecture `[▶]`, badge d'angle `4K` (interpolation et super-résolution).
6. **Carte Synchronisation Labiale (`Lip sync`)** : Icône lèvres parlantes `[👄]`, lecture vidéo synchronisée voix au survol.

### 5.1. Marquage des Favoris & Enregistrement Local Systématique
- **Bouton Étoile sur chaque Carte (`[★]`)** : Bascule l'état Favori d'un clic pour filtrage immédiat via la barre supérieure.
- **Enregistrement Automatique Exhaustif & Destination Résolue** :
  - **Toutes les générations sans exception sont enregistrées sur le disque local dans leur dossier de destination résolu** :
    - Répertoire personnalisé `storagePath` si le projet en définit un (stockage exclusif sans duplication).
    - Sous-dossier standard `outputs/projects/<id>/` par défaut pour un projet sans chemin personnalisé.
    - Dossier chronologique `outputs/YYYY-MM-DD/` pour toute génération hors projet.
  - Chaque média est indissociable de sa fiche d'archive locale complète : prompt complet, chemin absolu/relatif du fichier, paramètres de calcul (modèle, seed, ratio, résolution, durée, fps), date/horodatage précis, état favori et ID projet.

### 5.2. Clic sur une Carte : Lecteur Grand Format & Remix
- Clic sur une carte : fenêtre modale d'inspection avec lecteur HTML5 plein écran, fiche technique complète, bouton Favori `[★]`, bouton **Remix** (recharge prompt et réglages dans le dock flottant) et actions d'export (télécharger, copier chemin, ouvrir dossier local). *(Maquette réservée : `ui-spec_media_player_modal.png`, voir §9.2)*.

---

## 6. Station de Commande Flottante (*Floating Prompt Dock*)

*Captures de référence :* `ui-spec-page.jpg`, `ui-spec_video.png`, `ui-spec_image.png`, `ui-spec_lip-sync.png`

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [ Image ]  [ Video ]  [ Lip sync ]  [ Upscaling ]                                [@ Brand Kit] │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Start frame]  [End frame]  [Image refs]  [Video refs]  [Audio refs]                           │
│ Describe your video or reference by using @...                                                 │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [🎬 MODEL-NAME]  [▭ 16:9]  [⇅ 720p]  [⏱ 5s]  [🔊 On]  [⚏ 1]  [🪄 On]                     [↑]  │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1. Onglets de Catégorie & Action de Marque
- **Onglets de Mode** : `Image` (images fixes), `Video` (fentes temporelles et dynamique), `Lip sync` (visage + voix), `Upscaling` (super-résolution).
- **Bouton Pilule `@ Brand Kit`** : Insertion d'une identité de marque active dans le prompt.
  - *Premier usage (aucun kit)* : Popover avec message *« Aucun brand kit. Définissez votre marque une fois, puis utilisez-la pour générer. »* et bouton *« Create brand kit »*.
  - *Kits existants* : Popover ancré trié par `lastUsedAt`. Survol : carte d'aperçu dynamique (logo, nom, compteur d'actifs, nuancier).
  - *Sélection* : Insère un **chip atomique unique `[@NomDuKit]`** dans le prompt (remplace le précédent). Suppression d'un bloc par `Retour arrière`.
  - *Déclenchement* : Aucun écran intermédiaire ; clic sur `↑` compile directement via `BrandContextCompiler`.

### 6.2. Plateau de Conditionnement Multimodal (Fentes de Référence)
- **Mode Vidéo (5 fentes)** : `Start frame` (cadrage initial), `End frame` (atterrissage caméra), `Image refs` (style/sujet), `Video refs` (mouvement/angle), `Audio refs` (tempo sonore).
- **Mode Image (1 fente)** : `Image refs` (guidage stylistique).
- **Mode Lip Sync (2 fentes)** : Fente visage source (portrait) et fente audio vocal (`.mp3`, `.wav`). *(Maquette réservée : `ui-spec_lip-sync_reference-inputs.png`, voir §9.2)*.
- **Mode Upscaling (1 fente)** : Fente média source (image ou vidéo à réhausser).

### 6.3. Zone de Saisie de Prompt
- **Placeholder contextuel** : `Describe your video or reference by using @...` (vidéo) ou `Describe your image or reference by using @...` (image/lip sync).
- **Déclencheur `@`** : Ouvre un popover d'autocomplétion proposant d'invoquer un actif de marque ou un personnage cohérent.

### 6.4. Pilules de Contrôle Inférieures (Dynamiques)
- **Sélecteur de Modèle (`MODEL-NAME`)** (*Captures :* `ui-spec_lip-sync_model-selector-clean.jpeg`, `ui-spec-page.jpg`) : Ouvre le catalogue avec recherche, onglets (`Image`, `Video`, `Lip sync`, `Upscaling`), tags de filtres et cartes descriptives. Reconfigure instantanément les pilules adjacentes.
- **Format & Ratio (`16:9`)** : Image (`8:1` à `2:3`), Lip sync (`16:9`, `9:16`, `1:1`), Vidéo (`16:9`, `9:16`, `1:1`, `21:9`, `4:3`). *(Maquette réservée : `ui-spec_video_aspect-ratio.png`, voir §9.2)*.
- **Définition & Résolution (`720p`, `1K`, `1080p`)** : Image (`1K`, `2K`, `4K`), Vidéo / Lip sync (`720p`, `1080p`, `4K`). *(Maquettes réservées : `ui-spec_video_resolution.png`, `ui-spec_lip-sync_resolution.png`, voir §9.2)*.
- **Durée Temporelle (`5s`) & Commutateur Audio (`🔊 On`)** : Paliers vidéo (`3s`, `5s`, `10s`) et toggle audio synchronisé. *(Maquettes réservées : `ui-spec_video_duration.png`, `ui-spec_video_audio.png`, voir §9.2)*.
- **Tirages Parallèles (`⚏ 1` à `⚏ 4`)** : Génération de 1 à 4 déclinaisons simultanées sur la même consigne.
- **Amélioration de Prompt (`🪄 On`)** : Enrichissement automatique par vocabulaire photographique/cinématique.
- **Style d'Élocution (`Stable` / `Expressive` en Lip Sync)** : `Stable` (tête fixe, lèvres nettes) vs `Expressive` (micro-mouvements naturels).

### 6.5. Bouton d'Action Circulaire (`↑`) & Suivi de Tâche
- Bouton noir circulaire avec flèche `↑`. Clic : envoi asynchrone au worker, état de chargement léger, carte de suivi instantanée en haut de la galerie (pourcentage, étape, bouton d'annulation).
- À l'achèvement, média enregistré localement dans sa destination résolue (`storagePath`, `outputs/projects/<id>/` ou `outputs/YYYY-MM-DD/`) et miniature activée dans la galerie. *(Maquette réservée : `ui-spec_generation_in_progress.png`, voir §9.2)*.

---

## 7. Système Brand Kit (Identité de Marque & Contexte Automatisé)

*Captures de référence :* `Brand01.png`, `Brand02.png`, `Brand03.png`, `Brand04.png`, `Brand05.png`

Le **Brand Kit** formalise l'ADN d'une marque (logos, nuanciers, polices, images de référence et charte rédactionnelle) pour garantir une cohérence visuelle parfaite sans ressaisie manuelle dans les prompts.

### 7.1. Point d'Entrée & Sélecteur Rapide (`Brand01.png`)
- **Bouton `@ Brand Kit`** : Coin supérieur droit du dock flottant (ou déclencheur clavier `@` dans le prompt).
- **Menu Popover « Brand kits »** : Liste ordonnée des kits avec pastille, nom (ex: *Apple*) et compteur d'actifs (*15*). Bouton `+` pour créer un nouveau kit.
- **Carte d'Aperçu au Survol (*Hover Card*)** : Logo principal HD, nom en titre gras, métadonnées de fraîcheur (*15 assets · Updated 2 minutes ago*) et nuancier emblématique.
- **Sélection** : Chip atomique `[@NomDuKit]` dans le prompt (un seul kit actif, suppression d'un bloc).

### 7.2. Modale de Création d'un Brand Kit (`Brand02.png`, `Brand03.png`, `Brand04.png`)
Accessible via le bouton `+` du popover :
- **Trois Méthodes d'Initialisation (`Create from`)** :
  1. `[ Blank ]` (`Brand02.png`) : Création manuelle sans document préalable.
  2. `[ Brand files ]` (`Brand04.png`) : Zone de glisser-déposer pour PDF, images ou fichiers Figma `.fig` avec extraction automatique d'identité.
  3. `[ Website ]` (`Brand03.png`) : Saisie d'URL (`https://example.com`) avec analyse automatique (logos, nuancier CSS, résumé d'activité).
- **Validation** : Bouton pilule noir `[ Continue ]` pour passer à l'inspection détaillée.

### 7.3. Volet d'Inspection & Gestion des Actifs (`Brand05.png`)
- **Navigation Latérale (Colonne Gauche)** : `Overview` (synthèse), `Logos` (variantes claire/sombre/mono), `Colors` (hex et rôles), `Fonts` (familles/graisses), `Reference images` (photothèque DA), `Voices` (profils voix), `Captions` (sous-titres), `Guidelines` (règles do's & don'ts). Bouton ancré `[ Use this brand kit ]`.
- **Espace Éditorial (Zone Centrale)** : Titre de marque, bouton `[ + Add ]`, menu `[ ··· ]` (renommer, dupliquer, modifier brief, supprimer), brief narratif complet, grilles de logos et nuancier avec liens `View all`.

### 7.4. Intégration dans le Prompt & Comportement d'Exécution
- Chip `[@NomDuKit]` actif : prompt saisi librement.
- Au clic sur `↑` : aucun panneau intermédiaire bloquant. Compilation en arrière-plan par `BrandContextCompiler`, attribution prioritaire des slots libres aux images de style et au logo officiel.

---

## 8. Pôle Dédié : Rehaussement de Résolution (*Upscaling*)

*Captures de référence :* `ui-spec-page.jpg`, `ui-spec_upscaling-image.png`, `ui-spec_upscaling-video.png`, `ui-spec_upscaling-video_scale.png`, `ui-spec_upscaling-video_quality.png`, `ui-spec_upscaling-video_frame-rate.png`

L'onglet **Upscaling** unifie les modèles de super-résolution (image fixe ou séquence vidéo) :
1. Clic sur `Upscaling` filtre le sélecteur sur les modèles de rehaussement.
2. **Modèle Image** (ex: *Topaz Image Upscale*, `ui-spec_upscaling-image.png`) : fente image source, pilule modèle, facteur d'agrandissement (`⊕ 2x`), bouton réglages `🎛️`.
3. **Modèle Vidéo** (ex: *Topaz Video Upscale*, `ui-spec_upscaling-video.png`) : fente vidéo source et 4 pilules spécifiques : Modèle, Qualité (`Fast` vs `Precise`), Échelle (`1.25x` à `4x`), Cadence (`Same as source`, 24 à 60 fps). Bouton `🎛️` pour débruitage temporel. *(Maquettes réservées : `ui-spec_topaz-video_settings.png`, voir §9.2)*.

---

## 9. Inventaire Consolidé des Captures d'Écran

### 9.1. Captures d'Illustration Existantes (24 fichiers)

> [!NOTE]
> **Disponibilité des Maquettes** : L'intégralité des 24 captures et maquettes d'illustration listées ci-dessous est intégrée et suivie sous contrôle de version Git directement dans le dossier [`ui-specifications/`](./ui-specifications/), garantissant un accès pérenne et immédiat à tous les contributeurs.

| Fichier Image | Rôle Ergonomique & Éléments Illustrés |
| :--- | :--- |
| `ui-spec-page.jpg` | **Maquette maîtresse** : vue d'ensemble (Header, Ask, Dossier, Cloche, Profil), recherche, filtres, cartes de galerie et dock flottant avec les 4 onglets. |
| `ui-spec_lip-sync_model-selector-clean.jpeg` | **Maquette épurée du sélecteur de modèle** : structure générique `MODEL-NAME`, descriptifs, filtres et les 4 onglets de catégorie. |
| `Brand01.png` | **Sélecteur Brand Kit & Aperçu Hover** : bouton `@ Brand Kit`, popover avec compteur d'assets et carte de survol détaillée (logo Apple, nuancier). |
| `Brand02.png` | **Modale Brand Kit (Vierge)** : sélection de source `Blank`, sous-titre incitatif et bouton continuer. |
| `Brand03.png` | **Modale Brand Kit (Site Web)** : sélection `Website`, champ URL avec extraction automatique d'actifs. |
| `Brand04.png` | **Modale Brand Kit (Fichiers)** : sélection `Brand files`, zone glisser-déposer pour PDF, images ou fichiers Figma `.fig`. |
| `Brand05.png` | **Dialogue d'inspection Brand Kit** : navigation latérale (Overview, Logos, Colors, etc.), brief de marque complet, grille de logos, nuancier et bouton `Use this brand kit`. |
| `ui-spec_image.png` | Disposition du dock en mode Image avec la fente `Image refs`. |
| `ui-spec_image_aspect-ratio.png` | Menu déroulant des 9 formats d'image (8:1 à 2:3). |
| `ui-spec_image_generations.png` | Menu déroulant du nombre de tirages d'images (1 à 4). |
| `ui-spec_image_model-selector.png` | Volet de recherche et catalogue illustratif des modèles d'image. |
| `ui-spec_image_resolution.png` | Menu déroulant des résolutions d'image (1K, 2K, 4K). |
| `ui-spec_video.png` | Plateau des cinq fentes de conditionnement en mode Vidéo. |
| `ui-spec_video_model-selector.png` | Volet de recherche et catalogue illustratif des modèles vidéo. |
| `ui-spec_lip-sync.png` | Disposition du dock en mode Lip sync. |
| `ui-spec_lip-sync_aspect-ratio.png` | Menu déroulant des 3 ratios spécifiques au Lip sync. |
| `ui-spec_lip-sync_generations.png` | Menu déroulant des variantes de Lip sync (1 à 4). |
| `ui-spec_lip-sync_model-selector.png` | Volet des modèles de synthèse labiale. |
| `ui-spec_lip-sync_talking-style.png` | Menu déroulant du style d'élocution (`Stable` vs `Expressive`). |
| `ui-spec_upscaling-image.png` | Dock contracté pour la retouche et l'agrandissement d'image. |
| `ui-spec_upscaling-video.png` | Dock adapté pour l'agrandissement vidéo. |
| `ui-spec_upscaling-video_scale.png` | Menu déroulant des facteurs d'agrandissement vidéo (1.25x à 4x). |
| `ui-spec_upscaling-video_quality.png` | Menu déroulant de qualité d'agrandissement vidéo (`Fast` vs `Precise`). |
| `ui-spec_upscaling-video_frame-rate.png` | Menu déroulant des cadences vidéo (Same as source, 24 à 60 fps). |

### 9.2. Matrice des Captures Complémentaires Réservées (16 fichiers)

| Fichier Réservé | Déclencheur Utilisateur (Trigger) | État Visuel Attendu |
| :--- | :--- | :--- |
| `ui-spec_video_aspect-ratio.png` | Clic sur la pilule de format en Vidéo | Menu déroulant des ratios vidéo. |
| `ui-spec_video_resolution.png` | Clic sur la pilule de résolution en Vidéo | Menu des résolutions vidéo disponibles. |
| `ui-spec_video_duration.png` | Clic sur la pilule de durée en Vidéo | Paliers de durée vidéo (3s, 5s, 10s). |
| `ui-spec_video_audio.png` | Clic sur la pilule audio en Vidéo | Options d'activation et de sonorisation. |
| `ui-spec_video_generations.png` | Clic sur la pilule de tirages en Vidéo | Variantes vidéo générées en parallèle. |
| `ui-spec_video_enhance.png` | Clic sur `🪄 On` en Vidéo | Options d'optimisation de prompt vidéo. |
| `ui-spec_image_quality.png` | Clic sur `◇ High` en Image | Sélecteur de qualité (Standard, High, Ultra). |
| `ui-spec_image_enhance.png` | Clic sur `🪄 On` en Image | Comportement de l'enrichisseur de prompt image. |
| `ui-spec_lip-sync_resolution.png` | Clic sur la résolution en Lip sync | Sélecteur de définition (720p, 1080p). |
| `ui-spec_lip-sync_reference-inputs.png` | Affichage du plateau en Lip sync | Fentes de dépôt visage source + audio vocal. |
| `ui-spec_topaz-image_scale.png` | Clic sur `⊕ 2x` en retouche image | Facteurs d'échelle disponibles pour l'image. |
| `ui-spec_topaz-image_settings.png` | Clic sur `🎛️` en retouche image | Volet de réglages fins d'image. |
| `ui-spec_topaz-video_settings.png` | Clic sur `🎛️` en rehaussement vidéo | Volet de réglages fins vidéo. |
| `ui-spec_media_player_modal.png` | Clic sur une miniature de média | Lecteur grand format, métadonnées et remix. |
| `ui-spec_generation_in_progress.png` | Après clic sur le bouton `↑` | Carte de progression de tâche en direct. |
| `ui-spec_colab_connection_status.png` | Clic sur l'indicateur de liaison | Volet de diagnostic matériel et de latence. |
