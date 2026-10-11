# Registre d'Arbitrage et de Corrections Normatives UML (Audit Exhaustif 11/11)

> **Référentiel Méthodologique & Normatif** : Spécification Internationale **OMG UML 2.5.1** & Référentiel Universitaire **L3 MIAGE** (*Initiation au Langage UML*, Dr TRAORÉ Obonan Étienne, IUA).  
> **Source de l'audit** : Rapprochement contradictoire direct des **11 rapports d'audit normatifs indépendants** issus des transcripts agents (`scratch/audits/Diag_01.md` à `Diag_11.md`) et de l'arbitrage utilisateur sur la frontière Colab.  
> **Intégrité du dépôt** : **0 fichier SVG/PNG modifié** avant validation formelle et lancement de la phase d'exécution.

---

## 🧭 Typologie des Arbitrages et Pièges Démasqués

L'analyse intégrale des 11 rapports d'audit des sous-agents a révélé que plusieurs propositions initiales constituaient des **pièges de barème ou des anti-patrons académiques** selon le cours L3 MIAGE et la norme OMG UML 2.5.1 :

1. **Anti-patrons rejetés / Sanctions évitées** :
   - *Gestes d'interface physique dans les modèles dynamiques* : Remplacer les clics (`clickGenerate`, `clickAnnuler`, `Cliquer sur Annuler`) par des intentions/opérations métier (`demanderGeneration`, `demanderAnnulation`). *(Erreurs n°5 & n°6, Vol 3 p. 89 & Erreur n°8, Vol 4 p. 90)*.
   - *Confusion entre état final et état terminal* : Relier des entités persistées (`Terminee`, `Annulee`, `Echouee`) à un `FinalState` (disque cerclé de destruction). Une tâche conservée en base `generations.json` ne cesse pas d'exister. De plus, la transition d'achèvement détruisait l'idempotence interne d'`Annulee` ! *(Erreur n°21, Vol 5 p. 123)*.
   - *Douille orpheline sans composant fournisseur* : Poser une interface requise `ILlmEngine` dans le vide sans matérialiser en vis-à-vis le composant cible externe. *(Règle de complétude, Vol 6 p. 54)*.
   - *Cumul illégal de métaclasses disjointes* : L'annotation `«device» / «executionEnvironment»` est un barbarisme métamodélique. *(OMG UML §19.4)*.
   - *Impossibilité physique réseau* : Modéliser le `Client IDE tiers` comme un nœud matériel séparé mais connecté en `Loopback 127.0.0.1`.
   - *Type primitif ouvert pour cycle de vie fini* : Remplacer `status : String` par une énumération formelle `«enumeration» TaskStatus`. *(Erreur n°7, Vol 2 p. 99)*.
   - *Déclencheur sur transition initiale* : Le pseudo-état initial ne peut JAMAIS porter d'événement (*trigger* `initialiser()`). *(OMG UML §14.4.4.4 & QCM 79)*.
   - *Contradiction sémantique du fragment `break`* : Un `break` imbriqué dans `loop` court-circuite la boucle mais retombe sur la phase 3 nominale (`data: [DONE]`), créant une incohérence logique.
   - *Figurine humaine (stickman) pour un système logiciel* : `ClientTiers` doit être un rectangle d'instance d'acteur système `«system»`. *(OMG UML §17.3 & Vol 3 Annexe D)*.

---

## 📌 Fiche 01 — Diagramme 01 : Périmètre Fonctionnel (Cas d'Utilisation)

- **Fichiers cibles** : `01-perimetre-fonctionnel.svg` & `01-perimetre-fonctionnel.png`
- **Sujet du système (*System Under Design*)** : **Application Studio Locale (UI React + Orchestrateur FastAPI)**

