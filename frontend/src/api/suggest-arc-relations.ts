import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Suggest one subject's arc relationships (one model call).
 *
 * POST `{ subject, others, kind, context? }` -> sidecar `/relations/suggest`.
 *
 * The console loops this once per party member rather than asking for the
 * whole web at once: thirteen PCs against ten NPCs is 130 possible
 * connections, which will not fit in one CPU inference pass. One subject per
 * request keeps every call bounded and lets the console show real progress.
 */

interface DigestBody {
  name:     string;
  summary?: string;
  origin?:  string;
  faction?: string;
  hooks?:   string[];
}

interface SuggestBody {
  subject:  DigestBody;
  others:   DigestBody[];
  kind?:    'party' | 'npc';
  context?: string;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as SuggestBody;
  if (!body?.subject?.name?.trim()) {
    res.status(400).json({ error: 'subject.name is required' });
    return;
  }
  if (!Array.isArray(body.others) || body.others.length === 0) {
    res.status(400).json({ error: 'others must be a non-empty list' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Relation suggestion sidecar is not configured' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/relations/suggest`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: body.subject,
        others:  body.others,
        kind:    body.kind ?? 'party',
        context: body.context ?? '',
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Relations sidecar unreachable: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    res.status(sidecarRes.status).json({ error: await sidecarRes.text() });
    return;
  }
  res.status(200).json(await sidecarRes.json());
}
