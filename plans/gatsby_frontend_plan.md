# Gatsby Frontend Plan

## Overview

Build out the Gatsby/React frontend that reads from Drupal via JSON:API and
presents characters, stories, NPCs, items, and campaign data as a dark fantasy
web experience. Also covers the remaining Drupal API enablement steps required
for the source plugin to function.

**Related Documents:**

- Drupal CMS Integration: [`plans/drupal_cms_integration.md`](plans/drupal_cms_integration.md)
- TTS Web Integration: [`plans/tts_web_integration.md`](plans/tts_web_integration.md)
- Design System: [`plans/design_system_plan.md`](plans/design_system_plan.md)

---

## Status Overview

| Step | Area | Status |
| ---- | ---- | ------ |
| 1 | Enable Drupal API modules | Pending |
| 2 | Create gatsby_user + permissions | Pending |
| 3 | Configure Gatsby webhook in Drupal admin | Pending |
| 4 | Gatsby scaffold + gatsby-source-drupal | Done |
| 5 | Search page + search components | Done |
| 6 | Design system foundations | Done (partial) |
| 7 | Character page + GraphQL query | Pending |
| 8 | NPC page + GraphQL query | Pending |
| 9 | Story page + GraphQL query | Pending |
| 10 | Item page + GraphQL query | Pending |
| 11 | Campaign dashboard | Pending |

---

## Step 1 — Enable Drupal API modules

The gatsby-source-drupal plugin requires JSON:API. Basic Auth is the interim
auth method until Simple OAuth is set up.

```bash
ddev drush en jsonapi basic_auth serialization -y
ddev drush config:export -y
```

---

## Step 2 — Create gatsby_user

```bash
ddev drush user:create gatsby_user --password=<secure_password>
ddev drush user:role:add authenticated gatsby_user
```

Set the password in `drupal-cms/.ddev/.env` (gitignored):

```properties
GATSBY_DRUPAL_PASSWORD=<secure_password>
```

Configure JSON:API read permissions at `/admin/people/permissions#module-jsonapi`.

---

## Step 3 — Configure Gatsby webhook in Drupal admin

Admin: Configuration -> Gatsby -> Settings

- Preview server URL: `http://localhost:8000`

Or via drush:

```bash
ddev drush config:set gatsby.settings server_url 'http://localhost:8000' -y
ddev drush config:export -y
```

---

## Step 4-6 — Already done

- Gatsby project scaffolded in `frontend/` with TypeScript and gatsby-source-drupal
- Search page at `frontend/src/pages/search.tsx` with input and content type filters
- Atom components: `Badge`, `SearchResultItem`
- Design system plan established with dark fantasy tokens

---

## Step 7 — Character page

GraphQL query covering: name, class, species, ability scores, backstory,
personality traits, bonds, ideals, flaws, relationships, spells, feats.

File: `frontend/src/pages/characters/{nodeCharacter.title}.tsx`

---

## Step 8 — NPC page

GraphQL query covering: name, description, location, faction, voice ID.

File: `frontend/src/pages/npcs/{nodeNpc.title}.tsx`

---

## Step 9 — Story page

GraphQL query covering: title, campaign, body content, session reference.

File: `frontend/src/pages/stories/{nodeStory.title}.tsx`

---

## Step 10 — Item page

GraphQL query covering: name, type, magical properties, description.

File: `frontend/src/pages/items/{nodeItem.title}.tsx`

---

## Step 11 — Campaign dashboard

Landing page per campaign showing:

- Active character instances (filtered by `field_campaign`)
- Linked story and session nodes
- Search scoped to campaign via Milvus `field_campaign` filter

File: `frontend/src/pages/campaigns/{taxonomyTermCampaign.name}.tsx`

---

## Implementation Checklist

### Drupal API enablement

- [ ] Enable `jsonapi`, `basic_auth`, `serialization`
- [ ] Create `gatsby_user` with read permissions
- [ ] Configure Gatsby webhook URL in admin
- [ ] Export config after each change

### Gatsby pages

- [ ] Character page + GraphQL query
- [ ] NPC page + GraphQL query
- [ ] Story page + GraphQL query
- [ ] Item page + GraphQL query
- [ ] Campaign dashboard

### Design system

- [ ] Complete token definitions (colours, spacing, typography)
- [ ] Molecule components (CharacterCard, NPCCard, StoryCard, ItemCard)
- [ ] Layout components (CampaignLayout, PageLayout)
