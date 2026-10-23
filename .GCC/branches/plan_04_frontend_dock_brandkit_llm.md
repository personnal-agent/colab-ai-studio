# Execution Plan: Plan 04/05 — Floating Prompt Dock Modulaire, Brand Kit & Mode Chat LLM

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: Le `FloatingPromptDock` implémente une modularité atomique stricte (1 fichier composant par responsabilité, 0 écran codé en dur par modèle) pilotée par le schéma `capabilities` du modèle actif (`09-etats-dock-adaptatif.svg`), garantit la règle de subsomption obligatoire du conditionnement vidéo (*Ingredient Mode* + *Frame Chaining*), gère les durées `range` et `discrete`, intègre le système complet Brand Kit (popover, Hover Card, chip atomique `[@NomDuKit]`, modale de création 3 sources et volet d'inspection à 8 sections), et bascule sans perte de contexte vers le 5ᵉ onglet `LLM` avec chat streaming SSE et bandeau d'API OpenAI.
- **Pre-requisites**: Plan 03 complété ([`.GCC/branches/plan_03_frontend_foundation_gallery.md`](plan_03_frontend_foundation_gallery.md)). Références : `UI_SPECIFICATION.md` §6–§8, `SPECIFICATION.md` §3.1–§3.2, diagramme `09-etats-dock-adaptatif.svg`. Suivant dans la chaîne : [`.GCC/branches/plan_05_colab_worker_e2e.md`](plan_05_colab_worker_e2e.md).

## 🛠️ Step-by-Step Sequence

### Step 1: Composants atomiques de paramètres et registre piloté par capacités (`ParameterRegistry`) (TDD)

- [x] **Action**: Écrire `frontend/src/__tests__/dock_capabilities.test.tsx` puis créer un fichier par contrôle atomique sous `frontend/src/components/dock/controls/` :
  - Contrôles universels passe-partout : `BatchCountPill.tsx` (`⚏ 1`–`4`), `EnhancePromptPill.tsx` (`🪄 On`/`Off`), `SeedControlPill.tsx`.
  - Contrôles conditionnels : `ModelSelectorPopover.tsx` (recherche, filtres, badges `Beta`/`New`/`! Slower than usual`), `AspectRatioPill.tsx`, `ResolutionPill.tsx`, `DurationControlPill.tsx` (rendu curseur continu si `duration.type === "range"` vs pilules discrètes si `duration.type === "discrete"`), `NativeAudioPill.tsx` (`🔊 On`/`Off`), `TalkingStylePill.tsx` (`Stable`/`Expressive`), `UpscaleScalePill.tsx` (`1.25x`–`4x`), `UpscaleQualityPill.tsx` (`Fast`/`Precise`), `UpscaleFrameRatePill.tsx`, `FineSettingsPopover.tsx` (`🎛️`).
  - Assembler le registre déclaratif `ParameterRegistry.tsx`.
- [x] **Verify**: `npm --prefix frontend test -- --run src/__tests__/dock_capabilities.test.tsx`
- **Verification Proof**:

```text
✓ src/__tests__/dock_capabilities.test.tsx (11)
Test Files  1 passed (1)
Tests  11 passed (11)
```

### Step 2: Plateau de fentes de conditionnement et règle de subsomption vidéo (TDD)

- [x] **Action**: Écrire `frontend/src/__tests__/video_subsumption.test.tsx` vérifiant que tout modèle déclarant le mode vidéo complet (`Start frame` + `End frame` + `Ingredients`) active et autorise obligatoirement toutes les combinaisons partielles et unitaires (`Ingredients` seuls jusqu'à 9 réf. incluant *Video-as-Ingredient*, `Start frame` seul, `End frame` seul, `Start + End`, `Start + Ingredients`, `End + Ingredients`), ainsi que l'avertissement visuel en cas de dépassement de `maxImageRefs`. Implémenter `ReferenceSlot.tsx` (`w-20 h-16 rounded-slot`) et `ConditioningTray.tsx` pour les pôles `Image`, `Video`, `Lip sync` et `Upscaling`.
- [x] **Verify**: `npm --prefix frontend test -- --run src/__tests__/video_subsumption.test.tsx`
- **Verification Proof**:

```text
✓ src/__tests__/video_subsumption.test.tsx (4)
Test Files  1 passed (1)
Tests  4 passed (4)
```

### Step 3: Système Brand Kit complet (Popover, Hover Card, Chip atomique, Extraction & Inspection) (TDD)

- [x] **Action**: Écrire `frontend/src/__tests__/brand_kit.test.tsx` (couvrant le popover, le chip atomique et la vérification des actifs extraits — logos, couleurs hex, polices, `overview` — après validation des parcours `Brand files` et `Website`) puis implémenter sous `frontend/src/components/brand-kit/` :
  - `BrandKitSelectorPopover.tsx` : état vide initial (*« Aucun brand kit... »* + bouton *« Create brand kit »*), liste triée par `lastUsedAt`, et `BrandKitHoverCard.tsx` (logo HD, compteur d'actifs, fraîcheur, nuancier).
  - `PromptEditorWithChip.tsx` : zone de saisie avec déclencheur `@`, insertion d'un unique chip atomique `[@NomDuKit]` (remplace le précédent) et suppression en un bloc par `Backspace`.
  - `BrandKitCreateModal.tsx` : 3 méthodes d'initialisation (`Blank`, `Brand files` drag-and-drop de PDF/images/`.fig`, `Website` saisie d'URL) raccordées au bouton `[ Continue ]` qui déclenche l'extraction d'identité (`POST /api/brand-kits` avec fichiers ou URL), récupère les actifs extraits (logos, nuancier CSS/hex, polices, résumé d'activité) et ouvre directement `BrandKitInspectorModal.tsx` pré-rempli avec ces actifs.
  - `BrandKitInspectorModal.tsx` : navigation latérale à 8 sections (`Overview`, `Logos`, `Colors`, `Fonts`, `Reference images`, `Voices`, `Captions`, `Guidelines`) inspectant les actifs extraits ou saisis, et bouton `[ Use this brand kit ]`.
- [x] **Verify**: `npm --prefix frontend test -- --run src/__tests__/brand_kit.test.tsx`
- **Verification Proof**:

```text
✓ src/__tests__/brand_kit.test.tsx (6)
Test Files  1 passed (1)
Tests  6 passed (6)
```

### Step 4: Onglet `LLM` (5ᵉ mode), vue conversationnelle streaming et assemblage du `FloatingPromptDock` (TDD)

- [x] **Action**: Écrire `frontend/src/__tests__/llm_mode.test.tsx` couvrant `09-etats-dock-adaptatif.svg` : clic sur le 5ᵉ onglet `[ LLM ]`, masquage des fentes et pilules média, filtrage du sélecteur sur les modèles de langage, maintien du bouton `@ Brand Kit`, affichage du bandeau d'intégration `http://localhost:8000/v1/chat/completions` (avec extraits copiables Cursor / Python / cURL), streaming SSE mot à mot avec bouton d'arrêt (`AbortController`), et restauration sans perte de contexte (`[H]`) lors du retour vers `Image`, `Video`, `Lip sync` ou `Upscaling`. Implémenter `LlmChatView.tsx` et assembler `FloatingPromptDock.tsx`.
- [x] **Verify**: `npm --prefix frontend test -- --run && npm --prefix frontend run build`
- **Verification Proof**:

```text
Test Files  9 passed (9)
Tests  47 passed (47)
dist/assets/index-BlVgpEGP.css   33.24 kB │ gzip:   6.38 kB
dist/assets/index-DRRPXg-l.js   337.25 kB │ gzip: 101.14 kB
✓ built in 17.08s
depcruise: no dependency violations found (58 modules, 184 dependencies cruised)
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Saut visuel (*Layout Shift*) lors de la bascule entre les 5 onglets du dock (`Image`, `Video`, `Lip sync`, `Upscaling`, `LLM`) ou lors du changement de modèle.
- **Mitigation**: Hauteurs de ligne normalisées (`h-16` pour le plateau de fentes, `h-8` pour les pilules, `w-10 h-10` pour le bouton `↑`) et transitions CSS bornées à `150ms ease-out` conformément à `DESIGN_SPECIFICATION.md` §4 et §6.
- **Risk**: Perte des paramètres saisis par l'utilisateur lorsqu'il consulte temporairement l'onglet `LLM` puis revient sur `Video`.
- **Mitigation**: Conservation de l'état courant du brouillon par mode dans le store React local (implémentation directe du pseudo-état d'historique superficiel `[H]` de `09-etats-dock-adaptatif.svg`).