### 1. Synthèse de l'Audit Agent & Arbitrage Utilisateur
- **Frontière système & Statut de Colab** :
  - *Constat de l'auditeur* : Le code de gestion Colab (`ColabClient`, worker endpoints) est versionné dans le dépôt du projet. L'auditeur préconisait de conserver Colab dans la boîte frontière pour ne pas traiter le worker comme une boîte noire externe (alors que sa structure interne est détaillée en 02 et 11).
  - *Arbitrage Utilisateur (Confirmé)* : Dissociation rigoureuse : **le code local de pilotage Colab reste à l'intérieur** de la boîte système (dans le backend FastAPI), mais **Google Colab en tant qu'environnement distant de calcul GPU** (infrastructure cloud hébergée chez Google) est noté comme **Acteur Externe Secondaire** à droite du système.
- **Positionnement de l'Acteur `Client API externe`** :
  - *Règle L3 MIAGE (Slide 30 Règle n°5 & Slide 44 Étape 2)* : L'acteur principal est celui qui initie l'action ; les acteurs principaux se placent à **gauche** par convention. Le client API externe (IDE Cursor/Continue) initie les requêtes de complétion `/v1/chat/completions`. Il doit être qualifié d'acteur principal non-humain et placé à gauche.
- **Service d'inférence LLM** :
  - *Règle L3 MIAGE (Slide 29 & 50)* : Le nom d'un acteur désigne un rôle fonctionnel, pas une technologie. Renommer « Fournisseur LLM » en **`«actor» Service d'inférence LLM (Local / Cloud)`**, positionné en acteur secondaire à droite.
- **Rejet de l'acteur "Moteur Local Média"** :
  - *Règle L3 MIAGE (Slide 49 Contrôle n°4)* : Le mode local média répondant `501 Not Implemented`, créer un acteur pour ce mode violerait le principe de non-inventivité.
- **Liaison du cas UC-08 "Connecter l'environnement distant"** :
  - Ce cas représente la saisie de l'URL du tunnel par le créateur. Ne pas y relier l'acteur Colab (ce n'est pas Colab qui prend la décision fonctionnelle).

### 2. Actions de Retouche SVG / PNG
1. Délimiter le rectangle `«system» Colab AI Studio (Application Locale)`.
2. Positionner à droite les deux acteurs secondaires : `«actor» Google Colab (Worker GPU distant)` et `«actor» Service d'inférence LLM (Local / Cloud)` (sous forme de rectangles stéréotypés `«actor»`).
3. Déplacer l'acteur `«actor» Client API externe` à gauche (relié à *« Interagir avec l'assistant textuel IA »*).
4. Maintenir les liaisons fonctionnelles sans croisement de lignes.

---

## 📌 Fiche 02 — Diagramme 02 : Architecture Logique (Composants)

- **Fichiers cibles** : `02-composants.svg` & `02-composants.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Port de sortie Proxy LLM & Règle de clôture** :
  - *Règle L3 MIAGE (Vol 6 p. 54)* : *« Vérification : Chaque interface requise a un fournisseur. »* Une douille flottant dans le vide est interdite.
  - *Action validée* : Poser le port requis `pLlmOut` sur le Backend avec l'interface requise (douille) `ILlmEngine`. Modéliser en vis-à-vis le composant cible `«component» Service d'Inférence LLM <<externe>>` exposant la boule correspondante (assemblage ball-and-socket).
- **Intégration de `MediaFileStore` & Distinction Logique vs Physique** :
  - *Règle L3 MIAGE (Vol 6 p. 21 & p. 49)* : BANNIR absolument l'expression "stockage physique" dans une vue logique de composants. Les composants sont des briques logicielles, les disques sont des nœuds de déploiement.
  - *Action validée* : Ajouter `«component» MediaFileStore` avec le rôle **`rôle : MediaAssetManager`** (gestion des flux binaires dans `outputs/` et projets).
- **Plafond de Miller [3..7] parties internes (Slide 17 & 26)** :
  - Le backend passe de 6 à **exactement 7 parties internes** (`API Locale`, `Orchestrateur Asynchrone`, `BrandContextCompiler`, `Proxy LLM`, `ColabClient`, `JSONDocumentStore`, `MediaFileStore`). Le seuil maximal de granularité est respecté.
- **Câblage interne de `MediaFileStore`** :
  - Connecteur depuis `Orchestrateur Asynchrone` / `ColabClient` : `saveBinaryStream` (écriture médias).
  - Connecteur depuis `API Locale` : `resolveMediaPath` (résolution chemins et streaming).

