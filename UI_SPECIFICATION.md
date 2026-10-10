# Spécification Fonctionnelle & Ergonomique de l'Interface Utilisateur (UI/UX) — Colab AI Studio

---

## 1. Vision & Architecture Ergonomique Globale

L'interface de **Colab AI Studio** est un studio de création visuelle et multimodale par intelligence artificielle, conçu pour offrir une ergonomie fluide et hautement réactive sur machine locale.

### 1.1. Principes Ergonomiques Directeurs
- **Poste de Commande Flottant Unifié (*Floating Prompt Dock*)** : Tout le pilotage créatif (prompt, fentes de conditionnement, modèle, réglages de format et déclenchement) est regroupé dans un dock flottant ancré au centre inférieur de la fenêtre.
- **Quatre Pôles de Création Dédiés** :
  1. 🎨 **Image** : Génération d'images fixes guidée par prompt et images de référence.
  2. 🎬 **Vidéo** : Génération cinématique avec contrôle temporel (images clés de début/fin, références de mouvement et audio).
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
│ 🔍 Search images, videos, and lip syncs                                                │
│ [ + Image ]  [ + Video ]  [ + Lip sync ]                                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ GRILLE DE CONTENU (MOSAÏQUE DYNAMIQUE DES CRÉATIONS) :                                 │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│ │       [🖼]       │  │       [▶]        │  │       [🔊]       │  │ [4K]        [⤢]  │ │
│ │  Image generated │  │  Video generated │  │  Audio generated │  │  Upscaled image  │ │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│ │ [4K]        [▶]  │  │       [👄]       │  │       [🖼]       │  │       [🖼]       │ │
│ │  Upscaled video  │  │     Lip sync     │  │  Image generated │  │  Image generated │ │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                                        │
│          ┌──────────────────────────────────────────────────────────────┐              │
│          │ STATION DE COMMANDE FLOTTANTE (FLOATING PROMPT DOCK)         │              │
│          │ [ Image ]  [ Video ]  [ Lip sync ]  [ Upscaling ] [@ Brand Kit]│            │
│          │ ┌──────────────────────────────────────────────────────────┐ │              │
│          │ │ [Start frame] [End frame] [Image refs] [Video] [Audio]   │ │              │
│          │ └──────────────────────────────────────────────────────────┘ │              │
│          │ Describe your video or reference by using @...               │              │
│          │ [MODEL-NAME] [16:9] [720p] [5s] [🔊 On] [⚏ 1] [🪄 On]   [↑]  │              │
│          └──────────────────────────────────────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Barre Supérieure & Contrôles Globaux

*Capture de référence :* `ui-spec-page.jpg`

### 3.1. Bloc Gauche (Favoris & Titre)
- **Bouton Étoile Favoris `[★]`** :
  - *Rôle* : Filtre d'affichage des créations mises en favoris.
  - *Interaction* : Clic pour basculer la vue de la galerie et n'afficher **exclusivement que les générations marquées en favoris** par l'utilisateur. Un second clic rétablit le flux complet.
- **Titre de la Page `Image & Video`** :
  - *Rôle* : Identifie l'espace de travail actif dans l'application.

### 3.2. Bloc Droit (Outils & Compte)
- **Bouton Pilule `[▶ Ask]`** :
  - *Rôle* : Centre d'assistance, Foire Aux Questions (FAQ) et journal des versions (*Release Notes*).
  - *Interaction* : Ouvre un volet latéral ou une modale dédiée permettant à l'utilisateur de consulter l'aide intégrée (explication des paramètres, gestion de la mémoire VRAM, formats acceptés) et de découvrir les nouveautés des dernières mises à jour du studio.
