# Player Roles & Auth Plan

## Overview

Introduce two Drupal user roles — **Player** and **DM** — and wire them into
the Gatsby frontend so that:

- A Player logs in and sees only the one character node assigned to them.
- A DM sees all characters, all NPCs, and full campaign data.

The site stays a static Gatsby build for unauthenticated visitors; role-aware
behaviour is layered on top at runtime via a thin API proxy that exposes only
what the authenticated user is allowed to see.

**Related Documents:**

- Drupal CMS Integration: [`plans/drupal_cms_integration.md`](plans/drupal_cms_integration.md)
- Gatsby Frontend: [`plans/gatsby_frontend_plan.md`](plans/gatsby_frontend_plan.md)

---

## Status Overview

| Step | Area | Status |
| ---- | ---- | ------ |
| 1 | Drupal roles + `field_player` on character | Pending |
| 2 | Simple OAuth consumer + scopes | Pending |
| 3 | GraphQL Compose user query (current viewer) | Pending |
| 4 | Gatsby runtime auth context (login flow) | Pending |
| 5 | Player character redirect | Pending |
| 6 | DM-only content gates in the FE | Pending |
| 7 | Drupal access control (field-level) | Pending |

---

## Architecture Decision: Static Build vs. Runtime Auth

Gatsby is a static site generator. Full per-user SSR is not its model. The
recommended approach for this project:

- Build once with the DM credentials (all content in the Gatsby data layer).
- At runtime, fetch the logged-in user's identity from Drupal via a small
  **REST or GraphQL call** (`/api/me` or the GraphQL Compose `viewer` query).
- Use the returned `assignedCharacterId` to gate the React UI — players are
  redirected to their character page; non-assigned routes show a "forbidden"
  state.
- Drupal enforces the real access boundary server-side via field-level
  permissions and JSON:API / GraphQL access policies.

This keeps the build pipeline unchanged and avoids adding a Node.js SSR server.

---

## Step 1 — Drupal Roles and `field_player` on Character

### 1a. Create roles

```bash
ddev drush role:create player "Player"
ddev drush role:create dm "Dungeon Master"
ddev drush config:export -y
```

### 1b. Add `field_player` (user reference) to the character content type

Add a new field via Drupal UI or drush config:

- **Field type:** Entity reference (User)
- **Machine name:** `field_player`
- **Label:** Assigned Player
- **Cardinality:** 1 (each character belongs to at most one player)
- **Required:** No (NPCs and DM-only characters have no player)

Export config after adding:

```bash
ddev drush config:export -y
```

The resulting config file will be
`config/sync/field.field.node.character.field_player.yml`.

### 1c. Assign characters to players

In Drupal admin, edit each player-character node and set the
"Assigned Player" field to the corresponding Drupal user account.

---

## Step 2 — Simple OAuth Consumer and Scopes

Simple OAuth is already required (`drupal/simple_oauth` in composer.json).

### 2a. Enable and configure

```bash
ddev drush en simple_oauth -y
ddev drush config:export -y
```

### 2b. Create an OAuth consumer for the Gatsby frontend

In Drupal admin at `/admin/config/services/consumer/add`:

- **Label:** Gatsby Frontend
- **Secret:** store in `drupal-cms/.ddev/.env` as `OAUTH_CLIENT_SECRET`
- **Scopes:** `player`, `dm` (create these as OAuth scopes)
- **Grant type:** Authorization Code + PKCE (no client secret in the browser)

### 2c. Define scopes

Create two OAuth scopes at `/admin/config/services/oauth2/scopes`:

| Scope | Description | Role granted |
| ----- | ----------- | ------------ |
| `player` | Read own character | Player |
| `dm` | Full campaign access | Dungeon Master |

---

## Step 3 — GraphQL Compose Viewer Query

GraphQL Compose supports exposing the current authenticated user when
`graphql_compose_users` is enabled.

### 3a. Enable the submodule

```bash
ddev drush en graphql_compose_users -y
ddev drush config:export -y
```

### 3b. Expose `field_player` in the GraphQL schema

In `graphql_compose.settings.graphql_compose_server.yml`, ensure
`field_player` is included in the character entity type exposure. Export config.

### 3c. Add a `viewer` query

GraphQL Compose exposes a `viewer` (or `currentUser`) query. Use it in the
Gatsby runtime (not the build query) to fetch the logged-in user's ID and
their assigned character:

```graphql
query CurrentViewer {
  viewer {
    id
    name
    roles
    ... on Drupal_User {
      assignedCharacter: reverseFieldPlayerNode(first: 1) {
        nodes {
          id
          path
        }
      }
    }
  }
}
```

This query runs client-side after login; it is NOT part of the Gatsby build.

---

## Step 4 — Gatsby Runtime Auth Context

### 4a. AuthContext

Create `frontend/src/context/AuthContext.tsx`:

- Stores `{ userId, roles, assignedCharacterId, assignedCharacterPath }`.
- On mount, checks for a stored OAuth token (localStorage).
- If a token exists, fetches the `viewer` query against the Drupal GraphQL
  endpoint with the Bearer token.
