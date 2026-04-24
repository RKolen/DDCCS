# Design System Plan — New Beginnings D&D Frontend

## Overview

A design system for the Gatsby + TypeScript frontend that serves a D&D
Character Consultant. The visual language is a **dark fantasy / parchment**
aesthetic — ink on aged leather, candlelit gold, weathered stone.

The system is implemented as:

- CSS custom properties (design tokens) in `src/styles/tokens.css`
- CSS Modules per component (`ComponentName.module.css`)
- Atomic Design component hierarchy (atoms → molecules → organisms → templates)

---

## 1. Design Tokens

All tokens live in `src/styles/tokens.css` as CSS custom properties. No
hardcoded values anywhere else.

### 1.1 Color Palette

```css
:root {
  /* Backgrounds */
  --color-bg-base:        #1a1208;  /* near-black parchment darkness */
  --color-bg-surface:     #2a1e0f;  /* raised card / panel surface */
  --color-bg-overlay:     #3a2a1a;  /* badge, tag, inset backgrounds */
  --color-bg-hover:       #4a3520;  /* interactive hover state */

  /* Gold / Parchment (primary accent) */
  --color-gold-bright:    #f0c060;  /* headings, focus rings, key labels */
  --color-gold-mid:       #c9a96e;  /* body text on dark, borders */
  --color-gold-muted:     #8a6d3e;  /* disabled, placeholder, secondary text */
  --color-gold-border:    #c9a96e55; /* subtle border tint */

  /* Status / Semantic */
  --color-success:        #4caf6e;  /* HP full, positive effect */
  --color-warning:        #e8a030;  /* caution, concentration, temp HP */
  --color-danger:         #c0392b;  /* low HP, failed save, death */
  --color-info:           #5b9bd5;  /* informational, spell, arcane */
  --color-neutral:        #7a6a58;  /* inactive, unknown */

  /* Text */
  --color-text-primary:   #e8d5b0;  /* main body text */
  --color-text-secondary: #a08060;  /* captions, metadata */
  --color-text-disabled:  #5a4a38;  /* disabled elements */
  --color-text-inverse:   #1a1208;  /* text on light/gold backgrounds */

  /* Rarity (D&D item colours) */
  --color-rarity-common:    #9e9e9e;
  --color-rarity-uncommon:  #4caf50;
  --color-rarity-rare:      #2196f3;
  --color-rarity-very-rare: #9c27b0;
  --color-rarity-legendary: #ff9800;
  --color-rarity-artifact:  #f44336;
}
```

### 1.2 Typography

```css
:root {
  /* Font families */
  --font-display:  'Cinzel', 'Palatino Linotype', serif;   /* headings */
  --font-body:     'Crimson Text', 'Georgia', serif;        /* body copy */
  --font-mono:     'Fira Code', 'Courier New', monospace;  /* stat values */

  /* Scale (major third — 1.25x) */
  --text-xs:   0.64rem;   /* 10px — badges, labels */
  --text-sm:   0.8rem;    /* 13px — captions, metadata */
  --text-base: 1rem;      /* 16px — body */
  --text-md:   1.25rem;   /* 20px — sub-headings */
  --text-lg:   1.563rem;  /* 25px — section titles */
  --text-xl:   1.953rem;  /* 31px — page headings */
  --text-2xl:  2.441rem;  /* 39px — display / hero */

  /* Weights */
  --font-normal:    400;
  --font-semibold:  600;
  --font-bold:      700;

  /* Line heights */
  --leading-tight:  1.2;
  --leading-normal: 1.5;
  --leading-loose:  1.8;

  /* Letter spacing */
  --tracking-tight:  -0.01em;
  --tracking-normal:  0em;
  --tracking-wide:    0.05em;
  --tracking-widest:  0.12em;
}
```

### 1.3 Spacing

```css
:root {
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
```

### 1.4 Border, Radius, Shadow

```css
:root {
  /* Borders */
  --border-thin:   1px solid var(--color-gold-border);
  --border-mid:    1px solid var(--color-gold-muted);
  --border-accent: 1px solid var(--color-gold-mid);

  /* Radii */
  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-pill: 9999px;

  /* Shadows */
  --shadow-sm:  0 1px 3px rgba(0, 0, 0, 0.5);
  --shadow-md:  0 4px 12px rgba(0, 0, 0, 0.6);
  --shadow-lg:  0 8px 24px rgba(0, 0, 0, 0.7);
  --shadow-glow-gold: 0 0 8px rgba(201, 169, 110, 0.3);

  /* Transitions */
  --transition-fast:   120ms ease;
  --transition-normal: 220ms ease;
}
```

---

## 2. Atoms

Single-purpose components with no business logic or GraphQL queries.

| Component | File | Description |
| --------- | ---- | ----------- |
| `Badge` | `atoms/Badge.tsx` | Pill label — class, rarity, school, type |
| `Button` | `atoms/Button.tsx` | Primary, secondary, ghost, danger variants |
| `Input` | `atoms/Input.tsx` | Text input with fantasy border styling |
| `StatValue` | `atoms/StatValue.tsx` | Ability score number + modifier (+3) |
| `AbilityLabel` | `atoms/AbilityLabel.tsx` | "Strength", "DEX" etc. |
| `DiceIcon` | `atoms/DiceIcon.tsx` | SVG dice (d4, d6, d8, d10, d12, d20) |
| `SpellSlotPip` | `atoms/SpellSlotPip.tsx` | Filled / empty circle for spell slots |
| `Divider` | `atoms/Divider.tsx` | Decorative horizontal rule with rune accent |
| `Tag` | `atoms/Tag.tsx` | Removable filter tag (extends Badge) |

