# Execution Plan: Corrections documentaires de la PR #29

## 📋 Target Invariant & Pre-requisites
- **Target Invariant**: Distinguer le contrat actuel du worker des exigences futures Omniforge sans modifier le runtime. Préserver persistance atomique JSON, stockage exclusif par projet et objectif de transfert borné.
- **Pre-requisites**: PR head `6d0b949f635a9b4c8a6d132393603d173e24d46a`, 10 remarques majeures et 14 mineures lues. Base précédente `522377906ab86859585dc689ec2be2918c3f5ea2` ; aucune modification du runtime dans la PR.

## 🛠️ Step-by-Step Sequence

### Step 1: Corriger les contrats et exemples documentaires
- [x] **Action**: Corriger SPECIFICATION01.md, ARCHITECTURE01.md, UI_SPECIFICATION01.md, DESIGN_SPECIFICATION01.md, INTEGRATION_PLAN_V3.md et les deux README numérotés.
- [x] **Action**: Synchroniser les libellés des quatre SVG concernés (ports, états, mémoire).
- [x] **Verify**: Validation JSON/XML/liens et conformité de l’exemple de requête/configuration aux schémas actuels.
- **Verification Proof** (première exécution historique ; la dernière en vérifie six) :
```text
Documentation checks passed: 5 JSON blocks, current request/config schemas, 14 UML types, SVG XML, local links, statuses, ports and tokens.
```

### Step 2: Validation et revue indépendante
- [x] **Verify**: Ruff/compilation, 99 tests backend, 74 tests frontend, build et hook pre-push complet.
- [x] **Verify**: Cinq passes CodeRabbit terminées : 9, 4, 6, 5 puis 3 remarques (doublons inclus), toutes traitées. Dernière passe : trois mineures, vérifiées par assertions ciblées ; aucune nouvelle passe CLI à zéro finding revendiquée.
- **Verification Proof**: Sorties brutes dans `.GCC/branches/test.md` ; registre reproductible externe dans `workspace-context/validation-record.md`.

### Step 3: Corrections des instructions protégées et livraison
- [x] **Action**: Accord explicite obtenu et patch appliqué à AGENTS.md et CLAUDE.md (trois remarques mineures).
- [x] **Action**: Premier lot publié au commit `e985ef5f5db3375b71761c67f1be4c966d3fb612` sur `docs/modelisation-v3`, conformément à l’autorisation explicite de mise à jour de la PR #29 ; dernière revue locale du lot : zéro finding.

### Step 4: Nouvelle revue distante après publication
- [x] **Action**: Lire intégralement la revue du 2026-10-27 17:26 UTC, cinq retours directs, un nitpick et un complément ; consulter les deux anciens fils encore ouverts.
- [x] **Action**: Clarifier Auth séparé, readiness Local Service, coordination FastAPI/NestJS et publication no-replace ; documenter prérequis Colab et dépendances externes du handoff.
- [x] **Verify**: Validations documentaires et revue indépendante en lecture seule passées ; sorties et correctifs dans test.md.
- [x] **Verify**: Revue CodeRabbit du diff : 3 remarques corrigées puis 9 mineures (1 corrigée, 8 espaces non reproduits) ; événements terminaux et preuves dans test.md et registre externe.
- [ ] **Action**: Publier le nouveau lot et vérifier les fils distants sans déclarer de garantie runtime non implémentée.

## ⚠️ Mitigations & Edge Cases
- **Risk**: Confondre les cibles d’architecture avec les fonctions disponibles ou élargir une PR documentaire en implémentation multimoteur.
- **Mitigation**: États « actuel » / « cible » explicites et tests des exemples sur les schémas préexistants ; aucune modification du runtime.
- **Risk**: Fausse atomicité fichiers/SQLite, divergence de catalogue, mauvaise URL après repli ou budget RAM incomplet.
- **Mitigation**: Publication avec reprise et compensation, catalogue éditable unique, runtimeEndpoints partagé et deux scénarios mémoire ; garanties restant à implémenter et mesurer.