- Exposes `login()` (redirects to Drupal OAuth authorize URL) and `logout()`.

### 4b. PKCE login flow

Since the frontend is a static SPA, use the Authorization Code + PKCE flow:

1. `login()` generates a code verifier/challenge and redirects to
   `GATSBY_DRUPAL_BASE_URL/oauth/authorize?client_id=...&code_challenge=...`
2. Drupal redirects back to `GATSBY_SITE_URL/auth/callback?code=...`
3. The callback page exchanges the code for an access token via
   `GATSBY_DRUPAL_BASE_URL/oauth/token`.
4. The token is stored in `localStorage` (or `sessionStorage` for
   session-only auth).

### 4c. Auth callback page

Create `frontend/src/pages/auth/callback.tsx`:

- Reads `code` and `state` from the URL query string.
- Exchanges for token via fetch to Drupal `/oauth/token`.
- Redirects to the player's character path (or `/` for DMs).

### 4d. Environment variables

Add to `frontend/.env.development` (and `.env.example`):

```properties
GATSBY_OAUTH_CLIENT_ID=<consumer uuid from Drupal>
GATSBY_OAUTH_AUTHORIZE_URL=http://localhost:8080/oauth/authorize
GATSBY_OAUTH_TOKEN_URL=http://localhost:8080/oauth/token
GATSBY_OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
```

---

## Step 5 — Player Character Redirect

In `AuthContext` (or a `useEffect` in `characters.tsx`), once the viewer query
resolves:

```ts
if (hasRole('player') && assignedCharacterPath) {
  navigate(assignedCharacterPath);
}
```

The `/characters` list page stays accessible only to DMs. For players visiting
`/characters`, they are immediately redirected to their own character page.

If a player visits another character's URL directly, the character template
checks `assignedCharacterPath !== location.pathname` and renders a
`<ForbiddenState />` component instead of the character sheet.

---

## Step 6 — DM-Only Content Gates in the FE

Use the auth context role check throughout the UI:

| Location | Gate |
| -------- | ---- |
| `/characters` list page | `dm` role only — players redirected |
| `/npcs` list page | `dm` role only |
| Story pages | Both roles can read; DM sees edit link |
| Character sheet | Player sees own only; DM sees all |
| Nav topbar | Show/hide "Characters", "NPCs" links by role |

Helper hook in `frontend/src/hooks/useAuth.ts`:

```ts
export function useAuth() {
  const { roles, assignedCharacterPath } = useContext(AuthContext);
  return {
    isDM: roles.includes('dm'),
    isPlayer: roles.includes('player'),
    assignedCharacterPath,
  };
}
```

---

## Step 7 — Drupal Server-Side Access Control

The frontend role gates are UX conveniences. Real enforcement happens in
Drupal:

### 7a. JSON:API / GraphQL permissions

- Anonymous and `authenticated` roles: read access to all published content
  (current behaviour, supports the static build).
- No change needed for the build user.

### 7b. Character owner check (optional hardening)

For a small campaign this is optional, but for future multi-table use:

- Install `drupal/content_access` or write a small custom module that
  implements `hook_node_access()` to restrict character nodes so only the
  assigned player (and DMs) can view their data via the API.

This ensures that even a player who guesses a UUID cannot fetch another
character's private stats through the GraphQL endpoint.

---

## File Checklist

### Drupal (config/sync/)

- [ ] `user.role.player.yml`
- [ ] `user.role.dm.yml`
- [ ] `field.storage.node.field_player.yml`
- [ ] `field.field.node.character.field_player.yml`
- [ ] `core.entity_form_display.node.character.default.yml` (updated)
- [ ] Simple OAuth consumer and scope config files

### Frontend (frontend/src/)

- [ ] `context/AuthContext.tsx` — OAuth state, viewer query, login/logout
- [ ] `hooks/useAuth.ts` — role helper
- [ ] `pages/auth/callback.tsx` — PKCE token exchange
- [ ] Updated `pages/characters.tsx` — DM gate + player redirect
- [ ] Updated `pages/npcs.tsx` — DM gate
- [ ] Updated `components/templates/character.tsx` — forbidden state for wrong player
- [ ] Updated `components/layout/GlobalTopbar.tsx` — role-aware nav links
- [ ] Updated `frontend/.env.example` — OAuth env vars

---

## Open Questions

1. **Session persistence** — localStorage token vs. cookie session. PKCE with
   localStorage is standard for SPAs but requires short token TTL and refresh
   token rotation.
2. **Token refresh** — Simple OAuth supports refresh tokens. The auth context
   should silently refresh the access token before expiry.
3. **Multi-character players** — `field_player` is cardinality 1 on the
   character side. If a player ever has two characters (e.g. one retires),
   the redirect logic will need to show a small picker rather than
   auto-redirecting.
4. **Unauthenticated visitors** — Currently all content is public. Once player
   role gates are in place, decide whether anonymous visitors can still browse
   the full site (lore-style) or are blocked at the root.
