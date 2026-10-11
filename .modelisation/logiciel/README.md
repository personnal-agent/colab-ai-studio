# Modélisation UML de Colab AI Studio

> **Statut du modèle : cible spécifiée.** Ces vues décrivent le logiciel prévu dans `SPECIFICATION.md`, `UI_SPECIFICATION.md` et `ARCHITECTURE.md`. Elles ne constituent pas une preuve d’implémentation : les composants applicatifs décrits restent à créer ou à réaliser conformément aux jalons du projet.

## 1. Objet et périmètre

Ce dossier fournit une vue globale et complémentaire du système multimédia hybride :

- **Frontend local** : SPA React/Vite et dock flottant dont les contrôles dépendent des capacités du modèle choisi;
- **Backend local** : API FastAPI asynchrone, orchestration des tâches, flux SSE, proxy LLM, compilation du contexte de marque, rapatriement des médias et persistance documentaire;
- **Worker distant** : API FastAPI sur Google Colab, pipelines d’inférence et `ModelSwapper` pour la résidence des modèles sur le GPU;
- **liaisons et données** : tunnel public chiffré, documents JSON locaux, actifs importés, médias produits et destinations de projet.

Le mode d’inférence local est représenté uniquement comme option configurée et refusée tant que son runner n’est pas réalisé : les routes concernées répondent `501 Not Implemented`. Le diagramme ne le présente pas comme un moteur fonctionnel.

Les noms de composants, contrats et flux sont des éléments du **modèle cible spécifié**, et non des modules logiciels déjà présents. Les attributs de la vue de classes résument les exemples de schémas documentaires; ils ne remplacent pas des modèles Pydantic exhaustifs.

## 2. Principes de lecture

- Les notations suivent les notions UML 2.5.1 pertinentes : acteurs et cas d’utilisation, composants, nœuds et environnements d’exécution, classes et associations, partitions d’activité, lignes de vie et fragments de séquence, états et transitions.
- Les vues répondent à des questions distinctes. Un flux d’activité expose les choix et branches d’un parcours; une séquence ordonne les échanges entre participants; une machine à états décrit le cycle de vie d’un objet.
- Les rôles internes et externes sont distingués. Le worker Colab appartient au système cible; un client tiers de l’API LLM et le fournisseur LLM de compilation sont externes.
- Une relation notée `«extend»` est conditionnelle. Les associations de classes portent des multiplicités; une composition n’est employée que pour les objets possédés par le document parent.
- Les cadres `opt`, `alt`, `loop` et `ref` des séquences expriment respectivement un comportement optionnel, une alternative, une répétition et le renvoi à une interaction définie séparément.
- Tous les états des automates (actifs comme terminaux nominaux, d’annulation ou d’échec) sont formellement spécifiés et représentés par des rectangles à coins arrondis en trait plein continu conformément à OMG UML 2.5.1 §14.2.3. Les différenciations chromatiques (vert pour le succès, ambre pour l’annulation, rouge pour l’échec) facilitent le repérage visuel sans déroger à la syntaxe graphique normée.

## 3. Diagrammes retenus

Le corpus retient **7 types UML et 11 diagrammes**. Chaque fichier SVG est éditable; le PNG homonyme est son rendu lisible sans outil d’édition vectorielle.

