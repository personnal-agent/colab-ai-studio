# Politique de Sécurité — Colab AI Studio

## Versions Prises en Charge

Seule la version active sur la branche principale (`main`) reçoit des correctifs de sécurité.

| Version | Prise en charge |
| ------- | --------------- |
| main    | :white_check_mark: |
| < 1.0   | :x:             |

## Signalement d'une Vulnérabilité

**Ne signalez JAMAIS de vulnérabilité de sécurité via une issue publique ou une discussion ouverte.**

Nous prenons la sécurité de Colab AI Studio très au sérieux. Si vous découvrez une faille de sécurité ou une vulnérabilité potentielle :

### 1. Procédure de Divulgation Privée

Utilisez en priorité la fonctionnalité **GitHub Private Vulnerability Reporting** :
1. Rendez-vous sur l'onglet **Security** du dépôt GitHub.
2. Cliquez sur **Advisories**, puis sur **Report a vulnerability**.
3. Décrivez précisément le problème selon le modèle fourni.

Cette procédure garantit que les informations restent strictement confidentielles entre vous et les mainteneurs du projet jusqu'à la publication d'un correctif.

### 2. Informations à Fournir

Pour accélérer la qualification et la correction, incluez dans votre rapport :
- Une description claire de la vulnérabilité et de son impact potentiel.
- Les étapes détaillées ou un script de preuve de concept (PoC) permettant de reproduire l'anomalie.
- Les composants ou fichiers affectés (backend FastAPI, worker Colab, frontend SPA, workflows).
- Toute suggestion de remédiation ou correctif envisagé.

### 3. Délais de Traitement

- **Accusé de réception** : Sous 48 heures ouvrées.
- **Évaluation et confirmation** : Sous 5 jours ouvrés.
- **Mise à disposition du correctif** : En fonction de la gravité (critique, élevée, moyenne), un correctif sera développé sur une branche privée et publié avec une nouvelle version.
- **Divulgation publique** : Coordonnée d'un commun accord une fois le correctif déployé.
