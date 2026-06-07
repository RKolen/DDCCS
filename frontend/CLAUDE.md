# Frontend — D&D Character Consultant

Gatsby 5 + TypeScript 6 frontend that reads content from Drupal via
`gatsby-source-graphql` pointing at a `drupal/graphql_compose` v3 endpoint.

> Agent coding rules live here. For the human-facing overview (layout, pages,
> serverless functions, env), see [README.md](README.md); for setup, see
> [../docs/FRONTEND_QUICKSTART.md](../docs/FRONTEND_QUICKSTART.md).

---

## Stack

| Tool | Version | Purpose |
| ---- | ------- | ------- |
| Gatsby | 5.x | Static site generator + dev server |
| React | 18.x | Component rendering |
| TypeScript | 6.x | Strict type safety |
| gatsby-source-graphql | 5.x | Stitches remote Drupal GraphQL into Gatsby's data layer |
| gatsby-plugin-image | 3.x | Optimised image handling |

---

## Molecular Design Structure

Components follow **Atomic Design** (atoms → molecules → organisms → templates).
Each tier composes only from tiers below it.

```text
src/
|-- api/                # Gatsby serverless functions (writes + live AI)
|-- components/
|   |-- atoms/          # Smallest indivisible UI units
|   |-- molecules/      # Atoms combined into a functional group
|   |-- organisms/      # Molecules combined into a self-contained section
|   |-- templates/      # Full page layout shells (no real data)
|   |-- console/        # Admin/console screens (create, edit, validate, forge)
|   `-- layout/         # Global layout / chrome
|-- pages/              # Gatsby page components (run GraphQL page queries)
|-- templates/          # Per-node detail templates (built in gatsby-node.ts)
|-- types/              # Shared TypeScript interfaces and type aliases
|-- utils/              # Helpers
`-- styles/             # Global CSS / CSS modules (tokens.css)
```

Writes and live AI go through `src/api/` serverless functions, never directly
from components — see [README.md](README.md) for the function catalog.

### Atoms (`components/atoms/`)

Single-purpose, no business logic, no GraphQL queries.

Examples for this project:

| Component | Renders |
| --------- | ------- |
| `StatValue` | A number with an optional modifier badge (e.g. 16 / +3) |
| `AbilityLabel` | "Strength", "Dexterity", etc. with consistent typography |
| `Badge` | Small pill for rarity, class, spell school |
| `DiceIcon` | SVG dice icon by die type (d4 – d20) |
| `SpellSlotPip` | Filled / empty circle indicating a spell slot |

### Molecules (`components/molecules/`)

Two or more atoms working together as one UI concept.

Examples:

| Component | Composes |
| --------- | -------- |
| `AbilityScore` | `AbilityLabel` + `StatValue` (score + modifier) |
| `SpellSlotRow` | Label + row of `SpellSlotPip` per spell level |
| `SkillRow` | Proficiency marker + skill name + modifier |
| `CharacterBadgeGroup` | Class + race + alignment `Badge` atoms |
| `SpellCard` | Spell name, school `Badge`, level, description excerpt |

### Organisms (`components/organisms/`)

A complete, standalone section of a page.

Examples:

| Component | Composes |
| --------- | -------- |
| `AbilityScoreGrid` | 6 `AbilityScore` molecules in a grid |
| `SpellList` | Filtered + grouped list of `SpellCard` molecules |
| `CharacterHeader` | Portrait, name, `CharacterBadgeGroup` |
| `SkillPanel` | Full list of `SkillRow` molecules |
| `NPCCard` | NPC name, role, personality summary |

### Templates (`components/templates/`)

Layout shells with placeholder slots — no real data, no GraphQL.
Pages pass real data into templates as props.

Examples:

| Template | Slots |
| -------- | ----- |
| `CharacterSheetTemplate` | header, abilityScores, skills, spells |
| `StoryTemplate` | title, body, sidebar |
| `CampaignDashboardTemplate` | party list, session history |

### Pages (`pages/`)

Gatsby page components. These are the only files that run GraphQL page queries
(`useStaticQuery` or the exported `query`). Pages receive query data as props
and pass it into templates.

```text
pages/
|-- index.tsx                  # Campaign dashboard / landing
|-- characters/[id].tsx        # Character sheet
|-- stories/[id].tsx           # Story reader
`-- npcs/[id].tsx              # NPC detail
```

---

## Data Layer (Drupal → GraphQL)

`gatsby-source-graphql` stitches the remote `drupal/graphql_compose` schema
into Gatsby's data layer under the `drupal` field. All Drupal data is accessed
via `{ drupal { ... } }` in page queries. The source endpoint is
`${DRUPAL_BASE_URL}/graphql` (set in `gatsby-config.ts`) — **not** the Gatsby
dev server at `localhost:$GATSBY_PORT`.

Field names use **camelCase without the `field_` prefix** (e.g. `storyNumber`,
not `fieldStoryNumber`). The `path` field is a plain `String` (not an object).

| Drupal content type | GraphQL list query | Single-node query |
| ------------------- | ------------------ | ----------------- |
| character | `drupal { nodeCharacters(first: N) { nodes { ... } } }` | `drupal { node(id: $id) { ... on Drupal_NodeCharacter { ... } } }` |
| story | `drupal { nodeStories(first: N) { nodes { ... } } }` | `drupal { node(id: $id) { ... on Drupal_NodeStory { ... } } }` |
| item | `drupal { nodeItems(first: N) { nodes { ... } } }` | `drupal { node(id: $id) { ... on Drupal_NodeItem { ... } } }` |
| monster | `drupal { nodeMonsters(first: N) { nodes { ... } } }` | `drupal { node(id: $id) { ... on Drupal_NodeMonster { ... } } }` |
| spell | `drupal { nodeSpells(first: N) { nodes { ... } } }` | `drupal { node(id: $id) { ... on Drupal_NodeSpell { ... } } }` |

**NPCs are character nodes**, not a separate type. There is no `nodeNpcs` /
`Drupal_NodeNpc` (deprecated). Query `nodeCharacters` and filter on
`field_character_type` (exposed as `characterType`). See
[../docs/DRUPAL.md](../docs/DRUPAL.md).

Page context uses `id` (UUID string). Template variable is `$id: ID!`.

Explore the stitched schema at `http://localhost:``GATSBY_PORT``/___graphql` while the dev
server is running, or introspect Drupal directly at
```DRUPAL_URL``/graphql`.