### 2. Actions de Retouche SVG / PNG
1. Élargir le canal inter-systèmes Frontend ↔ Backend (≥ 180px) pour supprimer 100% des collisions de ports et de contrats.
2. Ajouter le port `pLlmOut` avec connecteur d'assemblage vers le composant externe `Service d'Inférence LLM`.
3. Intégrer `MediaFileStore` à l'intérieur du Backend local sans dépasser les bordures.
4. Redimensionner la boîte `Orchestrateur Asynchrone` pour dégager le mot "Asynchrone" de l'icône de composant.
5. Dérouter les connecteurs internes par les couloirs libres sans traverser les boîtes de composants.

---

## 📌 Fiche 03 — Diagramme 03 : Topologie Physique (Déploiement)

- **Fichiers cibles** : `03-deploiement.svg` & `03-deploiement.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Rejet du cumul `«device» / «executionEnvironment»`** :
  - *Règle OMG UML §19.4* : `Device` (matériel) et `ExecutionEnvironment` (logiciel hôte/runtime) sont disjoints. Leur fusion par slash est un contresens.
- **Anomalie réseau critique démasquée sur le Client IDE (Nœud 3)** :
  - Le `Poste Client / IDE Développeur` était modélisé comme une machine physique distincte mais relié en `Loopback 127.0.0.1:8000`. C'est physiquement impossible sur un réseau.
  - *Action validée* : Rapatrier l'IDE tiers comme sous-nœud `«executionEnvironment» IDE Développeur (Cursor / VSCode)` **à l'intérieur** du `«device» Station de travail locale (Hôte PC)`.
- **Modélisation du Nœud LLM (Nœud 4)** :
  - Remplacer le stéréotype non normé `«device» (Externe / Optionnel)` par **`«externe» Infrastructure Cloud Fournisseur LLM`** (avec sous-nœud `«executionEnvironment» Cloud API Gateway`).
  - La multiplicité `0..1` sur la liaison de communication exprime rigoureusement son caractère optionnel.
- **Stockage physique local & artefacts** :
  - Les partitions `data/*.json` et `outputs/` sont des répertoires du système de fichiers hôte, pas des nœuds d'exécution autonomes.

### 2. Actions de Retouche SVG / PNG
1. Rapatrier l'environnement de l'IDE à l'intérieur de la Station de travail locale.
2. Dérouter le tracé de la ligne reliant l'environnement Python au stockage local pour qu'elle passe dans l'interstice libre sans barrer le texte `outputs/`.
3. Élargir le viewport SVG à droite pour afficher intégralement la légende sans rognage.

---

## 📌 Fiche 04 — Diagramme 04 : Modèle de Données Métier (Classes)

- **Fichiers cibles** : `04-modele-de-donnees.svg` & `04-modele-de-donnees.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Typage de l'état d'exécution (`status`)** :
  - *Règle L3 MIAGE (Vol 2 p. 31 & Erreur n°7 p. 99)* : Proscription absolue du type primitif ouvert `String` pour une liste finie d'états.
  - *Action validée* : Créer la classe formelle **`«enumeration» TaskStatus`** avec les littéraux :
    `+ pending`, `+ running`, `+ completed`, `+ failed`, `+ cancelled`.
    Typer l'attribut sur `Generation` : `- status : TaskStatus`.
- **Multiplicités des attributs de `Generation`** :
  - `filePath : Path [0..1]` : optionnel car inexistant lors de la création ou en cas d'échec (conforme à la règle `dateClôture [0..1]`, Vol 2 p. 101).
  - `progress : Integer [0..1]` : présent pendant l'exécution asynchrone.
  - `errorMessage : String [0..1]` : support naturel de l'opération `markFailed(reason : String)`.
- **Association `Project` ➔ `BrandKit`** :
  - Déjà présente dans le SVG source (L333-340) en association simple navigable (`0..*` vers `0..1`, rôle `+activeBrandKit`). La préserver contre le risque d'une fausse composition (le BrandKit est partagé entre projets, losange plein interdit).

### 2. Actions de Retouche SVG / PNG
1. Dessiner la boîte `«enumeration» TaskStatus` et la positionner à proximité de `Generation`.
2. Mettre à jour les attributs de `Generation` (`status: TaskStatus`, `filePath: Path [0..1]`, etc.).
3. Rehausser `«singleton JSON»` pour supprimer le chevauchement avec `StudioConfig`.
4. Espacer verticalement les multiplicités `0..*` et `0..1` à droite de `StudioConfig`.
5. Surélever la ligne vers `BrandKitSnapshot` pour dégager le haut de `GenerationParameters`.

---

## 📌 Fiche 05 — Diagramme 05 : Flux d'Activité (Génération Média)

- **Fichiers cibles** : `05-activite-generation.svg` & `05-activite-generation.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Bannissement des gestes d'interface physique** :
  - *Règle L3 MIAGE (Vol 4 p. 90 Erreur 8)* : « Cliquer sur un bouton » est un geste d'interface sanctionné. Remplacer impérativement par l'action métier intentionnelle : **`Demander l'annulation de la génération`**.