| # | Vue / question à laquelle elle répond | Fichiers |
|---|---|---|
| 1 | **Cas d’utilisation — périmètre fonctionnel** : quels objectifs le créateur poursuit-il et quels services ou acteurs externes interviennent? | [SVG](diagrammes/01-perimetre-fonctionnel.svg) · [PNG](diagrammes/01-perimetre-fonctionnel.png) |
| 2 | **Composants — architecture logique** : quelles responsabilités et interfaces séparent SPA, API locale, compilateur, proxy, persistance et worker? | [SVG](diagrammes/02-composants.svg) · [PNG](diagrammes/02-composants.png) |
| 3 | **Déploiement — implantation** : sur quels nœuds et environnements se trouvent l’application, les documents, le relais et l’inférence? | [SVG](diagrammes/03-deploiement.svg) · [PNG](diagrammes/03-deploiement.png) |
| 4 | **Classes — données métier** : quelles informations sont enregistrées pour une génération, un projet, un Brand Kit et la configuration? | [SVG](diagrammes/04-modele-de-donnees.svg) · [PNG](diagrammes/04-modele-de-donnees.png) |
| 5 | **Activité — génération média** : quelles décisions et étapes mènent de la saisie à la galerie, y compris le mode local réservé et l’annulation? | [SVG](diagrammes/05-activite-generation.svg) · [PNG](diagrammes/05-activite-generation.png) |
| 6 | **Séquence — génération asynchrone** : comment la requête, l’identifiant de tâche, le suivi SSE, l’annulation et le rapatriement s’enchaînent-ils? | [SVG](diagrammes/06-sequence-generation.svg) · [PNG](diagrammes/06-sequence-generation.png) |
| 7 | **Séquence — compilation du contexte de marque** : comment sont appliqués le repli LLM, les capacités du modèle et l’ordre de priorité des références? | [SVG](diagrammes/07-sequence-brand-context.svg) · [PNG](diagrammes/07-sequence-brand-context.png) |
| 8 | **Séquence — proxy LLM** : comment un client OpenAI-compatible échange-t-il avec le moteur distant et retransmet-il les tokens? | [SVG](diagrammes/08-sequence-proxy-llm.svg) · [PNG](diagrammes/08-sequence-proxy-llm.png) |
| 9 | **États-transitions — dock adaptatif** : comment le mode média ou Chat sélectionné détermine-t-il l’ensemble de contrôles affiché? | [SVG](diagrammes/09-etats-dock-adaptatif.svg) · [PNG](diagrammes/09-etats-dock-adaptatif.png) |
| 10 | **États-transitions — tâche média** : quels sont les états actif et terminaux d’une génération, et quelles incertitudes subsistent? | [SVG](diagrammes/10-etats-tache-media.svg) · [PNG](diagrammes/10-etats-tache-media.png) |
| 11 | **États-transitions — Model Swapper** : comment le worker charge-t-il, réutilise-t-il ou évince-t-il un modèle résident? | [SVG](diagrammes/11-etats-model-swapper.svg) · [PNG](diagrammes/11-etats-model-swapper.png) |

### Justification des vues exclues

- **Communication** : elle reprendrait les participants et les échanges déjà explicités par les trois séquences; elle n’ajouterait pas de question distincte à cette documentation.
- **Paquetages** : l'organisation modulaire logique et le découpage fonctionnel en sous-systèmes autonomes sont déjà intégralement formalisés au niveau 1 par le diagramme de composants composite (`02-composants.svg`). Ce dernier explicite les sous-systèmes («subsystem»), ports de frontière, interfaces fournies/requises (notation ball-and-socket) et connecteurs d'assemblage, rendant une vue de paquetages dédiée redondante sans gain sémantique pour la cible spécifiée.
- **Diagramme d’objets** : un instantané d’instances serait redondant avec les schémas JSON illustrés et la vue de classes.
- **Diagrammes de composants ou de séquence supplémentaires** : le détail est limité aux frontières et scénarios pour lesquels les spécifications donnent un contrat distinct.

## 4. Matrice de traçabilité formelle (IEEE 1016 & L3 MIAGE)

Conformément aux normes IEEE 1016 et aux exigences académiques L3 MIAGE, la matrice ci-dessous établit la traçabilité bidirectionnelle complète entre les **8 Cas d'Utilisation** du périmètre fonctionnel (`01-perimetre-fonctionnel.svg`), les **exigences système amont**, les **composants logiques et classes structurelles participantes**, et les **réalisations dynamiques** (diagrammes d'activité, de séquence et de machine à états).

