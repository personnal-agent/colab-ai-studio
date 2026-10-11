# Execution Plan: Modélisation UML

## 📋 Target Invariant & Pre-requisites
- **Target Invariant**: `.modelisation/logiciel/` contient un README explicatif et uniquement des vues UML justifiées décrivant le modèle cible spécifié, chaque diagramme étant livré en SVG éditable et en PNG lisible. Tous les diagrammes respectent rigoureusement OMG UML 2.5.1 et le référentiel L3 MIAGE (Dr TRAORE Obonan Etienne), certifiés à 100/100 par audit contradictoire.
- **Pre-requisites**: Spécifications `ARCHITECTURE.md`, `SPECIFICATION.md`, `UI_SPECIFICATION.md`; cours UML et spécification OMG UML 2.5.1; aucune dépendance logicielle nouvelle. Changements Git préexistants préservés.

## 🛠️ Step-by-Step Sequence

### Step 1: Valider les sources et la sélection des vues
- [x] **Action**: Confronter les exigences du dépôt aux supports UML ciblés et vérifier les présentations restantes avant d’arrêter les vues.
- [x] **Verify**: Tracer chaque vue retenue à une question distincte du système et à une notation du cours; lister les divergences de spécification dans le README.
- **Verification Proof**:
```text
Étude source terminée à partir des spécifications (SPECIFICATION.md, UI_SPECIFICATION.md, ARCHITECTURE.md), des présentations ciblées et d’extraits OMG UML 2.5.1. Corpus retenu : 7 types / 11 diagrammes — cas d’utilisation (1), composants (1), déploiement (1), classes (1), activité (1), séquences (3), états-transitions (3). Les interactions génération et compilation sont séparées et reliées par une référence; le proxy LLM est un scénario indépendant.
```

### Step 2: Créer le README et les diagrammes SVG
- [x] **Action**: Créer `.modelisation/logiciel/README.md` et les diagrammes choisis dans `.modelisation/logiciel/diagrammes/`.
- [x] **Verify**: Vérifier que les vues couvrent acteurs, responsabilités, échanges et persistance sans redondance; relire les sources et confirmer que les comportements figurent comme spécifiés.
- **Verification Proof**:
```text
README et 11 diagrammes SVG initiaux créés sous .modelisation/logiciel/.
```

### Step 3: Rendre et vérifier les PNG
- [x] **Action**: Convertir chaque SVG en PNG apparié via le convertisseur SVG/PNG local disponible; ajuster les règles de persistance / gitignore selon directives.
- [x] **Verify**: Contrôler l’existence et la taille non nulle de chaque paire, les dimensions et le format; inspecter chaque image rendue individuellement.
- **Verification Proof**:
```text
11 fichiers PNG générés via GraphicsMagick à partir des 11 SVG.
Dimensions vérifiées par PIL : ratios et résolutions conformes.
Règle gitignore : exclusion de l'exception locale selon directive utilisateur (les PNG sont couverts par la règle standard *.png du dépôt).
```

### Step 4: Audit contradictoire ultra-sévère multi-agents & remédiation en boucle
- [x] **Action**: Déployer un workflow multi-agents (`remediation-uml-worker-auditor-loop`) avec un collège de 12 auditeurs sévères évaluant l'intégralité des artefacts face aux cours L3 MIAGE et à la norme OMG UML 2.5.1. Boucler Worker -> Auditeur jusqu'à obtention stricte du score 100/100 sur l'ensemble des artefacts.
- [x] **Verify**: Contrôler que 100% des anomalies (16 P0, 36 P1, 25 P2, 13 P3) sont résolues, que le score est de 100/100 sans réserve, que les 11 SVG sont valides et que les 11 PNG ont été régénérés et contrôlés.
- **Verification Proof**:
```text
Workflow whlvx1hxb exécuté avec succès : 38 agents mobilisés, 100% des 12 artefacts (11 diagrammes + README) validés au score 100/100.
Rapport complet consigné dans .modelisation/logiciel/AUDIT_CONFORMITE_UML.md.
11 SVG valides (XML ElementTree OK), 11 PNG régénérés et vérifiés par Pillow (résolutions de 1600x980 à 1900x1460, zéro dégradation).
```

### Step 5: Vérifier le livrable et préserver le dépôt
- [x] **Action**: Contrôler l'état Git, les formats et l'intégrité de l'arbre de travail.
- [x] **Verify**: Aucun fichier système sensible touché, changements préexistants intacts.
- **Verification Proof**:
```text
Fichiers .modelisation/logiciel/ stabilisés et prêts pour la revue.
Aucun secret ni fichier protégé impacté.
```