- **Bouton Dossier Projets & Collections `[📁]`** :
  - *Rôle* : Explorateur de stockage physique, gestionnaire de projets et collections.
  - *Interaction & Affichage* :
    - Ouvre un volet d'exploration visuelle permettant de parcourir l'arborescence des dossiers réels sur le disque, d'afficher les noms physiques des répertoires et l'intégralité du contenu où sont déposées les générations.
    - Offre un raccourci d'ouverture directe dans le gestionnaire de fichiers natif du système d'exploitation (*Ouvrir dans l'Explorateur / Finder*).
    - **Création de Projets & Collections (Stratégie de Stockage)** :
      - *Emplacement standard par défaut* : Le projet est créé en tant que sous-dossier direct dans l'arborescence principale de l'application (`outputs/projects/<nom-du-projet>/`).
      - *Emplacement sur mesure personnalisé* : L'utilisateur peut spécifier lors de la création un chemin physique sur mesure n'importe où sur son disque.
      - *Règle d'isolation absolue* : Lorsqu'un dossier physique personnalisé est spécifié pour un projet, **toutes les générations et tous les fichiers associés à ce projet sont stockés exclusivement dans cet emplacement défini**, et ne sont en aucun cas dupliqués dans le dossier local par défaut.
- **Bouton Cloche `[🔔]`** :
  - *Rôle* : Centre de notifications et suivi d'achèvement des tâches.
  - *Interaction* : Affiche la liste des générations terminées en arrière-plan, les alertes d'état de connexion Colab ou les avertissements de mémoire VRAM.
- **Indicateur de Mode & Compte Distant `[👤]` (Avatar / Pastille circulaire)** :
  - *Rôle* : Témoin du mode d'exécution actif (Google Colab vs Local) et santé de la liaison de calcul.
  - *Deux modes d'exécution (déterminés lors de l'installation / configuration initiale)* :
    1. **Mode Google Colab (Calcul Déporté)** :
       - L'avatar affiche le profil du compte Google/Colab connecté avec une pastille de statut active.
       - *Interaction au clic* : Ouvre un popover détaillé affichant toutes les métriques opérationnelles pertinentes :
         - Solde des crédits de calcul Colab restants (*Compute Units*).
         - Santé et état de disponibilité du serveur distant.
         - Utilisation en direct de la mémoire vive (RAM système hôte) et de la mémoire graphique (VRAM GPU).
         - Type de GPU alloué sur l'instance (ex. Tesla T4).
         - Temps de session restant avant expiration ou déconnexion.
    2. **Mode Local (Calcul sur Ressources Locales)** :
       - Le rond complet est affiché en gris neutre uniforme (`#9CA3AF`).
       - *Interaction au clic* : Inactive (le clic ne produit aucune action).
    - *Note d'évolution ergonomique* : La bascule entre le mode Local et le mode Colab est figée par le choix d'installation ; elle ne peut pas être commutée directement au clic sur ce bouton dans cette version (suivi dans l'issue [#2](https://github.com/personnal-agent/colab-ai-studio/issues/2) : *Bascule dynamique à chaud entre les modes d'exécution Local et Google Colab*).

---

## 4. Recherche Globale & Filtres de Flux

*Capture de référence :* `ui-spec-page.jpg`

### 4.1. Champ de Recherche
- **Apparence** : Barre horizontale pleine largeur aux coins adoucis avec icône loupe `🔍`.
- **Placeholder** : `Search images, videos, and lip syncs`.
- **Interaction** : Filtrage en temps réel des médias affichés dans la galerie selon le prompt textuel, le modèle utilisé, la date ou les mots-clés associés.

### 4.2. Puces d'Inclusion Rapide
- **Trois boutons pilules** : `+ Image`, `+ Video`, `+ Lip sync`.
- **Comportement** :
  - Un clic sur une puce active un filtre cumulatif permettant de restreindre la galerie à un type de média particulier.
  - État inactif : fond neutre léger avec signe `+`.
  - État actif : fond contrasté avec coche ou mise en surbrillance, filtrant instantanément la grille.

---

## 5. Grille de la Galerie & Types de Cartes Média

*Capture de référence :* `ui-spec-page.jpg`

La galerie présente les créations générées sous la forme de cartes standardisées selon la nature du média :

1. **Carte Image (`Image generated`)** :
   - *Visuel* : Icône paysage `[🖼]`, aperçu de l'image haute définition.
   - *Au survol* : Zoom doux, affichage du prompt tronqué et bouton d'action rapide.