| ID UC | Cas d'utilisation | Exigences système sources | Composants participants (`02-composants.svg`) | Classes / Entités participantes (`04-modele-de-donnees.svg`) | Réalisations dynamiques associées |
|---|---|---|---|---|---|
| **UC-01** | **Produire un média** *(image, vidéo, lip sync, upscale)* | `SPECIFICATION.md` §3.1, §4.3, §4.4, §5.1<br>`ARCHITECTURE.md` §3.1, §3.3, §4<br>`UI_SPECIFICATION.md` §6.1–§6.5 | `React SPA` (Dock adaptatif)<br>`API Locale`<br>`Compilateur Brand`<br>`Orchestrateur Tâches`<br>`Tunnel HTTP/SSE`<br>`Worker Colab` / `ModelSwapper` | `Generation`<br>`GenerationParameters`<br>`GenerationReferences`<br>`BrandKitSnapshot`<br>`Project`<br>`StudioConfig` | • `05-activite-generation.svg`<br>• `06-sequence-generation.svg`<br>• `07-sequence-brand-context.svg`<br>• `09-etats-dock-adaptatif.svg`<br>• `10-etats-tache-media.svg`<br>• `11-etats-model-swapper.svg` |
| **UC-02** | **Interagir avec l'assistant textuel IA** *(génération de texte et assistance)* | `SPECIFICATION.md` §3.2, §4.3<br>`ARCHITECTURE.md` §3.2<br>`UI_SPECIFICATION.md` §6.1 | `Vue Conversationnelle`<br>`Proxy LLM Local`<br>`Fournisseur LLM` (externe)<br>`Worker Colab` (optionnel) | `StudioConfig`<br>`CompilerLlmConfig`<br>`LlmProxyConfig` | • `08-sequence-proxy-llm.svg`<br>• `09-etats-dock-adaptatif.svg` |
| **UC-03** | **Suivre une génération** *(progression temps réel)* | `SPECIFICATION.md` §4.1, §4.3<br>`ARCHITECTURE.md` §3.1<br>`UI_SPECIFICATION.md` §6.5 | `Galerie & Suivi`<br>`API Locale`<br>`Orchestrateur Tâches`<br>`Tunnel HTTP/SSE`<br>`Worker Colab` | `Generation`<br>`StudioConfig` | • `05-activite-generation.svg`<br>• `06-sequence-generation.svg`<br>• `10-etats-tache-media.svg` |
| **UC-04** | **Annuler une génération** *(tâche en cours)* | `SPECIFICATION.md` §4.1, §4.3<br>`ARCHITECTURE.md` §3.1<br>`UI_SPECIFICATION.md` §6.5 | `Galerie & Suivi`<br>`API Locale`<br>`Orchestrateur Tâches`<br>`Tunnel HTTP/SSE`<br>`Worker Colab` | `Generation`<br>`StudioConfig` | • `05-activite-generation.svg`<br>• `06-sequence-generation.svg`<br>• `10-etats-tache-media.svg` |
| **UC-05** | **Parcourir et remixer** *(favoris, filtres, export)* | `SPECIFICATION.md` §4.2.1, §4.3<br>`UI_SPECIFICATION.md` §4, §5.1, §5.2 | `Galerie & Suivi`<br>`React SPA`<br>`API Locale`<br>`Gestionnaire Persistance JSON` | `Generation`<br>`GenerationParameters`<br>`GenerationReferences`<br>`BrandKitSnapshot`<br>`Project` | • `05-activite-generation.svg`<br>• `09-etats-dock-adaptatif.svg` |
| **UC-06** | **Gérer les Brand Kits** *(actifs, directives, identité)* | `SPECIFICATION.md` §4.2.2, §4.3, §4.4<br>`UI_SPECIFICATION.md` §7.1, §7.2 | `React SPA`<br>`API Locale`<br>`Compilateur Brand`<br>`Gestionnaire Persistance JSON` | `BrandKit`<br>`BrandKitSnapshot`<br>`Logo`<br>`Color`<br>`Font`<br>`Asset`<br>`Guideline` | • `07-sequence-brand-context.svg`<br>• `09-etats-dock-adaptatif.svg` |
| **UC-07** | **Organiser les projets** *(destination de stockage)* | `SPECIFICATION.md` §4.2.3, §4.3<br>`ARCHITECTURE.md` §2<br>`UI_SPECIFICATION.md` §3.2 | `React SPA`<br>`API Locale`<br>`Gestionnaire Persistance JSON` | `Project`<br>`Generation`<br>`BrandKit` | • `05-activite-generation.svg` |
| **UC-08** | **Connecter l'environnement de calcul distant** *(liaison réseau & diagnostic worker)* | `SPECIFICATION.md` §4.3, §5.1<br>`ARCHITECTURE.md` §1, §4<br>`UI_SPECIFICATION.md` §3.1 | `React SPA`<br>`API Locale`<br>`Tunnel HTTP/SSE`<br>`Worker Colab` | `StudioConfig`<br>`ColabConfig`<br>`LocalConfig` | • `06-sequence-generation.svg`<br>• `11-etats-model-swapper.svg` |

## 5. Synthèse du modèle

### 5.1 Responsabilités

1. Le **Frontend** configure une génération selon le type de média et les `capabilities` du modèle, insère éventuellement un chip de Brand Kit, présente le suivi et les résultats, et émet les appels locaux.
2. L’**API locale FastAPI** valide les requêtes, expose les routes REST, orchestre les tâches distantes, publie leur progression en SSE, offre le proxy `/v1/chat/completions`, rappelle le contexte de marque, récupère les fichiers et met à jour les documents JSON.
3. Le **worker Colab** charge les poids nécessaires, évince le modèle résident lorsqu’un autre est requis, exécute le pipeline et publie l’avancement et le résultat.
4. Le **système de fichiers local** contient les documents de `data/`, les médias importés sous `data/assets/` et les résultats générés sous leur destination résolue.

