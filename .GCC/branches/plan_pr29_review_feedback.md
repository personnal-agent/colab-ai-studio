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
- [ ] **Action**: Livraison Git après autorisation ; aucun commit, push ou résolution de thread distant effectué. Le sandbox autorise uniquement le push de `coderabbit/address-pr-review-feedback/701424ac`, pas celui de `docs/modelisation-v3`.

## ⚠️ Mitigations & Edge Cases
- **Risk**: Confondre les cibles d’architecture avec les fonctions disponibles ou élargir une PR documentaire en implémentation multimoteur.
- **Mitigation**: États « actuel » / « cible » explicites et tests des exemples sur les schémas préexistants ; aucune modification du runtime.
- **Risk**: Fausse atomicité fichiers/SQLite, divergence de catalogue, mauvaise URL après repli ou budget RAM incomplet.
- **Mitigation**: Publication avec reprise et compensation, catalogue éditable unique, runtimeEndpoints partagé et deux scénarios mémoire ; garanties restant à implémenter et mesurer.
