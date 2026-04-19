# Frontend — D&D Character Consultant

Gatsby 5 + TypeScript 6 frontend that reads content from Drupal via
`gatsby-source-drupal` (JSON:API) and exposes it as a GraphQL layer.

---

## Stack

| Tool | Version | Purpose |
| ---- | ------- | ------- |
| Gatsby | 5.x | Static site generator + dev server |
| React | 18.x | Component rendering |
| TypeScript | 6.x | Strict type safety |
| gatsby-source-drupal | 6.x | Pulls Drupal JSON:API into GraphQL |
| gatsby-plugin-image | 3.x | Optimised image handling |

---

## Molecular Design Structure

Components follow **Atomic Design** (atoms → molecules → organisms → templates).
Each tier composes only from tiers below it.

```text
src/
|-- components/
|   |-- atoms/          # Smallest indivisible UI units
|   |-- molecules/      # Atoms combined into a functional group
|   |-- organisms/      # Molecules combined into a self-contained section
|   `-- templates/      # Full page layout shells (no real data)
|-- pages/              # Gatsby page components (use templates + real data)
|-- hooks/              # Custom React hooks (data fetching, state)
|-- types/              # Shared TypeScript interfaces and type aliases
`-- styles/             # Global CSS / CSS modules
```

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

`gatsby-source-drupal` turns every Drupal JSON:API resource into a GraphQL
node type. The naming convention is `nodeCamelCase` for content types and
`taxonomyTermCamelCase` for taxonomy terms.

| Drupal content type | GraphQL type |
| ------------------- | ------------ |
| `node--character` | `allNodeCharacter` / `nodeCharacter` |
| `node--story` | `allNodeStory` / `nodeStory` |
| `node--npc` | `allNodeNpc` / `nodeNpc` |
| `node--item` | `allNodeItem` / `nodeItem` |
| `node--spell` | `allNodeSpell` / `nodeSpell` |
| `taxonomy_term--species` | `allTaxonomyTermSpecies` |
| `taxonomy_term--character_class` | `allTaxonomyTermCharacterClass` |

Explore the full schema at `http://localhost:8000/___graphql` while the dev
server is running.

### Query conventions

- Use page queries (exported `query`) in `pages/` — never in components.
- Use `useStaticQuery` only for truly site-wide static data (site title, etc.).
- Always type query results against the interfaces in `src/types/`.

```tsx
// pages/characters/[id].tsx
import type { PageProps } from 'gatsby';
import { graphql } from 'gatsby';
import type { CharacterQuery } from '../../types/queries';

const CharacterPage: React.FC<PageProps<CharacterQuery>> = ({ data }) => (
  <CharacterSheetTemplate
    header={<CharacterHeader character={data.nodeCharacter} />}
    abilityScores={<AbilityScoreGrid scores={data.nodeCharacter?.fieldAbilityScores} />}
  />
);

export const query = graphql`
  query Character($id: String!) {
    nodeCharacter(id: { eq: $id }) {
      title
      fieldAbilityScores { ...AbilityScoresFragment }
    }
  }
`;

export default CharacterPage;
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

## Commands

```bash
# Start dev server (requires frontend/.env.development)
npm run develop          # http://localhost:8000

# GraphQL explorer
open http://localhost:8000/___graphql

# Type-check (no emit)
npm run type-check

# Production build
npm run build
npm run serve            # preview at http://localhost:9000

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
| `DRUPAL_BASE_URL` | Drupal site URL (default: `https://drupal-cms.ddev.site`) |
| `DRUPAL_USER` | gatsby_user (read-only JSON:API account) |
| `DRUPAL_PASSWORD` | gatsby_user password |
