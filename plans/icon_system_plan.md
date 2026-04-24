# Icon System Plan — New Beginnings D&D Frontend

## Overview

Two complementary icon sets, cleanly separated by purpose:

| Set | Purpose | Licence | Delivery |
|---|---|---|---|
| **Game Icons** | D&D domain icons (dice, weapons, spells, classes, conditions) | CC BY 3.0 | SVG files in `public/icons/game/` |
| **Lucide** | UI chrome (search, close, chevron, settings, external link) | ISC | CDN or npm package |

---

## 1. Game Icons (https://game-icons.net)

### Why Game Icons

- 4 000+ fantasy/RPG SVGs, all monochrome and consistent stroke style
- Designed for exactly this domain — dice, swords, wands, skulls, spell schools, creature types
- CC BY 3.0: free for commercial use with attribution (one line in the footer or a `/licenses` page is enough)
- All SVGs have a uniform `viewBox="0 0 512 512"`, making them trivially resizable

### Recommended icon subset

Download these specific icons from https://game-icons.net (search by name):

#### Dice
| Icon name | File | Usage |
|---|---|---|
| `dice-d4` | `dice-d4.svg` | D4 roll indicator |
| `dice-d6` | `dice-d6.svg` | D6 roll indicator |
| `dice-d8` | `dice-d8.svg` | D8 roll indicator |
| `dice-d10` | `dice-d10.svg` | D10 roll indicator |
| `dice-d12` | `dice-d12.svg` | D12 roll indicator |
| `dice-d20` | `dice-d20.svg` | D20 roll indicator — most prominent |

#### Combat & Weapons
| Icon name | File | Usage |
|---|---|---|
| `crossed-swords` | `crossed-swords.svg` | Combat / attack action |
| `broadsword` | `broadsword.svg` | Melee weapon slot |
| `arrow-flights` | `arrow-flights.svg` | Ranged weapon slot |
| `shield` | `shield.svg` | AC / defense |
| `round-shield` | `round-shield.svg` | Armor category |

#### Magic & Spells
| Icon name | File | Usage |
|---|---|---|
| `magic-swirl` | `magic-swirl.svg` | Spellcasting / spell slot |
| `fire-spell-cast` | `fire-spell-cast.svg` | Evocation school |
| `crystal-ball` | `crystal-ball.svg` | Divination school |
| `shadow-follower` | `shadow-follower.svg` | Illusion school |
| `lightning-arc` | `lightning-arc.svg` | Conjuration school |
| `holy-symbol` | `holy-symbol.svg` | Abjuration / divine |
| `book-cover` | `book-cover.svg` | Ritual spell |
| `concentration-orb` | `concentration-orb.svg` | Concentration indicator |

#### Character & Class
| Icon name | File | Usage |
|---|---|---|
| `muscle-up` | `muscle-up.svg` | Strength |
| `run` | `run.svg` | Dexterity / speed |
| `heart-plus` | `heart-plus.svg` | Constitution / HP |
| `brain` | `brain.svg` | Intelligence |
| `eye` | `eye.svg` | Wisdom / Perception |
| `charm` | `charm.svg` | Charisma |
| `cowled` | `cowled.svg` | Wizard class |
| `knight-helmet` | `knight-helmet.svg` | Fighter / Paladin class |
| `hood` | `hood.svg` | Rogue class |
| `wolf-head` | `wolf-head.svg` | Ranger class |
| `holy-grail` | `holy-grail.svg` | Cleric class |

#### Conditions & Status
| Icon name | File | Usage |
|---|---|---|
| `heart-beats` | `heart-beats.svg` | HP / healing |
| `skull` | `skull.svg` | Death saves / danger |
| `poison-bottle` | `poison-bottle.svg` | Poisoned condition |
| `burning-passion` | `burning-passion.svg` | Burning / fire damage |
| `frozen-orb` | `frozen-orb.svg` | Frozen / restrained |
| `stars-stack` | `stars-stack.svg` | Inspiration |

#### Items
| Icon name | File | Usage |
|---|---|---|
| `swap-bag` | `swap-bag.svg` | Inventory / equipment |
| `gem-pendant` | `gem-pendant.svg` | Magic item |
| `ring` | `ring.svg` | Ring slot |
| `scroll-unfurled` | `scroll-unfurled.svg` | Scroll / story entry |
| `potion-ball` | `potion-ball.svg` | Potion / consumable |

### File structure

```
public/
└── icons/
    └── game/
        ├── dice-d4.svg
        ├── dice-d6.svg
        ├── dice-d8.svg
        ├── dice-d10.svg
        ├── dice-d12.svg
        ├── dice-d20.svg
        ├── crossed-swords.svg
        ├── broadsword.svg
        ...
```

### Download script (optional)

