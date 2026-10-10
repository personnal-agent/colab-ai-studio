# Spécifications Graphiques & Design System (Tokens) — Colab AI Studio

---

## 1. Philosophie Visuelle & Fondations

Le Design System de **Colab AI Studio** s'inspire directement des studios de création générative professionnels modernes (Wan 2.5, Runway, Kling AI, Luma Dream Machine).
Adapté à une architecture **React + Vite + Tailwind CSS**, il allie :
- **Une clarté optique maximale** : Fond clair, hiérarchie visuelle contrastée, absence de bruit graphique superflu.
- **Une géométrie adoucie et organique** : Composants en pilules (*pill-shaped*), fentes de conditionnement aux angles arrondis, dock flottant surélevé.
- **Une intégration directe Tailwind & Radix UI** : Les tokens de design se traduisent directement en classes utilitaires Tailwind v3 et en primitives d'accessibilité sans style.

---

## 2. Palette de Couleurs & Configuration Tailwind

L'intégralité des teintes a été calibrée à partir des 17 captures fournies dans `ui-specifications/`.

### 2.1. Tableau des Nuances Extraites

| Token Sémantique | Code Hexadécimal | Classe Tailwind | Utilisation Concrète |
| :--- | :--- | :--- | :--- |
| `surface-canvas` | `#F9FAFB` | `bg-gray-50` | Arrière-plan général de l'application et de la grille. |
| `surface-card` | `#FFFFFF` | `bg-white` | Cartes d'en-tête, grille de la galerie, dock flottant. |
| `surface-elevated` | `#FFFFFF` | `bg-white` | Menus déroulants, popovers et modales. |
| `surface-subtle` | `#F3F4F6` | `bg-gray-100` | Fentes de références (`Image refs`), champs de saisie, pilules inactives. |
| `surface-active` | `#E5E7EB` | `bg-gray-200` | Fond de pilule active ou au clic. |
| `surface-overlay` | `rgba(0, 0, 0, 0.45)` | `bg-black/45` | Voile d'ombrage pour les modales. |
| `text-primary` | `#111827` | `text-gray-900` | Noms de modèles, titres principaux, valeurs actives. |
| `text-secondary` | `#4B5563` | `text-gray-600` | Descriptions de modèles, onglets inactifs. |
| `text-muted` | `#6B7280` | `text-gray-500` | En-têtes de colonnes et sous-titres de menus. |
| `text-placeholder` | `#4B5563` | `text-gray-600` | Placeholder du prompt et champ de recherche (contraste WCAG AA >= 4.5:1 sur surface subtile, ratio 7.0:1). |
| `text-inverted` | `#FFFFFF` | `text-white` | Icônes et textes sur éléments sombres (`↑`). |
| `action-primary` | `#111827` | `bg-gray-900` | Bouton circulaire d'envoi (`↑`). |
| `badge-beta-bg` | `#F3F4F6` | `bg-gray-100` | Fond du badge `Beta`. |
| `badge-beta-text` | `#374151` | `text-gray-700` | Texte du badge `Beta`. |
| `badge-warning-bg`| `#FEF3C7` | `bg-amber-100` | Fond du badge `! Slower than usual`. |
| `badge-warning-text`| `#B45309` | `text-amber-700`| Texte du badge d'avertissement. |
| `badge-new-bg` | `#EEF2FF` | `bg-indigo-50` | Fond du badge `New`. |
| `badge-new-text` | `#4338CA` | `text-indigo-700`| Texte du badge de nouveauté. |
| `border-default` | `#E5E7EB` | `border-gray-200`| Pourtour du dock flottant, bordure des cartes et pilules. |
| `border-subtle` | `#F3F4F6` | `border-gray-100`| Séparateurs horizontaux légers. |

---

### 2.2. Configuration `tailwind.config.js`

```javascript
import animate from 'tailwindcss-animate';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        studio: {
          canvas: '#F9FAFB',
          card: '#FFFFFF',
          subtle: '#F3F4F6',
          active: '#E5E7EB',
          placeholder: '#4B5563',
          border: '#E5E7EB',
          divider: '#F3F4F6',
        },
      },
      borderRadius: {
        'dock': '24px',
        'slot': '12px',
        'menu': '16px',
        'pill': '9999px',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
        'tab-active': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
        'dropdown': '0 12px 24px -4px rgba(0, 0, 0, 0.08), 0 4px 8px -2px rgba(0, 0, 0, 0.04)',
        'floating-dock': '0 20px 32px -6px rgba(0, 0, 0, 0.12), 0 8px 16px -4px rgba(0, 0, 0, 0.05)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'in': 'fade-in 150ms ease-out, zoom-in-95 150ms ease-out',
        'out': 'fade-out 150ms ease-in, zoom-out-95 150ms ease-in',
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'fade-in': { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        'fade-out': { '0%': { opacity: '1' }, '100%': { opacity: '0' } },
        'zoom-in-95': { '0%': { transform: 'scale(0.95)' }, '100%': { transform: 'scale(1)' } },
        'zoom-out-95': { '0%': { transform: 'scale(1)' }, '100%': { transform: 'scale(0.95)' } },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(0.98)' },
        },
      },
    },
  },
  plugins: [animate],
};
```

---