- **Bannissement des signatures d'API techniques brutes** :
  - *Règle L3 MIAGE (Vol 4 p. 89 Erreur 7)* : Écrire `POST /api/tasks/{id}/cancel` dans une boîte d'activité mélange les niveaux d'abstraction. Remplacer par : **`Transmettre la demande d'annulation`** (ou émission du signal `«signal» DemandeAnnulation`).
- **Sémantique de l'interruption à tout moment (Règle d'or Dr Traoré)** :
  - *Règle L3 MIAGE (Slide 20 & Tableau 4 p. 199)* : Une annulation asynchrone à tout moment ne se traite pas par un simple `DecisionNode` (qui ne peut pas écouter d'événement à distance).
  - *Approche recommandée* : Encadrer la phase d'exécution asynchrone par une **Région d'Activité Interruptible** (`InterruptibleActivityRegion`, cadre arrondi en pointillés fins) d'où part une flèche en éclair (zigzag) vers la libération des buffers VRAM et le marquage `cancelled`.
  - *Alternative pragmatique* : Action de signal `AcceptEventAction` avec garde `[signal d'annulation reçu]`.

### 2. Actions de Retouche SVG / PNG
1. Nettoyer intégralement les textes pollués sur les 4 losanges de décision (supprimer `e [colab]`, `B [non]`, `M [oui]`, `É [annulée]`).
2. Remplacer les libellés d'actions par les termes métier normés dans la partition Créateur et SPA.
3. Matérialiser la région d'activité interruptible ou l'arc de signal vers la libération des ressources.

---

## 📌 Fiche 06 — Diagramme 06 : Séquence (Génération Asynchrone)

- **Fichiers cibles** : `06-sequence-generation.svg` & `06-sequence-generation.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Bannissement des clics d'interface (Erreurs n°5 & n°6, Vol 3 p. 89)** :
  - Message 1 : `clickGenerate(prompt, config)` (ligne 108 du SVG actuel) ➔ Remplacer par **`demanderGeneration(prompt, config)`** ou `lancerGeneration(...)`.
  - Message dans `alt` : `clickAnnuler()` ➔ Remplacer par **`demanderAnnulation(taskId)`**.
- **Qualification du flux d'événements Colab ➔ Backend** :
  - *Règle L3 MIAGE (Vol 3 p. 89 Erreur 10)* : Ne pas descendre au niveau du protocole réseau en nommant l'opération `streamChunk` (confusion de niveaux d'abstraction).
  - *Action validée* : Conserver la flèche asynchrone `:ColabWorker` ➔ `:FastAPIBackend` avec le signal métier : `notifierProgression(pct, step)` et qualifier le streaming chunked descendant en note ou stéréotype `«stream»`.
- **Harmonisation de la ligne de vie de stockage (Contrôle n°1, Slide 29)** :
  - Une ligne de vie doit instancier un classifieur formel du modèle structurel.
  - *Action validée* : Remplacer `:StorageManager` par les composants réels du diagramme 02 (`:MediaFileStore` pour le rapatriement binaire et `:JSONDocumentStore` pour la mise à jour documentaire), ou formaliser une façade explicite.

### 2. Actions de Retouche SVG / PNG
1. Remplacer `clickGenerate` et `clickAnnuler` par des opérations de domaine.
2. Ajouter la flèche d'annulation depuis `c : Créateur` vers `:ReactSPA`.
3. Aligner le nommage des lignes de vie de persistance.
4. Nettoyer l'en-tête de garde du fragment `alt [annulation demandée]` de toute collision graphique.

---

## 📌 Fiche 07 — Diagramme 07 : Séquence (Compilation du Contexte de Marque)

- **Fichiers cibles** : `07-sequence-brand-context.svg` & `07-sequence-brand-context.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Statut de `BrandContextCompiler` & Loi de Déméter (Erreur 11)** :
  - *Constat de l'auditeur* : Dans le modèle actuel, `BrandContextCompiler` contactait directement `:ColabWorker` et recevait le `202 Accepted`. C'était un anti-patron (*God Object*) en contradiction flagrante avec les diagrammes 02 et 06.
  - *Action validée* : `:ReactSPA` contacte le contrôleur d'API `:FastAPIBackend`. Celui-ci appelle le service interne `BrandContextCompiler.compile(...)`, qui lit le Brand Kit (`:StorageManager`), interroge `:LLMProvider` (externe), applique les règles de repli, et retourne `compiledContext` au backend. C'est le backend qui émet ensuite `POST /infer` vers Colab.
- **Suppression de l'écran spécifique en ligne de vie (Erreur n°2, -1,5 pt)** :
  - Remplacer `:FloatingPromptDock` par le composant architectural global **`:ReactSPA`**.

### 2. Actions de Retouche SVG / PNG
1. Remplacer `:FloatingPromptDock` par `:ReactSPA`.
2. Router la séquence : `:ReactSPA` ➔ `:FastAPIBackend` ➔ `:BrandContextCompiler`.
3. Dessiner la flèche de retour `compiledContext` vers `:FastAPIBackend`, suivie de `POST /infer` vers `:ColabWorker`.
4. Protéger les blocs d'auto-appels avec un fond blanc opaque pour supprimer le tranchage par la ligne verticale de `:StorageManager`.

---

## 📌 Fiche 08 — Diagramme 08 : Séquence (Proxy LLM Streaming)

- **Fichiers cibles** : `08-sequence-proxy-llm.svg` & `08-sequence-proxy-llm.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Remplacement de la figurine stickman (OMG UML §17.3 & Vol 3 Annexe D)** :
  - Le stickman est réservé aux humains. `ClientTiers` est un système logiciel : le remplacer par un rectangle d'instance d'acteur **`«system» client : ClientAPI`**.
  - Ajouter une note UML précisant la double consommation (client tiers externe type Cursor/Continue ou SPA locale).
- **Correction de la contradiction critique du fragment `break` (OMG UML §17.12.15.3)** :
  - Dans le modèle actuel, le `break [déconnexion client]` imbriqué dans `loop` court-circuitait la boucle mais retombait sur la Phase 3 nominale (`data: [DONE]`), affirmant que le système envoyait des tokens de complétion sur une socket fermée !
  - *Action validée (Standard L3 MIAGE)* : Restructurer la cinématique avec un opérateur **`alt`** exhaustif :
    - Branche nominale `[tokens disponibles]` : boucle `loop` de streaming + message de clôture `[DONE]`.
    - Branche d'interruption `[déconnexion client / AbortSignal]` : signal d'interruption, libération VRAM/GPU, fermeture immédiate.
- **Clarification du titre** : *« Séquence — Proxy LLM Streaming (Inférence distante Colab & Annulation AbortSignal) »*.

### 2. Actions de Retouche SVG / PNG
1. Dessiner le rectangle d'instance `«system» client : ClientAPI` à la place du stickman.
2. Restructurer le streaming et l'annulation avec l'opérateur `alt`.
3. Décaler le sous-titre de l'en-tête pour supprimer la collision avec la bordure supérieure.
4. Élargir le cadre de texte de note en pied de page pour supprimer le rognage droit.

---

## 📌 Fiche 09 — Diagramme 09 : Machine à États (Dock Adaptatif)

- **Fichiers cibles** : `09-etats-dock-adaptatif.svg` & `09-etats-dock-adaptatif.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Renommage normé de l'état image (Test du nom, Vol 5 p. 16)** :
  - Renommer `ModelImageSelectionne` en **`ModeImageSelectionne`** (règle du participe passé/adjectif).
- **Maintien du pseudo-état d'historique `[H]` (Shallow History)** :
  - *Règle L3 MIAGE (Vol 5 p. 117 & 123)* : Son omission est sanctionnée de **-2 points** ! Il permet au dock de retrouver son mode actif (ex. vidéo) après la génération sans réinitialiser arbitrairement en mode image par défaut.
- **Maintien des transitions internes (Slide 16 & Erreur n°7)** :
  - Évite le piège de l'auto-transition qui réinitialise `entry` et provoquerait en React un démontage/remontage destructif du composant.
- **Factorisation de `quitterApplication()`** :
  - Attacher la transition au niveau de l'état englobant pour éviter les croisements inesthétiques de multiples flèches.

### 2. Actions de Retouche SVG / PNG
1. Renommer `ModelImageSelectionne` en `ModeImageSelectionne`.
2. Conserver précieusement `[H]` et les transitions internes.
3. Dérouter vers la gauche la transition `selectModel [type != LLM]` pour contourner la boîte jaune avec un dégagement de 25px.

---

## 📌 Fiche 10 — Diagramme 10 : Machine à États (Tâche Média)

- **Fichiers cibles** : `10-etats-tache-media.svg` & `10-etats-tache-media.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Suppression formelle des transitions vers `FinalState` (Erreur n°21 du Dr Traoré)** :
  - *Règle L3 MIAGE (Vol 5 p. 123)* : Ne pas confondre fin de traitement et destruction de l'objet. Une tâche terminée, annulée ou échouée est conservée dans `data/generations.json` et consultable dans la galerie.
  - *Correction critique* : Supprimer les disques `FinalState` et les flèches d'achèvement. `Terminee`, `Annulee` et `Echouee` sont des **états terminaux stables sans transition sortante**. Cela restaure immédiatement l'idempotence interne d'`Annulee` (`annuler() [deja_annule]`).
- **Correction de la syntaxe de timeout (Question 84 & Vol 5 p. 125)** :
  - Remplacer `when(delai > 120s)` par l'événement temporel normé : **`after(120 s) [sans worker disponible]`**.
- **Correction des actions internes** :
  - Dans `EnAttentePriseEnCharge` : remplacer le contresens `exit / enregistrerDebutAttente()` par `exit / enregistrerFinAttente()`.
  - Dans `SauvegardeEnCours` : fusionner les deux clauses `do /` illégales en une seule : `do / ecrireFichierEtPersisterJSON()`.

### 2. Actions de Retouche SVG / PNG
1. Supprimer les disques `FinalState` et figer les trois états terminaux.
2. Corriger le timeout en `after(120 s)`.
3. Corriger les actions internes (`exit` et fusion du `do`).
4. Élargir l'espacement horizontal inter-boîtes (+260px au canevas) pour offrir 110px de portée aux flèches et afficher les étiquettes de transition nominales sans rognage.

---

## 📌 Fiche 11 — Diagramme 11 : Machine à États (Model Swapper)

- **Fichiers cibles** : `11-etats-model-swapper.svg` & `11-etats-model-swapper.png`

### 1. Synthèse de l'Audit Agent & Règles MIAGE
- **Violation critique sur la transition initiale (OMG UML §14.4.4.4 & QCM 79)** :
  - Une transition issue d'un pseudo-état initial ne peut JAMAIS comporter d'événement déclencheur (*trigger* `initialiser()`).
  - *Correction obligatoire* : Arc muet spontané ou effet explicite précédé d'un slash : **`/ initialiser()`**.
- **Renommage de l'état de saturation (Erreur n°3, Vol 5 p. 119)** :
  - `RecuperationSaturationMemoire` est un substantif d'action. Renommer en adjectif/participe : **`EnRecuperationSaturation`**.
  - Supprimer la garde redondante `[cache_purge]`.
- **Réarmement explicite du timer dans la transition interne** :
  - Dans `ModeleActif`, préciser : `requeteRecue(m) [m == active_model] / reutiliserPipeline(); rearmerTimer()`.
- **Épuration de la transition de timeout** :
  - Remplacer `timerInactiviteExpire [timeout]` par **`after(delaiInactivite) / demarrerEviction()`**.
- **Nettoyage du pseudo-état de choix** :
  - Supprimer le libellé textuel `«choice»` au-dessus du losange et épurer la garde en `[else]` sans commentaire parasite.

### 2. Actions de Retouche SVG / PNG
1. Supprimer le déclencheur sur la transition initiale (arc muet ou `/ initialiser()`).
2. Renommer l'état en `EnRecuperationSaturation` et nettoyer la transition sortante.
3. Remplacer le timeout par `after(delaiInactivite)`.
4. Nettoyer le losange de choix en `[else]`.
5. Décoller la cartouche de garde d'erreur OOM de 10px vers le haut.

---

## 📋 Tableau de Bord Récapitulatif et Ordonnancement des Retouches

| N° | Diagramme Cible | Type UML | Statut Sémantique Audité | Statut Visuel Audité | Prêt pour Exécution |
|---|---|---|---|---|:---:|
| **01** | `01-perimetre-fonctionnel.svg` | Cas d'utilisation | ✅ Validé (Dissociation locale/Colab, Client API à gauche) | ✅ Dégagé | ⏳ En attente GO |
| **02** | `02-composants.svg` | Composants | ✅ Validé (`MediaFileStore` logique + `ILlmEngine` vers composant externe) | ✅ Élargissement 180px | ⏳ En attente GO |
| **03** | `03-deploiement.svg` | Déploiement | ✅ Validé (IDE en local, types disjoints, nœud `«externe»`) | ✅ Ligne Python déroutée | ⏳ En attente GO |
| **04** | `04-modele-de-donnees.svg` | Classes | ✅ Validé (`«enumeration» TaskStatus`, optionnels [0..1]) | ✅ Multiplicités dégagées | ⏳ En attente GO |
| **05** | `05-activite-generation.svg` | Activité | ✅ Validé (Action métier + Région interruptible) | ✅ 4 losanges nettoyés | ⏳ En attente GO |
| **06** | `06-sequence-generation.svg` | Séquence | ✅ Validé (Opérations métier, annulation explicite, `clickGenerate` corrigé) | ✅ Garde alt dégagée | ⏳ En attente GO |
| **07** | `07-sequence-brand-context.svg` | Séquence | ✅ Validé (`BrandContextCompiler` interne, `:ReactSPA`) | ✅ Fond opaque auto-appels | ⏳ En attente GO |
| **08** | `08-sequence-proxy-llm.svg` | Séquence | ✅ Validé (Rectangle acteur système, `alt` canonique) | ✅ Marges corrigées | ⏳ En attente GO |
| **09** | `09-etats-dock-adaptatif.svg` | États-transitions | ✅ Validé (`ModeImageSelectionne`, historique [H] & transitions internes maintenus) | ✅ Déroutement boîte jaune | ⏳ En attente GO |
| **10** | `10-etats-tache-media.svg` | États-transitions | ✅ Validé (Pas de FinalState, `after(120 s)`, `enregistrerFinAttente()`) | ✅ Élargissement +260px | ⏳ En attente GO |
| **11** | `11-etats-model-swapper.svg` | États-transitions | ✅ Validé (Arc initial muet, `EnRecuperationSaturation`, `after()`) | ✅ Cartouche décollée | ⏳ En attente GO |
| **Doc**| `README.md` | Architecture IEEE 1016 | ✅ Validé (Traçabilité exhaustive 11/11 & matrice d'audit) | N/A | ⏳ En attente GO |
