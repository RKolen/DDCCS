import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Analyse one chunk of a story into one arc data point (one model call).
 *
 * POST `{ characterName, content, title?, storyNumber?, pronouns? }` -> sidecar
 * `/character/arc/story` (which, for a single small chunk, is a single fast
 * model pass). The console loops this per chunk (`arc-story-chunks.ts` supplies
 * the chunks) so every request is short and per-chunk progress is visible — no
 * more one multi-minute request that looks frozen.
 */

interface ArcChunkBody {
  characterName: string;
  content:       string;
  title?:        string;
  storyNumber?:  number | null;
  pronouns?:     string;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as ArcChunkBody;
  if (!body?.characterName?.trim() || !body?.content?.trim()) {
    res.status(400).json({ error: 'characterName and content are required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Arc analysis sidecar is not configured' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/character/arc/story`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: body.characterName,
        content:        body.content,
        title:          body.title ?? '',
        story_number:   body.storyNumber ?? null,
        pronouns:       body.pronouns ?? '',
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Arc sidecar unreachable: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    const text = await sidecarRes.text();
    res.status(sidecarRes.status).json({ error: text });
    return;
  }

  // The data point is opaque to the browser — pass it straight through to the
  // aggregate step.
  const dataPoint = await sidecarRes.json();
  res.status(200).json({ dataPoint });
}