2. **Carte Vidéo (`Video generated`)** :
   - *Visuel* : Icône lecture dans un cercle `[▶]`.
   - *Au survol* : Lancement automatique de la prévisualisation vidéo en boucle muette.
3. **Carte Audio (`Audio generated`)** :
   - *Visuel* : Icône d'ondes acoustiques `[🔊]`.
   - *Au survol* : Lecteur audio compact avec spectrogramme dynamique.
4. **Carte Image Agrandie (`Upscaled image`)** :
   - *Visuel* : Icône d'expansion diagonale `[⤢]`, badge d'angle `4K`.
   - *Indication* : Signale un traitement de super-résolution appliqué.
5. **Carte Vidéo Agrandie (`Upscaled video`)** :
   - *Visuel* : Icône lecture `[▶]`, badge d'angle `4K`.
   - *Indication* : Vidéo traitée avec interpolation temporelle et agrandissement haute fidélité.
6. **Carte Synchronisation Labiale (`Lip sync`)** :
   - *Visuel* : Icône lèvres parlantes avec ondes sonores `[👄]`.
   - *Au survol* : Lecture vidéo synchronisée avec la piste voix.

### 5.1. Marquage des Favoris & Enregistrement Local Systématique
- **Bouton Étoile sur chaque Carte (`[★]`)** :
  - Chaque carte de média dans la galerie comporte une icône étoile discrète (visible au survol ou en permanence si active).
  - Un clic sur l'étoile bascule l'état de la création en **Favori**, ce qui permet de l'isoler instantanément via le filtre `[★]` de la barre supérieure.