Game Icons provides a ZIP of the full set (~200 MB). Alternatively use their
API to fetch individual icons:

```bash
# Example: fetch a single icon SVG
curl "https://game-icons.net/icons/ffffff/000000/1x1/delapouite/dice-d20.svg" \
  -o public/icons/game/dice-d20.svg
```

URL pattern: `https://game-icons.net/icons/{fg}/{bg}/{style}/{author}/{name}.svg`
- `fg` = foreground hex (use `ffffff` for white fill — recolour via CSS)
- `bg` = background hex (use `transparent` or `000000`)
- `style` = `1x1` (square)
- `author` = icon creator (shown on each icon page)

### Usage in React

```tsx
// atoms/DiceIcon.tsx
interface DiceIconProps {
  die: 'd4' | 'd6' | 'd8' | 'd10' | 'd12' | 'd20';
  size?: number;
  color?: string;
}

export function DiceIcon({ die, size = 20, color = 'currentColor' }: DiceIconProps) {
  return (
    <img
      src={`/icons/game/dice-${die}.svg`}
      alt={die}
      width={size}
      height={size}
      style={{ filter: `invert(1) sepia(1) saturate(2) hue-rotate(10deg)`, opacity: 0.9 }}
    />
  );
}
```

**CSS recolouring tip:** Game Icons SVGs use `fill` on the path. The cleanest
way to apply the design system gold colour is via an SVG `<use>` with
`currentColor`, or a CSS `filter` that maps white → gold. A utility:

```css
/* In tokens.css — reusable filter for gold-mid (#c9a96e) */
--filter-gold: invert(72%) sepia(22%) saturate(600%) hue-rotate(10deg) brightness(95%);
--filter-gold-bright: invert(82%) sepia(28%) saturate(700%) hue-rotate(5deg);
```

### Attribution

Add one line to the site footer or a `/licenses` route:

```
D&D domain icons from Game Icons (https://game-icons.net), CC BY 3.0.
```

---

## 2. Lucide (https://lucide.dev)

### Why Lucide

- Clean, consistent 24px stroke icons for UI chrome
- No fantasy domain overlap with Game Icons — strict separation
- ISC licence (no attribution required)
- Available as `lucide-react` npm package, or individually via CDN

### Recommended icons

| Icon | Component name | Usage |
|---|---|---|
| Search | `<Search />` | Search bar |
| X | `<X />` | Close / dismiss |
| ChevronDown | `<ChevronDown />` | Dropdowns, accordions |
| ChevronRight | `<ChevronRight />` | Nav expansion, breadcrumb |
| ChevronLeft | `<ChevronLeft />` | Back navigation |
| Plus | `<Plus />` | Add NPC, add story |
| Settings | `<Settings />` | Config / settings page |
| ExternalLink | `<ExternalLink />` | Link to Drupal admin |
| Menu | `<Menu />` | Mobile nav toggle |
| AlertTriangle | `<AlertTriangle />` | Warning / caution messages |
| CheckCircle | `<CheckCircle />` | Success confirmation |
| Info | `<Info />` | Info tooltip |

### Installation

```bash
npm install lucide-react
```

```tsx
import { Search, ChevronDown } from 'lucide-react';

// Usage — always match the gold token colours
<Search size={16} color="var(--color-gold-mid)" />
```

### CDN (no npm)

```html
<script src="https://unpkg.com/lucide@latest"></script>
<script>lucide.createIcons();</script>
<!-- Then use: <i data-lucide="search"></i> -->
```

---

## 3. Rules & anti-patterns

1. **Never mix sets in the same context.** Game Icons for D&D domain, Lucide for UI chrome. Never use a Lucide sword or a Game Icons search magnifier.
2. **Never inline SVG paths by hand** — always reference the source file or component.
3. **No emoji as icons.** Per `frontend/CLAUDE.md`, no emoji in source files.
4. **No Unicode substitutes** for proper icons (e.g. `⚔` as a nav logo is a temporary placeholder — replace with `crossed-swords.svg` once icons are downloaded).
5. **Consistent sizing:** Lucide icons at 16px inline, 20px in buttons. Game Icons at 20px inline, 32px in large display contexts (e.g. spell school badges).
6. **Always provide `aria-label` or `aria-hidden`** depending on whether the icon is decorative or communicates meaning.

---

## 4. Implementation order

1. Download the dice icons (d4–d20) first — these are the most visible and blockers for the `DiceIcon` atom.
2. Implement `DiceIcon` atom using the downloaded SVGs.
3. Add Lucide for the `SearchBar` organism (replaces plain text button).
4. Download class icons (cowled, knight-helmet, hood, wolf-head, holy-grail) for character badges.
5. Download condition/status icons for character sheet.
6. Audit every `<img alt="">` and `role="img"` for accessibility.