### Badge variants

```
variant: "class" | "rarity" | "school" | "alignment" | "type"
size:    "sm" | "md"
```

### Button variants

```
variant: "primary" | "secondary" | "ghost" | "danger"
size:    "sm" | "md" | "lg"
disabled: boolean
loading:  boolean
```

---

## 3. Molecules

Two or more atoms combined into one UI concept.

| Component | File | Composes |
| --------- | ---- | -------- |
| `AbilityScore` | `molecules/AbilityScore.tsx` | `AbilityLabel` + `StatValue` |
| `SpellSlotRow` | `molecules/SpellSlotRow.tsx` | Label + row of `SpellSlotPip` |
| `SkillRow` | `molecules/SkillRow.tsx` | Proficiency pip + label + modifier |
| `CharacterBadgeGroup` | `molecules/CharacterBadgeGroup.tsx` | Class + race + alignment `Badge` |
| `SpellCard` | `molecules/SpellCard.tsx` | Name, school `Badge`, level, excerpt |
| `SearchResultItem` | `molecules/SearchResultItem.tsx` | Title, type `Badge`, excerpt |
| `StatBlock` | `molecules/StatBlock.tsx` | Monster-style stat block (name, AC, HP, speeds) |
| `ItemCard` | `molecules/ItemCard.tsx` | Item name, rarity `Badge`, description |

---

## 4. Organisms

Complete, standalone sections of a page.

| Component | File | Composes |
| --------- | ---- | -------- |
| `AbilityScoreGrid` | `organisms/AbilityScoreGrid.tsx` | 6 `AbilityScore` molecules |
| `SpellList` | `organisms/SpellList.tsx` | Filtered + grouped `SpellCard` list |
| `CharacterHeader` | `organisms/CharacterHeader.tsx` | Portrait + name + `CharacterBadgeGroup` |
| `SkillPanel` | `organisms/SkillPanel.tsx` | Full `SkillRow` list |
| `NPCCard` | `organisms/NPCCard.tsx` | NPC name, role, personality summary |
| `Navigation` | `organisms/Navigation.tsx` | Site nav with campaign title |
| `SearchBar` | `organisms/SearchBar.tsx` | `Input` + filters + submit `Button` |
| `SearchResults` | `organisms/SearchResults.tsx` | Grid of `SearchResultItem` molecules |

---

## 5. Templates

Layout shells with named slots — no real data or GraphQL queries.

| Template | File | Slots |
| -------- | ---- | ----- |
| `CharacterSheetTemplate` | `templates/CharacterSheetTemplate.tsx` | header, abilityScores, skills, spells |
| `StoryTemplate` | `templates/StoryTemplate.tsx` | title, body, sidebar |
| `CampaignDashboardTemplate` | `templates/CampaignDashboardTemplate.tsx` | partyList, sessionHistory |
| `SearchTemplate` | `templates/SearchTemplate.tsx` | searchBar, results, filters |
| `BaseTemplate` | `templates/BaseTemplate.tsx` | navigation, main, footer |

---

## 6. Global Styles

```
src/styles/
  tokens.css         # All CSS custom properties (source of truth)
  reset.css          # Box-sizing, margin reset, base font
  typography.css     # h1–h6, p, a default styles using tokens
  global.css         # Body background, scrollbar, selection colour
```

`global.css` imports all of the above in order. Gatsby's `gatsby-browser.tsx`
imports `global.css` once.

---

## 7. Implementation Order

Work top-down: tokens first, then atoms, molecules, organisms, templates.

1. `src/styles/tokens.css` — all design tokens
2. `src/styles/reset.css` + `typography.css` + `global.css`
3. Atoms: `Badge`, `Button`, `Input`, `StatValue`, `Divider`
4. Molecules: `AbilityScore`, `SearchResultItem`, `SpellCard`
5. Organisms: `AbilityScoreGrid`, `SearchBar`, `SearchResults`, `CharacterHeader`
6. Templates: `BaseTemplate`, `SearchTemplate`, `CharacterSheetTemplate`
7. Wire pages to templates with real GraphQL data

---

## 8. Fonts

Google Fonts (loaded in `gatsby-ssr.tsx` via `<link>`):

- **Cinzel** (400, 600, 700) — display / headings — classical Roman-inspired
- **Crimson Text** (400, 400i, 600) — body — elegant old-style serif
- **Fira Code** (400, 500) — stat values, dice rolls

---

## 9. Notes for Claude Artifacts / AI Design

When generating components or layouts from this plan, use these constraints:

- Dark background (`#1a1208`) with gold text (`#e8d5b0`, `#c9a96e`)
- No white backgrounds — use `--color-bg-surface` for cards
- All borders are gold-tinted, never grey
- Headings always use the display font; body uses serif
- Stat numbers use monospace for alignment
- All interactive elements have a gold glow focus ring
- Border-radius is subtle (`--radius-md` = 8px) — not bubbly