- **Enregistrement Automatique Exhaustif** :
  - **Toutes les générations sans exception sont enregistrées sur le disque local** dans le répertoire `outputs/` (organisé par date ou par projet).
  - Chaque média est indissociable de sa fiche d'archive complète conservée localement :
    - **Prompt complet** (incluant les mentions `@` et les conditionnements appliqués).
    - **Emplacement exact du fichier sur le disque** (chemin d'accès absolu et relatif).
    - **Paramètres de calcul** (modèle utilisé, graine aléatoire *seed*, ratio, résolution, durée, cadence fps).
    - **Date et horodatage précis**.
    - **État favori** et **Projet / Collection** associé(e).

### 5.2. Clic sur une Carte : Lecteur Grand Format & Remix
- Ouvre une fenêtre modale d'inspection complète :
  - Lecteur plein écran HTML5 haute définition avec contrôle de vitesse.
  - Fiche technique complète affichant le prompt, l'emplacement du fichier sur disque, le modèle et la graine (*seed*).
  - Bouton **Étoile Favori `[★]`** pour marquer/démarquer la création.
  - Bouton **Remix** : recharge immédiatement le prompt original et tous les réglages dans la station flottante pour réitérer sans friction.
  - Boutons d'export : **Télécharger**, **Copier le chemin local**, **Ouvrir le dossier local dans l'explorateur**.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Modal Lecteur Multimédia & Remix**  
> *Fichier attendu :* `ui-spec_media_player_modal.png`  
> *Déclencheur :* Clic sur une carte de la galerie.  
> *Comportement :* Modale d'inspection avec lecteur, métadonnées, bouton Remix et téléchargement direct.  
> ![Placeholder: ui-spec_media_player_modal.png](./ui-specifications/ui-spec_media_player_modal.png)

---

## 6. Station de Commande Flottante (*Floating Prompt Dock*)

*Captures de référence :* `ui-spec-page.jpg`, `ui-spec_video.png`, `ui-spec_image.png`, `ui-spec_lip-sync.png`

Le dock flottant est le cœur opérationnel du studio créatif. Il comprend quatre strates interactives :

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [ Image ]  [ Video ]  [ Lip sync ]  [ Upscaling ]                                [@ Brand Kit] │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│ │ [Start frame]│ │  [End frame] │ │ [Image refs] │ │ [Video refs] │ │ [Audio refs] │          │
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘          │
│                                                                                                │
│ Describe your video or reference by using @...                                                 │
│                                                                                                │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [🎬 MODEL-NAME]  [▭ 16:9]  [⇅ 720p]  [⏱ 5s]  [🔊 On]  [⚏ 1]  [🪄 On]                     [↑]  │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 6.1. Onglets de Catégorie & Action de Marque
- **Onglets de Mode** :
  - `Image` : Configure le studio pour la génération d'images fixes.
  - `Video` : Active les fentes temporelles et les contrôles de dynamique vidéo.
  - `Lip sync` : Active le conditionnement visage + voix et les styles d'élocution.
- **Bouton Pilule `@ Brand Kit`** :
  - *Rôle* : Raccourci d'insertion d'une identité de marque active dans le prompt.
  - *Comportement à l'usage* :
    1. **Premier usage (aucun kit enregistré)** : Ouvre un popover incitatif avec le message : *« Aucun brand kit. Définissez votre marque une fois, puis utilisez-la pour générer. »* et un bouton d'action *« Create brand kit »* ouvrant la modale de création.
    2. **Kits existants** : Ouvre un popover ancré affichant la liste des kits triés par dernière utilisation (`lastUsedAt`). Le survol d'une ligne affiche une carte d'aperçu dynamique (logo, nom, compteur d'assets, pastilles de couleurs).
    3. **Sélection** : Insère dans le champ de prompt un **chip atomique unique `[@NomDuKit]`** (un seul kit actif par prompt ; en choisir un autre remplace le précédent). Le chip se supprime d'un bloc avec la touche `Retour arrière`.
    4. **Déclenchement** : Aucun écran de validation intermédiaire ; le clic sur `↑` lance directement la génération avec compilation par le `BrandContextCompiler`.

> [!NOTE]  
> **Intégration Visuelle Complète — Captures Brand Kit Disponibles**  
> Le système Brand Kit est illustré en détail dans la section 7 avec les captures `Brand01.png`, `Brand02.png`, `Brand03.png`, `Brand04.png` et `Brand05.png`.

---

### 6.2. Plateau de Conditionnement Multimodal (Fentes de Référence)

Le plateau sous les onglets déploie les fentes de dépôt adaptées au mode sélectionné :

#### En Mode Vidéo (5 fentes) :
1. `Start frame` : Téléversement de l'image de début imposant le cadrage initial.
2. `End frame` : Téléversement de l'image de fin guidant l'atterrissage de la caméra.
3. `Image refs` : Injection d'images de style ou de sujet (cohérence visuelle continue).
4. `Video refs` : Référence vidéo pour transfert de mouvement ou d'angle de prise de vue.
5. `Audio refs` : Piste sonore servant de guide de synchronisation ou de rythme.

#### En Mode Image (1 fente) :
- `Image refs` : Téléversement d'une ou plusieurs images de guidage stylistique.

#### En Mode Lip Sync (2 fentes) :
- Fente de visage source (photo d'un personnage/avatar) et fente de fichier audio vocal (`.mp3`, `.wav`).

#### En Mode Upscaling (1 fente) :
- Fente média source (image ou vidéo à réhausser en résolution).

> [!NOTE]  
> **Zone Réservée — Image Manquante : Fentes de Conditionnement Lip Sync**  
> *Fichier attendu :* `ui-spec_lip-sync_reference-inputs.png`  
> *Déclencheur :* Bascule sur l'onglet `Lip sync`.  
> *Comportement :* Affichage des fentes dédiées (visage source + piste vocale).  
> ![Placeholder: ui-spec_lip-sync_reference-inputs.png](./ui-specifications/ui-spec_lip-sync_reference-inputs.png)

---

### 6.3. Zone de Saisie de Prompt
- **Placeholder contextuel** :
  - Vidéo : `Describe your video or reference by using @...`
  - Image / Lip sync : `Describe your image or reference by using @...`
- **Déclencheur `@`** : La saisie de `@` ouvre un popover d'autocomplétion proposant d'invoquer un actif de marque ou un personnage cohérent.

---

### 6.4. Pilules de Contrôle Inférieures (Dynamiques)

#### 6.4.1. Sélecteur de Modèle (`MODEL-NAME`)
*Captures de référence :* `ui-spec_lip-sync_model-selector-clean.jpeg`, `ui-spec-page.jpg`
- Affiche l'icône de la famille et le nom du modèle actif.
- Un clic ouvre le volet déroulant complet du catalogue :
  - **Champ de recherche** : `Search all models...`
  - **Onglets internes de catégorie** : `Image`, `Video`, `Lip sync`, `Upscaling`.
  - **Filtres contextuels** (tags) : `Supports non-human faces`, `Video input`, `Realistic`, `Fast`, etc.
  - **Cartes de modèles** : Chaque carte affiche l'icône `[✨]`, le titre `MODEL-NAME`, le descriptif `Model description goes here...`, et les badges/tarifs éventuels.
  - Le choix d'un modèle reconfigure immédiatement les pilules adjacentes.

#### 6.4.2. Format & Ratio d'Aspect (`16:9`)
- Ouvre la liste des ratios autorisés pour le modèle actif :
  - Image : `8:1`, `4:1`, `21:9`, `16:9`, `5:4`, `4:3`, `3:2`, `1:1`, `2:3`.
  - Lip sync : `16:9`, `9:16`, `1:1`.
  - Vidéo : `16:9`, `9:16`, `1:1`, `21:9`, `4:3`.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Ratios Vidéo**  
> *Fichier attendu :* `ui-spec_video_aspect-ratio.png`  
> *Déclencheur :* Clic sur la pilule de format en mode Vidéo.  
> ![Placeholder: ui-spec_video_aspect-ratio.png](./ui-specifications/ui-spec_video_aspect-ratio.png)

#### 6.4.3. Définition & Résolution (`720p`, `1K`, `1080p`)
- Image : `1K`, `2K`, `4K`.
- Vidéo / Lip sync : `720p`, `1080p`, `4K`.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Résolutions Vidéo & Lip Sync**  
> *Fichiers attendus :* `ui-spec_video_resolution.png`, `ui-spec_lip-sync_resolution.png`  
> *Déclencheur :* Clic sur la pilule de résolution correspondante.  
> ![Placeholder: ui-spec_video_resolution.png](./ui-specifications/ui-spec_video_resolution.png)

#### 6.4.4. Durée Temporelle (`5s`) & Commutateur Audio (`🔊 On`)
- Durées vidéo : Paliers temporels (ex: `3s`, `5s`, `10s`).
- Commutateur audio : Active ou désactive la synthèse de la piste sonore synchronisée.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Menu de Durée Vidéo**  
> *Fichier attendu :* `ui-spec_video_duration.png`  
> *Déclencheur :* Clic sur la pilule de durée en Vidéo.  
> ![Placeholder: ui-spec_video_duration.png](./ui-specifications/ui-spec_video_duration.png)

> [!NOTE]  
> **Zone Réservée — Image Manquante : Bascule Audio Vidéo**  
> *Fichier attendu :* `ui-spec_video_audio.png`  
> *Déclencheur :* Clic sur la pilule audio en Vidéo.  
> ![Placeholder: ui-spec_video_audio.png](./ui-specifications/ui-spec_video_audio.png)

#### 6.4.5. Nombre de Générations Simultanées (`⚏ 1` à `⚏ 4`)
- Permet de générer de 1 à 4 déclinaisons parallèles sur une même consigne.

#### 6.4.6. Amélioration de Prompt (`🪄 On`)
- Commutateur d'optimisation automatique qui enrichit les descriptions avec un vocabulaire photographique ou cinématique.

#### 6.4.7. Style d'Élocution (`📡 Stable` / `Expressive` en Lip Sync)
- `Stable` : Tête fixe, précision maximale sur les lèvres.
- `Expressive` : Micro-expressions vivantes et mouvements naturels de tête.

---

### 6.5. Bouton d'Action Circulaire (`↑`) & Suivi de Tâche
- **Bouton Circulaire Noir** avec flèche montante blanche `↑`.
- **Comportement au Clic** :
  1. Déclenchement immédiat de la tâche d'inférence asynchrone vers le worker de calcul.
  2. Le bouton passe en état de chargement léger.
  3. Une carte de suivi apparaît instantanément en haut de la galerie locale.
  4. La progression affiche le pourcentage, l'étape en cours et un bouton d'annulation.
  5. Dès l'achèvement, le fichier média est enregistré localement dans `outputs/` et la miniature s'active dans la galerie.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Suivi de Génération en Cours**  
> *Fichier attendu :* `ui-spec_generation_in_progress.png`  
> *Déclencheur :* Après le clic sur le bouton `↑`.  
> *Comportement :* Carte avec jauge d'avancement, étape de calcul et bouton d'interruption.  
> ![Placeholder: ui-spec_generation_in_progress.png](./ui-specifications/ui-spec_generation_in_progress.png)

---

## 7. Système Brand Kit (Identité de Marque & Contexte Automatisé)

*Captures de référence :* `Brand01.png`, `Brand02.png`, `Brand03.png`, `Brand04.png`, `Brand05.png`

Le **Brand Kit** permet à l'utilisateur de formaliser l'ADN complet d'une marque (logos, nuanciers de couleurs, typographies, images de référence et charte rédactionnelle) pour garantir une parfaite cohérence visuelle et sémantique lors des générations, sans avoir à ressaisir manuellement les consignes dans le prompt.

### 7.1. Point d'Entrée & Sélecteur Rapide (`Brand01.png`)

- **Bouton Déclencheur `@ Brand Kit`** :
  - Situé dans le coin supérieur droit du dock flottant, à côté du bouton de réglages fins `🎛️`.
  - Accessible également de manière contextuelle au clavier en tapant le caractère `@` dans la zone de texte du prompt.
- **Menu Popover « Brand kits »** :
  - S'ouvre sous le bouton `@ Brand Kit` avec un en-tête épuré comportant l'intitulé *Brand kits* et un bouton d'action `+` pour créer un nouveau kit.
  - Affiche la liste ordonnée des kits enregistrés avec pastille d'identification, nom (ex: *Apple*) et compteur d'actifs (ex: *15*).
- **Carte d'Aperçu au Survol (*Hover Card*)** :
  - Le survol d'une ligne de kit déclenche l'affichage d'un volet d'aperçu dynamique ancré à droite du popover.
  - Éléments visibles :
    - Grand visuel du logo principal de la marque (ex: logo Apple monochrome).
    - Nom de la marque en titre gras (ex: *Apple*).
    - Métadonnées de fraîcheur : nombre d'actifs et date de dernière modification (ex: *15 assets · Updated 2 minutes ago*).
    - Nuancier rapide des couleurs emblématiques (pastilles carrées noir, blanc, etc.).
- **Sélection et Insertion** :
  - Un clic sur un élément de la liste insère immédiatement un chip atomique `[@NomDuKit]` au sein du champ de texte.
  - Un seul kit peut être actif simultanément. La touche `Retour arrière` supprime l'intégralité du chip en une seule frappe.

### 7.2. Modale de Création d'un Brand Kit (`Brand02.png`, `Brand03.png`, `Brand04.png`)

Accessible via le bouton `+` du popover ou lors du premier lancement :
- **En-tête de la Modale** :
  - Titre : `Create brand kit`.
  - Indicateur de quota / progression : `○ 1 / 1 created` (ou nombre de kits créés).
  - Bouton de fermeture `✕`.
  - Sous-titre explicatif : *« Define your brand once, then use it generate on-brand assets. »*.
- **Sélecteur de Source Segmenté (`Create from`)** :
  Trois méthodes d'initialisation de marque :
  1. **Option Vierge (`[ Blank ]`, `Brand02.png`)** :
     - Affiche la consigne : *« You'll be able to add brand assets in the next step. »*.
     - Permet de démarrer un kit sans document préalable et de le renseigner manuellement.
  2. **Option Fichiers de Marque (`[ Brand files ]`, `Brand04.png`)** :
     - Déploie une fente de glisser-déposer (*dropzone*) avec icône d'envoi.
     - Libellé : *« Click or drag to upload »*.
     - Formats de fichiers pris en charge : *« PDFs, images, or Figma .fig files »*.
     - Permet l'extraction automatique de l'identité à partir d'une charte graphique existante.
  3. **Option Site Web (`[ Website ]`, `Brand03.png`)** :
     - Champ de saisie d'URL avec placeholder : `https://example.com`.
     - Libellé d'aide : *« We'll find the relevant brand assets, you can edit them later. »*.
     - Analyse automatiquement le site pour extraire les logos, le nuancier CSS et le résumé d'activité.
- **Bouton d'Action** :
  - Bouton pilule noir `[ Continue ]` ancré en bas à droite pour valider l'étape et passer à l'édition détaillée.

### 7.3. Volet d'Inspection & Gestion des Actifs (`Brand05.png`)

Dialogue grand format offrant une vue panoramique et un contrôle granulaire de l'ensemble des composantes de la marque :

#### 7.3.1. Volet Latéral de Navigation (Colonne Gauche)
- **Rubriques Disponibles** :
  - `Overview` (sélectionné par défaut) : Vue d'ensemble synthétique (description, logos majeurs, nuancier).
  - `Logos` : Bibliothèque exhaustive des variantes du logo (clair, sombre, monochrome, badges produit).
  - `Colors` : Palette de couleurs avec codes hexadécimaux et rôles (primaire, secondaire, fond, texte).
  - `Fonts` : Références typographiques de la marque (titres, corps de texte).
  - `Reference images` : Photothèque de référence incarnant la direction artistique et l'éclairage de la marque.
  - `Voices` : Profils de voix de synthèse associés pour les animations et le Lip sync.
  - `Captions` : Modèles de sous-titrage et signatures textuelles.
  - `Guidelines` : Règles d'or éditoriales et interdictions graphiques (*do's & don'ts*).
- **Bouton d'Action Ancré** :
  - Bouton pilule noir pleine largeur `[ Use this brand kit ]` en bas de la colonne pour appliquer immédiatement le kit en cours de consultation au dock flottant.

#### 7.3.2. Espace de Contenu & Éditorial (Zone Centrale)
- **Barre d'Actions Supérieure** :
  - Titre de la marque en grand format (ex: `Apple`).
  - Bouton `[ + Add ]` (pilule noire avec icône plus) pour ajouter de nouveaux actifs dans la section courante.
  - Bouton de menu d'options `[ ··· ]` (renommer le kit, dupliquer, modifier le brief, supprimer le kit).
  - Séparateur vertical `|` et bouton de fermeture `✕`.
- **Brief Narratif d'Identité de Marque** :
  - Paragraphe éditorial complet synthétisant le positionnement de la marque, son public cible, son ton de voix et sa signature visuelle (minimalisme, espace blanc, contraste, cadrage produit).
- **Section Logos (`Logos`)** :
  - Lien interactif `View all` en haut à droite de la section.
  - Grille horizontale de vignettes affichant les variantes de logos (fond blanc, fond transparent, sub-brands).
- **Section Couleurs (`Colors`)** :
  - Lien interactif `View all` en haut à droite de la section.
  - Nuancier de pastilles de couleurs avec prévisualisation fidèle des teintes.

### 7.4. Intégration dans le Prompt & Comportement d'Exécution
- Lorsque le chip `[@Apple]` est présent dans le prompt, l'utilisateur rédige son intention créative librement.
- Au clic sur le bouton d'exécution `↑` :
  - Aucun panneau de confirmation intrusif ne vient bloquer le flux de l'utilisateur.
  - L'identité de marque est résolue et compilée de manière fluide en arrière-plan.
  - Les emplacements de référence libres reçoivent en priorité les images de style de la marque et le logo officiel.

---

## 8. Pôle Dédié : Rehaussement de Résolution (*Upscaling*)

*Captures de référence :* `ui-spec-page.jpg`, `ui-spec_upscaling-image.png`, `ui-spec_upscaling-video.png`, `ui-spec_upscaling-video_scale.png`, `ui-spec_upscaling-video_quality.png`, `ui-spec_upscaling-video_frame-rate.png`

L'onglet **Upscaling** regroupe désormais l'ensemble des modèles de super-résolution et d'amélioration (image fixe ou séquence vidéo) au sein d'une même famille dédiée :

### 8.1. Parcours de Sélection du Modèle d'Upscale
1. Le clic sur l'onglet `Upscaling` filtre automatiquement le sélecteur de modèles sur la catégorie des modèles de rehaussement (qu'ils traitent de l'image ou de la vidéo).
2. L'utilisateur choisit le modèle d'upscaling souhaité dans la liste.
3. **Adaptation contextuelle selon la nature du modèle choisi** :
   - **Si un modèle d'upscaling image est sélectionné** (ex: *Topaz Image Upscale*, voir `ui-spec_upscaling-image.png`) :
     - Le dock présente la fente de dépôt d'image source.
     - Les pilules de temporalité ou de framerate sont masquées.
     - Le dock affiche la pilule du modèle, la pilule du facteur d'agrandissement (`⊕ 2x`) et le bouton d'accès rapide aux réglages fins `🎛️`.
   - **Si un modèle d'upscaling vidéo est sélectionné** (ex: *Topaz Video Upscale*, voir `ui-spec_upscaling-video.png`) :
     - Le dock présente la fente de dépôt de la vidéo source.
     - Le dock affiche les 4 pilules spécifiques au traitement vidéo :
       1. **Modèle** : Nom du modèle d'upscaling vidéo.
       2. **Qualité (`Quality`)** : `Fast` ("Fastest, good quality") ou `Precise` ("Highest quality, will take longer").
       3. **Facteur d'échelle (`Upscale`)** : `1.25x`, `1.5x`, `2x`, `3x`, `4x`.
       4. **Fréquence d'images (`Frame rate`)** : `Same as source`, `24 fps`, `25 fps`, `30 fps`, `48 fps`, `50 fps`, `60 fps`.
     - Le bouton `🎛️` permet d'accéder aux réglages de débruitage temporel et de fluidification.

> [!NOTE]  
> **Zone Réservée — Image Manquante : Volets de Réglages Fins Upscaling**  
> *Fichiers attendus :* `ui-spec_topaz-image_settings.png`, `ui-spec_topaz-video_settings.png`  
> *Déclencheur :* Clic sur le bouton `🎛️` en mode Upscaling.  
> ![Placeholder: ui-spec_topaz-video_settings.png](./ui-specifications/ui-spec_topaz-video_settings.png)

---

## 9. Inventaire Consolidé des Captures d'Écran

### 9.1. Captures d'Illustration Existantes (24 fichiers)

| Fichier Image | Rôle Ergonomique & Éléments Illustrés |
| :--- | :--- |
| `ui-spec-page.jpg` | **Maquette maîtresse** : vue d'ensemble complète avec en-tête (Sidebar, Ask, Dossier, Cloche, Profil), recherche, filtres, cartes de galerie types et dock flottant avec les 4 onglets (`Image`, `Video`, `Lip sync`, `Upscaling`). |
| `ui-spec_lip-sync_model-selector-clean.jpeg` | **Maquette épurée du sélecteur de modèle** : structure générique `MODEL-NAME`, descriptifs, filtres et les 4 onglets de catégorie. |
| `Brand01.png` | **Sélecteur Brand Kit & Aperçu Hover** : bouton `@ Brand Kit`, popover de liste avec compteur d'assets et carte de survol détaillée (logo Apple, fraîcheur, palette). |
| `Brand02.png` | **Modale de création Brand Kit (Vierge)** : sélection de source `Blank`, sous-titre incitatif et bouton continuer. |
| `Brand03.png` | **Modale de création Brand Kit (Site Web)** : sélection `Website`, champ URL avec extraction automatique d'actifs. |
| `Brand04.png` | **Modale de création Brand Kit (Fichiers)** : sélection `Brand files`, zone glisser-déposer pour PDF, images ou fichiers Figma `.fig`. |
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
