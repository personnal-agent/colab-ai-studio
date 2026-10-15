# Execution Plan: Retouche Normative des Diagrammes UML (11/11) & Documentation

## 📋 Target Invariant & Pre-requisites
- **Target Invariant**: Les 11 diagrammes SVG et PNG sous `.modelisation/logiciel/diagrammes/` ainsi que `.modelisation/logiciel/README.md` respectent rigoureusement les arbitrages d'ingénierie logicielle de Colab AI Studio. Aucune modification hors périmètre n'est introduite.
- **Pre-requisites**: Convertisseur ImageMagick/GraphicsMagick disponible (`convert -density 150`); analyseur XML Python (`xml.etree.ElementTree`); intégrité du dépôt préservée.

## 🛠️ Step-by-Step Sequence

### Step 1: Corriger le Diagramme 01 (Cas d'utilisation) & Régénérer son PNG
- [x] **Action**: Retoucher `01-perimetre-fonctionnel.svg` selon Fiche 01 (rectangle système local, acteurs secondaires Colab et Service LLM à droite, Client API externe à gauche, suppression note Colab interne).
- [x] **Verify**: Validation XML ElementTree et régénération de `01-perimetre-fonctionnel.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 211K 11 oct. 16:11 .modelisation/logiciel/diagrammes/01-perimetre-fonctionnel.png
Dimensions: 1440x1100 -> PNG valide
```

### Step 2: Corriger le Diagramme 02 (Composants) & Régénérer son PNG
- [x] **Action**: Retoucher `02-composants.svg` selon Fiche 02 (élargissement canal ≥ 180px, port pLlmOut vers Service LLM externe, composant MediaFileStore interne avec rôle MediaAssetManager, redimensionnement boîte Orchestrateur Asynchrone, connecteurs internes déroutés).
- [x] **Verify**: Validation XML ElementTree et régénération de `02-composants.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 355K 11 oct. 16:13 .modelisation/logiciel/diagrammes/02-composants.png
Canal Frontend <-> Backend élargi à 190px, 7 parties dans Backend (Plafond de Miller).
```

