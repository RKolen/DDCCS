# Frontend Quick Start

Get the full system running and drive it from the Gatsby frontend. By the end
you will have Drupal, the search sidecar, and the Gatsby dev server up, and you
will create a character and an AI-generated story without ever logging into
Drupal.

For how the pieces fit together, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Prerequisites

| Tool | Why |
| ---- | --- |
| [DDEV](https://ddev.readthedocs.io/) | Runs Drupal + Ollama + Milvus + Solr in containers |
| Node.js 18+ and npm | Gatsby frontend |
| Python 3.8+ | Search/spotlight sidecar |
| [mkcert](https://github.com/FiloSottile/mkcert) | Local TLS cert DDEV uses for `*.ddev.site` |
| Ollama models | Pulled inside the DDEV Ollama service (chat + embeddings) |

Install Python deps once:

```bash
pip install -r requirements.txt
```

---

## 2. Configure environment

Two env files, root first.

```bash
# Project root — shared service credentials
cp .env.example .env
```

Fill in at least:

- `DRUPAL_BASE_URL` and
  `DRUPAL_GRAPHQL_TOKEN` if your endpoint needs auth.
- `AI_CREATIVE_BASE_URL` and `AI_CREATIVE_MODEL` — the Ollama-compatible
  endpoint and model used for story generation.
- `OLLAMA_API_KEY` (Ollama accepts any non-empty value).
- `RAG_WIKI_BASE_URL` / `RAG_RULES_BASE_URL` if you use RAG.

```bash
# Frontend — browser/site settings
cp frontend/.env.example frontend/.env.development
```

Fill in `SITE_URL`, `SITE_TITLE`, and `GATSBY_DRUPAL_BASE_URL`. Use the **HTTP**
Drupal URL here if Node rejects DDEV's self-signed cert. The AI and RAG display
values are bridged automatically from the root `.env`.

> Only `GATSBY_`-prefixed variables reach browser code. See
> [frontend/README.md](../frontend/README.md#environment-variables).

---

## 3. Start everything

The one-command path (brings up Drupal + sidecar + Gatsby, skips the legacy
CLI):

```bash
./start.sh --no-cli
```

This runs `ddev start` (Drupal, Ollama, Milvus, Solr), launches the sidecar in
the background, and starts the Gatsby dev server. Logs go to `.sidecar.log` and
`.gatsby.log`.

Or do it manually:

```bash
cd drupal-cms && ddev start && cd ..
python3 run_sidecar.py &
cd frontend && npm run develop
```

---

## 4. First-run index

Seed the Milvus vector index so search and semantic retrieval work:

```bash
python3 -m src.cli.dnd_consultant --reindex
# check status:
python3 -m src.cli.dnd_consultant --milvus-status
```

(These flags run engine utilities only — they do not open the deprecated
interactive CLI menu.)

Then open the app:

- Frontend: <http://localhost:`GATSBY_PORT`>
- GraphQL explorer (stitched schema): <http://localhost:`GATSBY_PORT`/___graphql>
- Sidecar health: <http://localhost:`SIDECAR_PORT/health`>

---

## 5. Do everything from the frontend

Each task maps to a page and the serverless function or service behind it.

| Task | Where in the UI | Backed by |
| ---- | --------------- | --------- |
| Browse characters / NPCs | Characters, NPCs pages | Drupal GraphQL |
| View a character sheet | character detail | Drupal GraphQL |
| Edit a character's optional fields | character edit screen | `api/update-character.ts` |
| Create a campaign | Party page | `api/campaigns.ts` |
| Add a character to a campaign | Party page | `api/campaign-party.ts` |
| AI-generate a story | story forge | `api/generate-story.ts` (streams) |
| Save a finished story | story forge | `api/create-story.ts` |
| Read stories | Stories, Campaign Reader | Drupal GraphQL |
| Items / monsters / spells | Items, Monsters pages | Drupal GraphQL |
| Search | Search page | sidecar `/search/parse-query` + Milvus |
| Audit NPC profile completeness | NPC validator screen | Drupal GraphQL + engine |

**Try it:** open the story forge, pick a campaign and party, enter beats, and
generate — text streams in live from the LLM. Save it, and it is written to
Drupal via `createStory`; the new story appears on the Stories page after
Gatsby's 30-second refetch (or restart the dev server).

---

## 6. Troubleshooting

| Symptom | Fix |
| ------- | --- |
| Gatsby cannot reach Drupal / TLS error | Use the HTTP `GATSBY_DRUPAL_BASE_URL`, or trust DDEV's mkcert CA (`NODE_EXTRA_CA_CERTS=$HOME/.local/share/mkcert/rootCA.pem`). `start.sh` does this for you. |
| Stale schema / weird build errors | `cd frontend && npm run clean`, then `npm run develop`. |
| Schema missing a new field/type | Re-run `ddev drush config:import -y && ddev drush cache:rebuild`, then `npm run clean`. |
| Story generation returns no content | Confirm `AI_CREATIVE_MODEL` is pulled and loaded in the DDEV Ollama service. |
| Search returns nothing | Re-run `--reindex`; confirm the sidecar is up at `:$SIDECAR_PORT/health`. |
| Inspect background services | `tail -f .gatsby.log` / `tail -f .sidecar.log`. |

---

## See also

- [frontend/README.md](../frontend/README.md) — frontend layout and functions.
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — the three tiers and data flow.
- [docs/DRUPAL.md](DRUPAL.md) — content model and GraphQL exposure.
