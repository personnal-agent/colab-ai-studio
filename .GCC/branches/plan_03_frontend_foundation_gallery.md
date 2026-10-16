# Execution Plan: Plan 03/05 — Socle Frontend React SPA, Design System, Galerie & Projets

## 📋 Target Invariant & Pre-requisites

- **Target Invariant**: L'application frontend React 18 / Vite 5 / TypeScript 5 compile sans erreur, applique strictement les tokens de `DESIGN_SPECIFICATION.md` (contraste WCAG AA `#4B5563`, ombres et rayons `rounded-dock`, `rounded-slot`, `rounded-pill`), affiche la barre supérieure complète (Favoris, Ask, Projets avec `storagePath`, Notifications, Avatar Colab/Local), la barre de recherche et filtres cumulatifs, la grille des 6 types de cartes média avec suivi SSE temps réel, et la modale d'inspection avec fonction **Remix**.
- **Pre-requisites**: Plans 01 et 02 complétés ([`.GCC/branches/plan_02_backend_brand_compiler_orchestrator.md`](plan_02_backend_brand_compiler_orchestrator.md)). Références : `UI_SPECIFICATION.md` §1–§5, `DESIGN_SPECIFICATION.md` §1–§6. Suivant dans la chaîne : [`.GCC/branches/plan_04_frontend_dock_brandkit_llm.md`](plan_04_frontend_dock_brandkit_llm.md).

## 🛠️ Step-by-Step Sequence

### Step 1: Initialisation Vite 5 + React 18 + TypeScript 5 + Tailwind v3 + Radix UI + Vitest

- [ ] **Action**: Initialiser `frontend/` avec `package.json`, `tsconfig.json`, `vite.config.ts` (proxy `/api` et `/v1` vers `http://localhost:8000` + configuration Vitest/jsdom), et `tailwind.config.js` intégrant l'intégralité des tokens `studio.*`, `borderRadius`, `boxShadow`, `fontFamily` et `keyframes` spécifiés dans `DESIGN_SPECIFICATION.md` §2.2.
- [ ] **Verify**: `npm --prefix frontend run build && npm --prefix frontend test -- --run`
- **Verification Proof**:

```text
[Pending execution — paste raw build & vitest output here]
```

### Step 2: Contrats TypeScript et client API / SSE (`frontend/src/types` & `services`) (TDD)

- [ ] **Action**: Écrire `frontend/src/__tests__/api_client.test.ts` puis implémenter `frontend/src/types/studio.ts` (miroir exact des modèles Pydantic : `Generation`, `TaskStatus`, `ModelDefinition`, `ModelCapabilities`, `BrandKit`, `Project`, `StudioConfig`) et `frontend/src/services/apiClient.ts` (appels REST typés + souscription `EventSource` SSE pour `/api/tasks/{id}/status`).
- [ ] **Verify**: `npm --prefix frontend test -- --run src/__tests__/api_client.test.ts`
- **Verification Proof**:

```text
[Pending execution — paste raw vitest output here]
```

### Step 3: Barre supérieure (`TopNavBar`), statut Colab/Local et gestionnaire de Projets (`[📁]`) (TDD)

- [ ] **Action**: Écrire `frontend/src/__tests__/header_projects.test.tsx` puis implémenter les composants isolés dans `frontend/src/components/header/` : `FavoriteFilterToggle.tsx` (`[★]`), `AskHelpDrawer.tsx` (`[▶ Ask]`), `ProjectsDrawer.tsx` (`[📁]` avec création de projet et saisie optionnelle de `storagePath` personnalisé), `NotificationsPopover.tsx` (`[🔔]`) et `WorkerStatusAvatar.tsx` (`[👤]` : popover interactif VRAM/RAM/GPU/tunnel en mode `"colab"`, pastille grise inerte `#9CA3AF` en mode `"local"`).
- [ ] **Verify**: `npm --prefix frontend test -- --run src/__tests__/header_projects.test.tsx`
- **Verification Proof**:

```text
[Pending execution — paste raw vitest output here]
```

### Step 4: Recherche globale, puces de filtrage et grille de la galerie (`MediaGallery`) (TDD)

- [ ] **Action**: Écrire `frontend/src/__tests__/gallery.test.tsx` puis implémenter `SearchAndFilterBar.tsx` (champ loupe `🔍` avec placeholder `#4B5563` + puces cumulatives `+ Image`, `+ Video`, `+ Lip sync`), `MediaGallery.tsx`, `TaskProgressCard.tsx` (carte en tête de galerie suivant le flux SSE avec pourcentage, étape et bouton d'annulation), et `MediaCard.tsx` prenant en charge les 6 variantes (`Image`, `Video` muette en boucle au survol, `Audio`, `Upscaled image 4K`, `Upscaled video 4K`, `Lip sync`) et le bouton étoile `[★]`.
- [ ] **Verify**: `npm --prefix frontend test -- --run src/__tests__/gallery.test.tsx`
- **Verification Proof**:

```text
[Pending execution — paste raw vitest output here]
```

### Step 5: Modale d'inspection grand format (`MediaPlayerModal`) et action Remix (TDD)

- [ ] **Action**: Écrire `frontend/src/__tests__/media_modal.test.tsx` puis implémenter `MediaPlayerModal.tsx` (`@radix-ui/react-dialog`) affichant le lecteur HTML5 plein écran, la fiche technique complète (prompt, `compiledPrompt`, modèle, seed, ratio, résolution, durée, `brandKitSnapshot`), le basculement Favori, les actions d'export/suppression et le bouton **Remix** qui réinjecte l'intégralité du contexte de création dans l'état du dock flottant.
- [ ] **Verify**: `npm --prefix frontend test -- --run && npm --prefix frontend run build`
- **Verification Proof**:

```text
[Pending execution — paste raw vitest & build output here]
```

## ⚠️ Mitigations & Edge Cases

- **Risk**: Consommation mémoire excessive du navigateur lorsque la galerie contient de nombreuses vidéos en prévisualisation.
- **Mitigation**: Chargement `preload="none"` par défaut sur les balises `<video>` des cartes ; déclenchement du `play()` uniquement au `onMouseEnter` et `pause()` + remise à zéro au `onMouseLeave`.
- **Risk**: Décalage de mise en page (*Layout Shift*) lors de l'apparition d'une carte de tâche en cours ou du filtrage instantané.
- **Mitigation**: Grille CSS à ratio d'aspect réservé et hauteur minimale stable sur le conteneur principal.