### 5.2 Parcours principal

Le créateur prépare prompt, modèle, paramètres et références dans le dock puis déclenche `POST /api/generate/media`. Si un Brand Kit est sélectionné, le `BrandContextCompiler` lit ses données, demande si possible la synthèse au LLM configuré et applique un gabarit anglais déterministe lorsque le fournisseur est indisponible, invalide ou en erreur. Les références utilisateur priment sur celles du kit, puis sur le logo; si le modèle n’accepte aucune image de référence, seul le brief textuel est transmis.

En mode Colab, le backend relaie la demande par le tunnel au worker. Le client reçoit un identifiant de tâche et consulte `GET /api/tasks/{task_id}/status` en SSE. `POST /api/tasks/{task_id}/cancel` permet de demander l’annulation d’une tâche en cours. À l’achèvement, le média est rapatrié et les métadonnées sont conservées dans `data/generations.json`.

En mode local, aucun pipeline de génération n’est modélisé : les routes d’inférence répondent `501 Not Implemented` tant que le runner local reste réservé.

### 5.3 Données et persistance

Les collections documentaires visées sont `data/generations.json`, `data/brand_kits.json`, `data/projects.json` et `data/config.json`. La configuration mémorise notamment le mode d’exécution, la liaison Colab, les options du compilateur LLM et du proxy ainsi que les préférences de stockage. Le diagramme de classes montre les champs métier saillants et leurs associations, pas toutes les propriétés des exemples.

Les écritures JSON doivent être sérialisées par `asyncio.Lock`, écrites dans un fichier temporaire, puis publiées par renommage atomique POSIX `os.replace`. Pour les médias : un `storagePath` explicitement défini sur un projet est la destination exclusive; sinon un projet utilise `outputs/projects/<id>/`; sans projet, la destination est `outputs/YYYY-MM-DD/`.

Un `Generation` conserve son contexte de création, notamment `parameters`, `references` et un `brandKitSnapshot`, pour soutenir le remix et préserver l’identité de marque utilisée. Le snapshot est une copie de contexte et non une association de cycle de vie au Brand Kit courant. `projectId` et `brandKitId` sont des références par identifiant; la politique de suppression ou de réparation d’une référence devenue orpheline n’est pas définie.

### 5.4 Dock et capacités

Les modes média sont **Image**, **Vidéo**, **Lip sync** et **Upscaling**. Les paramètres universels restent communs; les contrôles spécifiques sont montés selon les capacités du modèle actif. Le mode vidéo combine le conditionnement par ingrédients (`Ingredient Mode`, dont *Video-as-Ingredient*) et l’interpolation par images de début/fin (`Frame Chaining`); la subsomption du mode complet sur les variantes partielles est exigée par la spécification. La durée prend la forme d’un intervalle continu (`range`) ou de valeurs permises discrètes (`discrete`). En mode Chat LLM, les contrôles média sont masqués.

### 5.5 Interfaces locales citées

Les séquences s’appuient sur les contrats documentés suivants :

- `POST /api/generate/media` — lancer une génération asynchrone;
- `GET /api/tasks/{task_id}/status` — progression par SSE;
- `POST /api/tasks/{task_id}/cancel` — demander une annulation idempotente;
- `GET /api/health`, `GET /api/models`, `POST /api/models/switch` — diagnostic et sélection/chargement des modèles;
- `GET /api/generations`, `PATCH /api/generations/{id}/favorite`, `DELETE /api/generations/{id}` — gérer la galerie;
- `GET|POST /api/brand-kits`, `GET|POST /api/projects`, `POST /api/config/colab-url` — gérer les données et la liaison;
- `POST /v1/chat/completions` — proxy compatible OpenAI.

Les endpoints ci-dessus sont des interfaces spécifiées, pas une assertion qu’ils sont déjà tous implémentés.

## 6. Hypothèses et points à confirmer

Les diagrammes ne complètent pas silencieusement les contrats absents. Les points suivants doivent être confirmés avant d’être considérés comme des comportements garantis :

