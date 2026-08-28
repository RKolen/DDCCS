import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Read the NPC cast a campaign's played sessions name.
 *
 * POST `{ campaignName, recaps, party, known }` -> sidecar `/arc-draft/npcs`
 * -> `{ npcs: [{ name, role, known }] }`.
 *
 * A separate call from `draft-arc`: the NPC roster is not the cast, and a
 * campaign ported from elsewhere has stories full of people who have no
 * character node at all. Names marked `known` matched something already on
 * record; the rest are what the console offers to create.
 */

interface RecapBody {
  storyNumber: number;
  summary:     string;
}

interface ExtractNpcsBody {
  campaignName: string;
  recaps:       RecapBody[];
  party?:       string[];
  known?:       string[];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as ExtractNpcsBody;
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
    sidecarRes = await sidecarFetch(`${sidecarUrl}/arc-draft/npcs`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_name: body.campaignName ?? '',
        recaps: body.recaps.map(r => ({
          story_number: r.storyNumber,
          summary:      r.summary,
        })),
        party: body.party ?? [],
        known: body.known ?? [],
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
