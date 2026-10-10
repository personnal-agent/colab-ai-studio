# Gouvernance du Dépôt GitHub — Colab AI Studio

Ce document régit les règles d'automatisation, le cycle de vie des signalements (*issues*), les règles des propositions de modifications (*pull requests*), les publications (*releases*) et la gestion des dépendances sur GitHub pour **Colab AI Studio**. Il constitue la référence lisible par les humains et les agents IA de la configuration active dans `.github/`.

---

## 1. Workflows d'Automatisation GitHub Actions

| Workflow | Fichier | Déclencheur | Rôle & Pipeline |
|---|---|---|---|
| **Intégration Continue (CI)** | `.github/workflows/ci.yml` | `pull_request`, `push` sur `main`, `workflow_dispatch` | Vérification des 3 volets : qualité backend Python (syntaxe, ruff, tests pytest), qualité frontend Node.js (lint, tests, build) et intégrité des workflows GitHub. |
| **Gouvernance des PR** | `.github/workflows/governance.yml` | Événements `pull_request` | Contrôle du format Conventional Commits du titre et des commits, respect du budget de taille (alerte > 500 lignes, rejet strict > 1000 lignes) et publication du commentaire d'audit. |
| **Revue des Dépendances** | `.github/workflows/security.yml` | `pull_request` | Revue des dépendances ajoutées ou modifiées sur PR (gravité élevée, filtrage des licences AGPL/GPL). |
| **Hygiène des Workflows** | `.github/workflows/workflow-hygiene.yml` | `pull_request`, `push` sur `main`, hebdo | Vérifie le verrouillage par hash SHA complet (40 caractères) de toutes les actions tierces et le principe de moindre privilège des jetons. |
| **Triage des Issues** | `.github/workflows/issue-triage.yml` | `issues` (opened, reopened, edited), `workflow_dispatch` | Qualification et étiquetage initial des signalements selon les formulaires d'issues. |
| **Détection d'Anomalies** | `.github/workflows/issue-detection.yml` | Planifié / manuel | Analyse de santé du dépôt et signalement d'incohérences structurelles. |
| **Publication de Version** | `.github/workflows/release.yml` | `push` sur `main`, `workflow_dispatch` | Release sémantique automatique, génération du journal des modifications (*changelog*) et publication GitHub. |

---

## 2. Cycle de Vie des Signalements (Issues)

### Formats Recommandés
Quatre formulaires stricts sont configurés dans `.github/ISSUE_TEMPLATE/` :
- `bug.md` : Signalement d'anomalie avec contexte technique précis, comportement observé vs attendu et étapes de reproduction.
- `feature.md` : Proposition d'amélioration ou nouvelle fonctionnalité avec cas d'usage et bénéfice utilisateur.
- `documentation.md` : Amélioration, clarification ou correction des spécifications et guides du studio.
- `config.yml` : Configuration des gabarits et désactivation des signalements vides sans structure.

### Signalements Générés par les Agents
Les agents IA ne créent pas d'issues de façon autonome sans validation préalable du mainteneur, à l'exception des rapports de défauts forensiques formellement vérifiés et documentés avec preuves d'exécution. Les alertes de sécurité sont systématiquement orientées vers la procédure privée décrite dans [`SECURITY.md`](../SECURITY.md).

---

## 3. Règles des Pull Requests

- **Mode de livraison** : Toute modification substantielle transite par une branche dédiée et une Pull Request — voir `AGENTS.md` §4 (mode Strict Review).
- **Titres et commits** : Respect impératif de la norme **Conventional Commits** (`type(scope): description`). Types autorisés : `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `build`, `style`, `revert`.
- **Budget de taille** : ≤ 500 lignes recommandées pour faciliter la relecture, rejet automatique au-delà de 1000 lignes.
- **Gabarit obligatoire** : `.github/PULL_REQUEST_TEMPLATE.md` doit être intégralement complété (cause racine, description synthétique, commandes de test exécutées, risques résiduels).
- **Revues de code & Approbation** :
  - **L'agent IA n'approuve JAMAIS son propre code.**
  - 100 % des retours des bots d'audit et des revues humaines doivent être lus et résolus avant fusion.
  - La décision de fusion (*merge*) appartient exclusivement aux mainteneurs humains.
- **Chemins sanctuarisés (protection stricte)** :
  Aucun agent ne peut modifier sans validation humaine explicite : `AGENTS.md`, `.gouvernance/**`, `.github/workflows/**`, `.github/scripts/**`, `.githooks/**`, `.GCC/PROTOCOL.md`.

---

## 4. Gestion des Dépendances

- Configuration automatisée via `.github/dependabot.yml` avec vérification hebdomadaire des écosystèmes GitHub Actions, Python (pip) et JavaScript (npm).
- Mises à jour regroupées et vérifiées systématiquement par la suite de validation CI avant intégration.

---

## 5. Documents de Référence Associés

| Thème | Fichier |
|---|---|
| Matrice de droits de l'agent en session interactive | [`accompanied-agent.md`](./accompanied-agent.md) |
| Protocole pour runner d'exécution isolé | [`autonomous-agent.md`](./autonomous-agent.md) |
| Politique de revue de code assistée par IA | [`review-policy.md`](./review-policy.md) |
| Procédure de signalement de vulnérabilités | [`../SECURITY.md`](../SECURITY.md) |
| Modèle de Pull Request | [`../.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) |
| Modèles d'Issues | [`../.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) |