## 3. Système Typographique

### 3.1. Échelle Modulaire

| Niveau Typographique | Classe Tailwind | Taille / Hauteur | Graisse | Rôle Ergonomique |
| :--- | :--- | :--- | :--- | :--- |
| **Page Title** | `text-2xl leading-8 font-semibold` | `24px` / `32px` | Semibold (`600`) | Titre principal ("Image & Video"). |
| **Section Title** | `text-base leading-6 font-semibold`| `16px` / `24px` | Semibold (`600`) | Titre des cartes d'en-tête ("Avatars", "Brand kit"). |
| **Prompt Body** | `text-sm leading-[22px] font-normal` | `14px` / `22px` | Regular (`400`) | Texte saisi dans la zone de prompt. |
| **Menu Section Header**| `text-[13px] leading-[18px] font-medium` | `13px` / `18px` | Medium (`500`) | En-têtes ("Aspect ratio", "Editing", "Frame rate"). |
| **Model Card Title** | `text-sm leading-5 font-semibold` | `14px` / `20px` | Semibold (`600`) | Nom du modèle dans le sélecteur. |
| **Model Description**| `text-xs leading-4 font-normal` | `12px` / `16px` | Regular (`400`) | Explication succincte du modèle. |
| **Pill Value** | `text-xs leading-4 font-medium` | `12px` / `16px` | Medium (`500`) | Texte d'une pilule de réglage ("16:9", "1K", "2x"). |
| **Micro Badge** | `text-[10px] leading-[14px] font-semibold`| `10px` / `14px` | Semibold (`600`) | Badges de statut ("Beta", "! Slower than usual"). |

---

## 4. Système d'Espacement & Dimensions des Composants

Incrément fondamental : **4px** (échelle base 4/8 Tailwind).

### 4.1. Composants Structuraux

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ COMPOSANT : DOCK FLOTTANT DE PROMPT (FloatingPromptDock)                               │
│ • Largeur max : max-w-4xl (~896px) centrée sur l'écran                                 │
│ • Position : fixed bottom-8 left-1/2 -translate-x-1/2                                  │
│ • Padding interne : p-4 sm:p-5                                                         │
│ • Espace vertical interne : space-y-3                                                  │
│ • Rayon : rounded-dock (24px)                                                          │
│ • Ombre : shadow-floating-dock                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ COMPOSANT : FENTES DE CONDITIONNEMENT (ReferenceSlot)                                  │
│ • Dimensions : w-20 h-16 (80px × 64px)                                                 │
│ • Forme : rounded-slot (12px), bg-studio-subtle                                        │
│ • Contenu : icône w-5 h-5 (20px), texte text-[11px] font-medium                        │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ COMPOSANT : PILULE DE RÉGLAGE (ParamPill)                                              │
│ • Hauteur : h-8 (32px), padding px-3                                                   │
│ • Forme : rounded-pill (9999px), border border-studio-border                           │
│ • Icônes : w-3.5 h-3.5 (14px)                                                          │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ COMPOSANT : BOUTON CIRCULAIRE DE SOUMISSION (SubmitButton)                             │
│ • Dimensions : w-10 h-10 (40px × 40px), rounded-full                                   │
│ • Fond : bg-gray-900 text-white                                                        │
│ • Icône : flèche montante w-4 h-4 (16px)                                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Mappage avec les Primitives Radix UI

L'assemblage des composants interactifs s'appuie sur la suite Radix UI :

| Composant de l'Interface | Primitive Radix Recommandée | Rôle d'Accessibilité & Comportement |
| :--- | :--- | :--- |
| **Onglets de Catégorie** | `@radix-ui/react-tabs` | Gestion du focus clavier (flèches gauche/droite) et changement instantané sans rechargement. |
| **Sélecteur de Modèle** | `@radix-ui/react-popover` | Panneau ancré avec autofocus dans le champ de recherche et fermeture par `Escape` ou clic extérieur. |
| **Pilules de Paramètres** | `@radix-ui/react-dropdown-menu` | Menu accessible avec gestion de l'item sélectionné (`DropdownMenuRadioGroup`). |
| **Modales de Détail / Brand Kit**| `@radix-ui/react-dialog` | Piégeage du focus (*focus trap*) et voile d'ombrage animé. |
| **Infobulles de Quota** | `@radix-ui/react-tooltip` | Explication rapide du solde de calcul restant. |

---

## 6. Micro-Interactions & États

### 6.1. États des Pilules
- **Repos (`default`)** : `bg-white border-gray-200 text-gray-900 hover:bg-gray-100 transition-colors duration-150`
- **Actif / Menu Ouvert (`open`)** : `bg-gray-200 border-gray-300 text-gray-900`
- **Désactivé (`disabled`)** : `opacity-40 cursor-not-allowed`

### 6.2. Transitions & Fluidité
- **Ouverture des Popovers / Menus (via `tailwindcss-animate`)** :
  ```css
  data-[state=open]:animate-in data-[state=closed]:animate-out
  data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
  data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
  ```
- **Durée recommandée** : `150ms` à `200ms` avec courbe `ease-out`.
- **Zéro Layout Shift** : Les hauteurs et espacements des fentes de référence sont figés pour éviter tout sautillement visuel lors de la bascule de mode.
