import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Merge per-subject relation batches into one deduplicated set.
 *
 * POST `{ batches }` -> sidecar `/relations/merge`.
 *
 * Two subjects usually propose the same bond from opposite ends - A to B and
 * B to A are one relationship - so the batches cannot simply be concatenated.
 * Merging keys on the unordered character pair and keeps the more specific
 * entry.
 */

interface RelationBody {
  source:         string;
  target:         string;
  relation_type?: string;
  tier?:          number;
  note?:          string;
}

interface MergeBody {
  batches: RelationBody[][];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as MergeBody;
  if (!Array.isArray(body?.batches)) {
    res.status(400).json({ error: 'batches must be a list' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Relation suggestion sidecar is not configured' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/relations/merge`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ batches: body.batches }),
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
