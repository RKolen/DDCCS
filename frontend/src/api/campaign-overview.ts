import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { synthesizeOverview, type SessionSummary } from '../utils/aiSummary';

/**
 * Synthesize per-session recaps into one flowing campaign overview.
 *
 * POST `{ summaries: [{ storyNumber, summary }] }` -> `{ overview }`. Used by
 * the campaign-summary backfill script; create-story synthesises inline via the
 * same helper.
 */

interface OverviewBody {
  summaries: SessionSummary[];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as OverviewBody;
  if (!Array.isArray(body?.summaries) || body.summaries.length === 0) {
    res.status(400).json({ error: 'summaries[] is required' });
    return;
  }

  try {
    const overview = await synthesizeOverview(body.summaries);
    res.status(200).json({ overview });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
