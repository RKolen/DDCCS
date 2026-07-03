import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { summarizeSession } from '../utils/aiSummary';

/**
 * Summarise a single session (story body) into a concise recap.
 *
 * POST `{ storyBody }` -> `{ summary }`. Used by the campaign-summary backfill
 * script; create-story summarises inline via the same helper.
 */

interface SummarizeBody {
  storyBody: string;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as SummarizeBody;
  if (!body?.storyBody?.trim()) {
    res.status(400).json({ error: 'storyBody is required' });
    return;
  }

  try {
    const summary = await summarizeSession(body.storyBody);
    res.status(200).json({ summary });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
