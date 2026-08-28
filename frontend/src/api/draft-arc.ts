import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Propose the story arc a campaign's played sessions add up to.
 *
 * POST `{ campaignName, recaps, party, npcs }` -> sidecar `/arc-draft/propose`
 * -> `{ draft }`, or `{ draft: null }` when the model produced nothing usable.
 *
 * One model call over the recaps, not the story text: a campaign's bodies run
 * to hundreds of thousands of characters and will not fit a local context. The
 * proposal is never written here - the console reviews and edits it first.
 */

interface RecapBody {
  storyNumber: number;
  summary:     string;
}

interface DraftArcBody {
  campaignName: string;
  recaps:       RecapBody[];
  party?:       string[];
  npcs?:        string[];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as DraftArcBody;
  if (!Array.isArray(body?.recaps) || body.recaps.length === 0) {
    res.status(400).json({ error: 'recaps must be a non-empty list' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Arc drafting sidecar is not configured' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/arc-draft/propose`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_name: body.campaignName ?? '',
        recaps: body.recaps.map(r => ({
          story_number: r.storyNumber,
          summary:      r.summary,
        })),
        party: body.party ?? [],
        npcs:  body.npcs ?? [],
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Arc drafting sidecar unreachable: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    res.status(sidecarRes.status).json({ error: await sidecarRes.text() });
    return;
  }
  res.status(200).json(await sidecarRes.json());
}
