import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Synthesize a full character arc from the data points stored on the node.
 *
 * POST `{ campaignId, characterId, characterName, pronouns? }`. Reads each
 * story's persisted structured data point (JSON), runs the sidecar
 * `/character/arc/aggregate` to compute real metric trend lines, direction,
 * relationships, goals, and a summary, then saves the arc onto the character
 * (via `saveCharacterArc`) so the existing sparkline display renders it. Returns
 * the arc (camelCase) so the caller can show it immediately.
 *
 * The data points stay server-side; the browser never holds every story.
 */

interface Body {
  campaignId:    string;
  characterId:   string;
  characterName: string;
  pronouns?:     string;
}

interface AnalysisNode {
  character:     { id: string } | null;
  storyAnalyses: Array<{ storyNumber: number | null; datapoint: string | null }> | null;
}

interface SidecarArc {
  direction:        string;
  stage:            string;
  summary:          string;
  stories_analyzed: number;
  updated_at:       string;
  metrics:          Record<string, unknown>;
  relationships:    unknown[];
  goals:            unknown[];
}

const NODE_QUERY = `
  query {
    nodeCharacterAnalysis(first: 100) {
      nodes {
        character { ... on NodeCharacter { id } }
        storyAnalyses {
          ... on ParagraphSessionSummary { storyNumber datapoint }
        }
      }
    }
  }
`;

const SAVE_ARC_MUTATION = `
  mutation SaveCharacterArc($id: ID!, $payload: String!) {
    saveCharacterArc(id: $id, payload: $payload) { id }
  }
`;

const UPSERT_SUMMARY_MUTATION = `
  mutation UpsertSummary($characterId: ID!, $summary: String) {
    upsertCharacterAnalysis(campaignId: "", characterId: $characterId, summary: $summary) { id }
  }
`;

function drupalConfig(): { url: string; token: string } | null {
  const url = (
    process.env.GATSBY_DRUPAL_BASE_URL ?? process.env.DRUPAL_BASE_URL ?? ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  return url && token ? { url, token } : null;
}

async function drupalGraphql(
  cfg: { url: string; token: string },
  query: string,
  variables?: Record<string, unknown>,
): Promise<unknown> {
  const res = await fetch(`${cfg.url}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${cfg.token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({ query, variables }),
  });
  return res.json();
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const body = req.body as Body;
  if (!body?.characterId || !body?.characterName?.trim()) {
    res.status(400).json({ error: 'characterId and characterName are required' });
    return;
  }

  const cfg = drupalConfig();
  if (!cfg) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }
  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Arc analysis sidecar is not configured' });
    return;
  }

  // Read the stored per-story data points for this character.
  let dataPoints: unknown[];
  try {
    const payload = (await drupalGraphql(cfg, NODE_QUERY)) as {
      data?: { nodeCharacterAnalysis: { nodes: AnalysisNode[] } };
    };
    const node = (payload.data?.nodeCharacterAnalysis.nodes ?? []).find(
      n => n.character?.id === body.characterId,
    );
    dataPoints = (node?.storyAnalyses ?? [])
      .slice()
      .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0))
      .map(s => {
        try {
          return s.datapoint ? JSON.parse(s.datapoint) : null;
        } catch {
          return null;
        }
      })
      .filter((d): d is Record<string, unknown> => d !== null);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to read stored data points: ${message}` });
    return;
  }
  if (dataPoints.length === 0) {
    res.status(409).json({
      error: 'No structured data points stored — re-run the analysis to capture metrics.',
    });
    return;
  }

  // Aggregate the data points into a full arc (metric trends + direction + more).
  let arc: SidecarArc;
  try {
    const sidecarRes = await sidecarFetch(`${sidecarUrl}/character/arc/aggregate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: body.characterName,
        campaign_name:  '',
        pronouns:       body.pronouns ?? '',
        data_points:    dataPoints,
      }),
    });
    if (!sidecarRes.ok) {
      const text = await sidecarRes.text();
      res.status(sidecarRes.status).json({ error: text });
      return;
    }
    arc = (await sidecarRes.json()) as SidecarArc;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Arc sidecar unreachable: ${message}` });
    return;
  }

  // Save the arc onto the character (display store) + mirror the summary onto
  // the analysis node. Best effort: the arc is still returned if a write fails.
  const arcPayload = JSON.stringify({
    direction:        arc.direction,
    stage:            arc.stage,
    summary:          arc.summary,
    stories_analyzed: arc.stories_analyzed,
    updated_at:       arc.updated_at,
    metrics:          arc.metrics,
    relationships:    arc.relationships,
    goals:            arc.goals,
  });
  try {
    await drupalGraphql(cfg, SAVE_ARC_MUTATION, { id: body.characterId, payload: arcPayload });
    await drupalGraphql(cfg, UPSERT_SUMMARY_MUTATION, {
      characterId: body.characterId,
      summary:     arc.summary,
    });
  } catch {
    // Persistence is best effort; the caller still gets the arc to display.
  }

  res.status(200).json({
    direction:       arc.direction,
    stage:           arc.stage,
    summary:         arc.summary,
    storiesAnalyzed: arc.stories_analyzed,
    lastAnalyzed:    arc.updated_at,
    metrics:         arc.metrics,
    relationships:   arc.relationships,
    goals:           arc.goals,
  });
}