### Query conventions

- Use page queries (exported `query`) in `pages/` — never in components.
- Use `useStaticQuery` only for truly site-wide static data (site title, etc.).
- Define query result types as local interfaces in the same file.

```tsx
// src/templates/story.tsx
export const query = graphql`
  query StoryPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeStory {
          title
          storyNumber
          body { processed }
        }
      }
    }
  }
`;
```

---

## TypeScript Rules

- Strict mode is on — every prop, parameter, and return must be typed.
- No `any`. Use `unknown` if the type is genuinely unknown, then narrow.
- No `// @ts-ignore` or `// @ts-expect-error` — fix the underlying type.
- No `// eslint-disable` comments of any kind — fix the underlying issue.
- Define shared Drupal response shapes in `src/types/drupal.ts`.
- Define GraphQL query result shapes in `src/types/queries.ts`.
- Component props interfaces live in the same file as the component.
- For third-party packages that have resolution issues with `"moduleResolution": "bundler"`,
  use `import type` where possible, or declare a local `.d.ts` shim in `src/types/`.

---

## Code Style

- No emojis in any source file.
- No default exports except Gatsby pages and templates (named exports
  everywhere else — easier to tree-shake and refactor).
- CSS Modules for component-scoped styles (`ComponentName.module.css`
  alongside the component file).
- File names: `PascalCase` for components, `camelCase` for hooks and
  utilities.

---

## Colour Rules (enforced, non-negotiable)

**Only `#RRGGBB` or `#RRGGBBAA` hex literals are permitted.** `rgba()`,
`rgb()`, `hsl()`, and `hsla()` are banned everywhere — `.css`, `.module.css`,
and inline styles in `.tsx`.

**Always prefer a `var(--token)` from `tokens.css` over a bare hex literal.**
Bare hex is only acceptable when no token exists *and* the value is truly
one-off (e.g. a specific parchment grain colour in a single gradient). In that
case add a comment explaining why no token was used.

**Canonical token file:** `frontend/src/styles/tokens.css`

| Need | Token to use |
| ---- | ------------ |
| Transparent gold border | `var(--color-gold-border)` = `#c9a96e54` |
| Success green | `var(--color-success)` = `#5a9e6f` |
| Warning amber | `var(--color-warning)` = `#e8a030` |
| Partial / mid | `var(--color-partial)` = `#c9a96e` |
| Danger red | `var(--color-danger)` = `#c0392b` |
| Danger gradient top | `var(--color-danger-mid)` = `#b04a3a` |
| Danger gradient base | `var(--color-danger-deep)` = `#832d23` |
| Danger border | `var(--color-danger-border)` = `#6b1f17` |
| Text on danger bg | `var(--color-on-danger)` = `#fff7e8` |
| Muted danger text | `var(--color-danger-text)` = `#d68a7e` |
| Info blue | `var(--color-info)` = `#5b9bd5` |
| Muted info text | `var(--color-info-text)` = `#92bce0` |

**Converting alpha:** multiply the alpha fraction by 255, round to nearest
integer, format as two-digit hex and append. Examples:
`0.12 × 255 = 31 = 0x1f` → `#c9a96e1f`; `0.5 × 255 = 128 = 0x80` → `#00000080`.

---

## Commands

```bash
# Start dev server (requires frontend/.env.development)
npm run develop

# GraphQL explorer
open http://localhost:$GATSBY_PORT/___graphql

# Type-check (no emit)
npm run type-check

# Production build
npm run build
npm run serve

# Clear Gatsby cache (fixes most weird build errors)
npm run clean
```

---

## Environment Variables — Critical Rule

Gatsby only exposes `process.env` to **browser-side** code when the variable is
prefixed with `GATSBY_`. Without the prefix the value is `undefined` at runtime.

| Prefix | Available in | Use for |
| ------ | ------------ | ------- |
| none | Build only (`gatsby-config.ts`, `gatsby-node.ts`) | Plugin auth, build secrets |
| `GATSBY_` | Browser + build | Any value a React component needs at runtime |

Never read a non-`GATSBY_` variable inside a page or component — it will be
empty in the browser even if it is set in `.env.development`.

## Environment

Credentials live in `frontend/.env.development` (gitignored — see
`.env.example`). `gatsby-config.ts` loads them via `dotenv` before the plugin
options are evaluated.

| Variable | Purpose |
| -------- | ------- |
| `DRUPAL_BASE_URL` | **Required.** Drupal site URL — no default, build fails without it. |
| `DRUPAL_USER` | Drupal account for GraphQL Basic Auth (optional for anonymous access) |
| `DRUPAL_PASSWORD` | Password for `DRUPAL_USER` |
