import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Draw the staging as a skeleton, before any render is paid for.
 *
 * POST `{ people, placements, shot }` -> sidecar `/story/stage` -> the
 * openpose canvas plus each placement with the box it produced. A scene costs
 * minutes and a ComfyUI restart; the staging that decides who stands where,
 * how far back and which way they face costs nothing to look at first.
 */

interface StagePlacement {
  name:     string;
  lateral:  number;
  depth:    number;
  pose:     string;
  facing:   string;
  toward?:  string;
  limbs?:   Array<{ joint: string; x: number; y: number }>;
  box?:     number[];
}

interface StageBody {
  people?:     Array<Record<string, unknown>>;
  placements?: StagePlacement[];
  shot?:       string;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = (req.body ?? {}) as StageBody;
  if (!Array.isArray(body.people) || body.people.length === 0) {
    res.status(400).json({ error: 'No one is in the shot' });
    return;
  }

  const base = sidecarBaseUrl();
  if (!base) {
    res.status(500).json({ error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let sidecarRes: Response;
  try {
    sidecarRes = await fetch(`${base}/story/stage`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        people:     body.people,
        placements: body.placements ?? [],
        shot:       body.shot ?? 'full',
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the story sidecar: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    res.status(sidecarRes.status).json({ error: await sidecarRes.text() });
    return;
  }

  res.status(200).json(await sidecarRes.json());
}