1. **Progression du worker** : la progression est consultable par l’orchestrateur local, mais le protocole inter-nœuds (callback, polling ou autre), le format d’événement et les erreurs de transport ne sont pas arrêtés.
2. **Identité de tâche** : le worker et l’API locale exposent un `task_id`; le mapping, la propriété et la stratégie de reprise de cet identifiant ne sont pas formalisés.
3. **États d’échec** : les statuts terminaux et le traitement des erreurs worker, de téléchargement et de persistance ne sont pas entièrement énumérés. L’état `Échec` du diagramme 10 est donc à valider.
4. **Course annulation / achèvement** : la réponse quand l’annulation et le résultat se produisent simultanément n’est pas spécifiée; le diagramme n’impose pas de priorité.
5. **Model Swapper** : les effets de requêtes concurrentes, la file d’attente, les erreurs de chargement et la politique de conservation d’un modèle ne sont pas décrits.
6. **Dock** : le mode initial lorsqu’aucun modèle n’est sélectionné n’est pas fixé.
7. **Proxy distant** : le contrat OpenAI-compatible local et la retransmission en streaming sont spécifiés, mais l’endpoint distant et le contrat exact d’annulation amont ne sont pas détaillés.
8. **Configuration LLM** : les exemples documentaires donnent le nom `apiKeyEnv` et aussi un champ `apiKey: null`; le modèle métier ne représente aucun secret en clair. La politique finale de persistance et de résolution du secret reste à confirmer.

## 7. Références

### Spécifications du dépôt

- [`ARCHITECTURE.md`](../../ARCHITECTURE.md) :
  - Section 1 : Vue d'ensemble du système & contraintes d'empreinte mémoire locale;
  - Section 2 : Cartographie des répertoires et organisation des flux;
  - Section 3 : Flux de données & responsabilités (3.1 Cycle de génération multimédia, 3.2 Passerelle LLM locale `/v1/chat/completions`, 3.3 Modularité atomique UI & registre de paramètres);
  - Section 4 : Contraintes matérielles & garde-fous d'exécution (Model Swapper GPU T4 16 Go VRAM).
- [`SPECIFICATION.md`](../../SPECIFICATION.md) :
  - Section 2 : Architecture globale et principes directeurs;
  - Section 3 : Spécifications UI/UX (3.1 Mode Studio Vidéo & Image, 3.2 Mode Chat LLM & passerelle API);
  - Section 4 : Spécifications du backend local FastAPI (4.1 Responsabilités, 4.2 Architecture de stockage local & base de données documentaire JSON `generations.json`, `brand_kits.json`, `projects.json`, `config.json`, 4.3 Endpoints locaux REST/SSE, 4.4 Compilateur de contexte de marque);
  - Section 5 : Spécifications du worker distant Google Colab (5.1 Gestion dynamique de la VRAM et cycle de vie Model Swapper).
- [`UI_SPECIFICATION.md`](../../UI_SPECIFICATION.md) :
  - Section 1 : Vision & architecture ergonomique globale (1.1 Principes ergonomiques directeurs);
  - Section 2 : Disposition spatiale de l'écran (Layout global);
  - Section 3 : Barre supérieure & contrôles globaux (3.1 Statut worker Colab, 3.2 Sélecteur de projet & configuration);
  - Section 4 : Recherche globale & filtres de flux;
  - Section 5 : Grille de la galerie & types de cartes média (5.1 Favoris et persistance, 5.2 Lecteur grand format & remix);
  - Section 6 : Station de commande flottante / Floating Prompt Dock (6.1 Onglets de modes média, 6.2 Conditionnement vidéo Ingredient Mode & Frame Chaining avec règle de subsomption, 6.3 Zone de saisie, 6.4 Pilules de contrôle selon capacités et gestion de durée range/discrete, 6.5 Action et suivi de tâche);
  - Section 7 : Système Brand Kit (7.1 Point d'entrée dock & sélecteur rapide, 7.2 Modale de gestion des Brand Kits).

### Références UML

- *Initiation au langage UML*, cours L3 MIAGE fourni par le demandeur : supports et présentations étudiés pour les conventions pédagogiques des diagrammes retenus.
- Object Management Group, *OMG Unified Modeling Language (OMG UML), Version 2.5.1* : vocabulaire et sémantique UML utilisés en complément des supports pédagogiques.

## 8. Fichiers

Tous les couples SVG/PNG sont dans [`diagrammes/`](diagrammes/). Les SVG constituent les sources éditables; les PNG sont des rendus dérivés et sont conservés en versionnement pour consultation rapide. Les images ont été générées localement sans ajouter de dépendance logicielle au projet.