### Step 3: Corriger le Diagramme 03 (Déploiement) & Régénérer son PNG
- [x] **Action**: Retoucher `03-deploiement.svg` selon Fiche 03 (rapatriement IDE dans station hôte locale, stéréotype `«externe» Infrastructure Cloud Fournisseur LLM`, ligne Python déroutée dans l'interstice sans barrer `outputs/`, viewport et légende dégagés).
- [x] **Verify**: Validation XML ElementTree et régénération de `03-deploiement.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 344K 11 oct. 16:15 .modelisation/logiciel/diagrammes/03-deploiement.png
IDE local intégré, zéro traversée abusive sur outputs/.
```

### Step 4: Corriger le Diagramme 04 (Classes) & Régénérer son PNG
- [x] **Action**: Retoucher `04-modele-de-donnees.svg` selon Fiche 04 (ajout `«enumeration» TaskStatus`, attributs `status: TaskStatus`, `filePath: Path [0..1]`, `progress [0..1]`, `errorMessage [0..1]` sur `Generation`, dégagement des multiplicités et boîtes).
- [x] **Verify**: Validation XML ElementTree et régénération de `04-modele-de-donnees.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 549K 11 oct. 16:18 .modelisation/logiciel/diagrammes/04-modele-de-donnees.png
TaskStatus insérée avec + pending, + running, + completed, + failed, + cancelled. Multiplicités dégagées.
```

### Step 5: Corriger le Diagramme 05 (Activité) & Régénérer son PNG
- [x] **Action**: Retoucher `05-activite-generation.svg` selon Fiche 05 (nettoyage des 4 losanges de décision, libellés d'actions métier normés `Demander l'annulation...`, `Transmettre la demande...`, région d'activité interruptible).
- [x] **Verify**: Validation XML ElementTree et régénération de `05-activite-generation.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 243K 11 oct. 16:20 .modelisation/logiciel/diagrammes/05-activite-generation.png
4 losanges nettoyés, interruption normée «interruptible activity region» avec arc en éclair.
```

### Step 6: Corriger le Diagramme 06 (Séquence Génération) & Régénérer son PNG
- [x] **Action**: Retoucher `06-sequence-generation.svg` selon Fiche 06 (`demanderGeneration(...)`, `demanderAnnulation(...)`, flèche c vers :ReactSPA pour annulation, notification progression métier, lignes de vie de persistance alignées).
- [x] **Verify**: Validation XML ElementTree et régénération de `06-sequence-generation.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 243K 11 oct. 16:22 .modelisation/logiciel/diagrammes/06-sequence-generation.png
Messages métier de domaine, persistance alignée sur :MediaFileStore.
```

### Step 7: Corriger le Diagramme 07 (Séquence Contexte Marque) & Régénérer son PNG
- [x] **Action**: Retoucher `07-sequence-brand-context.svg` selon Fiche 07 (remplacer `:FloatingPromptDock` par `:ReactSPA`, routage `:ReactSPA` -> `:FastAPIBackend` -> `:BrandContextCompiler`, retour `compiledContext` puis émission vers Colab, fond blanc opaque sur auto-appels).
- [x] **Verify**: Validation XML ElementTree et régénération de `07-sequence-brand-context.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 285K 11 oct. 16:25 .modelisation/logiciel/diagrammes/07-sequence-brand-context.png
Médiation FastAPI respectée, Loi de Déméter appliquée, auto-appels protégés.
```

### Step 8: Corriger le Diagramme 08 (Séquence Proxy LLM) & Régénérer son PNG
- [x] **Action**: Retoucher `08-sequence-proxy-llm.svg` selon Fiche 08 (remplacer stickman par rectangle d'acteur système `«system» client : ClientAPI`, restructurer l'interruption en `alt` exhaustif au lieu du `break` contradictoire, ajuster le titre et marges).
- [x] **Verify**: Validation XML ElementTree et régénération de `08-sequence-proxy-llm.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 258K 11 oct. 16:27 .modelisation/logiciel/diagrammes/08-sequence-proxy-llm.png
Acteur système normé, alt exhaustif évitant toute émission parasite sur socket fermée.
```

### Step 9: Corriger le Diagramme 09 (États Dock) & Régénérer son PNG
- [x] **Action**: Retoucher `09-etats-dock-adaptatif.svg` selon Fiche 09 (nommage `ModeImageSelectionne`, préservation de [H] et transitions internes, déroutement de la transition vers la gauche avec 25px de dégagement).
- [x] **Verify**: Validation XML ElementTree et régénération de `09-etats-dock-adaptatif.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 336K 11 oct. 16:27 .modelisation/logiciel/diagrammes/09-etats-dock-adaptatif.png
Transition déroutée largement à gauche (x=60), dégagement > 25px par rapport à la boîte jaune (x=175).
```

### Step 10: Corriger le Diagramme 10 (États Tâche Média) & Régénérer son PNG
- [x] **Action**: Retoucher `10-etats-tache-media.svg` selon Fiche 10 (suppression des FinalState vers états terminaux stables, syntaxe `after(120 s) [sans worker disponible]`, correction actions internes `exit` et fusion `do`, élargissement canevas).
- [x] **Verify**: Validation XML ElementTree et régénération de `10-etats-tache-media.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 325K 11 oct. 16:29 .modelisation/logiciel/diagrammes/10-etats-tache-media.png
États terminaux stables (Terminee, Annulee, Echouee) sans FinalState, after(120 s) normé, do fusionné, canevas à 1980px avec portées de 120px.
```

### Step 11: Corriger le Diagramme 11 (États Model Swapper) & Régénérer son PNG
- [x] **Action**: Retoucher `11-etats-model-swapper.svg` selon Fiche 11 (transition initiale sans événement `initialiser()`, renommage `EnRecuperationSaturation` et suppression garde redondante, réarmement timer interne, `after(delaiInactivite)`, nettoyage du pseudo-état de choix en `[else]`).
- [x] **Verify**: Validation XML ElementTree et régénération de `11-etats-model-swapper.png`.
- **Verification Proof**:
```text
XML OK
-rw-rw-r-- 1 omni omni 266K 11 oct. 16:31 .modelisation/logiciel/diagrammes/11-etats-model-swapper.png
Transition / initialiser(), EnRecuperationSaturation, after(delaiInactivite), [else] épuré et cartouche OOM décollée.
```

### Step 12: Synchroniser le README d'Architecture
- [x] **Action**: Mettre à jour `.modelisation/logiciel/README.md` (aligner acteurs, rôles des composants dont MediaFileStore, types dont TaskStatus et contrats avec les 11 diagrammes corrigés).
- [x] **Verify**: Relecture de cohérence globale et vérification de la matrice de traçabilité.
- **Verification Proof**:
```text
Matrice de traçabilité mise à jour avec TaskStatus, MediaFileStore, ReactSPA et contrats alignés sur les 11 diagrammes retouchés.
```

### Step 13: Contrôle Qualité Global & Intégrité du Dépôt
- [x] **Action**: Exécuter les commandes de validation du dépôt (`python3 -m py_compile .github/scripts/*.py`, inspection git diff et git status).
- [x] **Verify**: 0 fichier hors périmètre modifié, 11 paires SVG/PNG valides, 1 README synchronisé.
- **Verification Proof**:
```text
Compiles clean: python3 -m py_compile .github/scripts/*.py (Exit code: 0)
11/11 SVGs parsables sans erreur XML.
11/11 PNGs générés avec succès (> 200 Ko chacun).
```

## ⚠️ Mitigations & Edge Cases
- **Risk**: Collision graphique SVG lors de l'ajout d'éléments ou élargissement de conteneurs.
- **Mitigation**: Recalcul précis des coordonnées X/Y, incrémentation cohérente des largeurs (viewBox/width) et validation visuelle via les dimensions et rendus PNG.
- **Risk**: Dépassement mémoire lors des conversions multiples d'images sur machine modeste.
- **Mitigation**: Exécution séquentielle stricte diagramme par diagramme (`convert -density 150`), surveillance `free -m`.
