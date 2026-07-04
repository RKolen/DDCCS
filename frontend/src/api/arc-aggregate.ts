import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Aggregate per-story arc data points into the full character arc.
 *
 * POST `{ characterName, campaignName, dataPoints }` (the opaque points from
 * `arc-analyze-story.ts`) -> sidecar `/character/arc/aggregate`. Maps the
 * snake_case result to the camelCase arc shape the console consumes; the Accept
 * action then persists it via `save-arc.ts`.
 */

interface ArcAggregateBody {
  characterName: string;
  campaignName?: string;
  pronouns?:     string;
  dataPoints:    unknown[];
}

interface SidecarArcResponse {
  direction:        string;
  stage:            string;
  summary:          string;
  stories_analyzed: number;
  updated_at:       string;
  metrics:          Record<string, unknown>;
  relationships:    unknown[];
  goals:            unknown[];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as ArcAggregateBody;
  if (!body?.characterName?.trim()) {
    res.status(400).json({ error: 'characterName is required' });
    return;
  }
  if (!Array.isArray(body.dataPoints) || body.dataPoints.length === 0) {
    res.status(400).json({ error: 'dataPoints is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Arc analysis sidecar is not configured' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/character/arc/aggregate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: body.characterName,
        campaign_name:  body.campaignName ?? '',
        pronouns:       body.pronouns ?? '',
        data_points:    body.dataPoints,
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

  const data = (await sidecarRes.json()) as SidecarArcResponse;
  res.status(200).json({
    direction:       data.direction,
    stage:           data.stage,
    summary:         data.summary,
    storiesAnalyzed: data.stories_analyzed,
    lastAnalyzed:    data.updated_at,
    metrics:         data.metrics,
    relationships:   data.relationships,
    goals:           data.goals,
  });
}
