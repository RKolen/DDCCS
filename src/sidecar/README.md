# Sidecar — Search & Spotlight Service

A small FastAPI microservice that imports the Python engine in-process and
exposes a couple of HTTP endpoints the [Gatsby frontend](../../frontend/README.md)
calls. It exists so the frontend can use engine logic (query normalisation,
spotlight scoring) without bundling Python into the browser.

See [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) for where the sidecar sits
in the three-tier system.

---

## Run it

```bash
python3 run_sidecar.py        # from the project root
```

Host, port, log level, and reload come from config (`src/config/`) /
environment — `SIDECAR_HOST` and `SIDECAR_PORT`. `start.sh` launches it in the
background (logs to `.sidecar.log`).

---

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/health` | Readiness probe (no auth) |
| POST | `/search/parse-query` | Normalise a natural-language search query for the Milvus index |
| POST | `/eval/spotlight` | Compute spotlight scores for a campaign's characters |

Request/response shapes are defined as Pydantic models in
[models.py](models.py). Query normalisation logic is in
[query_parser.py](query_parser.py); spotlight scoring delegates to
`src.stories.spotlight_engine.SpotlightEngine`.

### Authentication

If `SIDECAR_SECRET` is set, every request except `/health` must send a matching
`X-Sidecar-Secret` header. When `SIDECAR_SECRET` is unset, all requests are
allowed (local dev default).

---

## Consumers

- `frontend/src/pages/search.tsx` — search, via `/search/parse-query`.
- `frontend/src/api/spotlight.ts` — spotlight scoring, via the sidecar.

---

## Files

| File | Purpose |
| ---- | ------- |
| `app.py` | FastAPI app, middleware, routers |
| `models.py` | Pydantic request/response models |
| `query_parser.py` | AI query normalisation |

The runner lives at the project root: `run_sidecar.py`.
