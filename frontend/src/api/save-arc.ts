import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Persist an accepted character arc analysis to Drupal.
 *
 * POST `{ id, arc }` where `arc` is the camelCase result from `arc-analyze.ts`.
 * Maps it to the snake_case payload the `saveCharacterArc` mutation expects and
 * writes it onto the character node.
 */

interface ArcMetric {
  label:     string;
  series:    number[];
  direction: string;
  obs:       string;
}

interface ArcRelationship {
  target:   string;
  type:     string;
  strength: number;
  trust:    number;
  note:     string;
}

interface ArcGoal {
  description: string;
  status:      string;
  progress:    number;
}

interface ArcData {
  direction:       string;
  stage:           string;
  summary:         string;
  storiesAnalyzed: number;
  lastAnalyzed:    string;
  metrics:         Record<string, ArcMetric>;
  relationships:   ArcRelationship[];
  goals:           ArcGoal[];
}

interface SaveArcBody {
  id:  string;
  arc: ArcData;
}

interface GraphQlResponse {
  data?:   { saveCharacterArc: { id: string; title: string } | null };
  errors?: Array<{ message: string }>;
}

const SAVE_ARC_MUTATION = `
  mutation SaveCharacterArc($id: ID!, $payload: String!) {
    saveCharacterArc(id: $id, payload: $payload) {
      id
      title
    }
  }
`;

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as SaveArcBody;
  if (!body?.id || !body?.arc) {
    res.status(400).json({ error: 'id and arc are required' });
    return;
  }

  const drupalUrl = (
    process.env.GATSBY_DRUPAL_BASE_URL ??
    process.env.DRUPAL_BASE_URL ??
    ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  if (!drupalUrl || !token) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  const { arc } = body;
  const payload = JSON.stringify({
    direction:        arc.direction,
    stage:            arc.stage,
    summary:          arc.summary,
    stories_analyzed: arc.storiesAnalyzed,
    updated_at:       arc.lastAnalyzed,
    metrics:          arc.metrics,
    relationships:    arc.relationships,
    goals:            arc.goals,
  });

  let drupalRes: Response;
  try {
    drupalRes = await fetch(`${drupalUrl}/graphql`, {
      method:  'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept:         'application/json',
      },
      body: JSON.stringify({
        query:     SAVE_ARC_MUTATION,
        variables: { id: body.id, payload },
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${message}` });
    return;
  }

  if (!drupalRes.ok) {
    const text = await drupalRes.text();
    res.status(drupalRes.status).json({ error: text });
    return;
  }

  let result: GraphQlResponse;
  try {
    result = (await drupalRes.json()) as GraphQlResponse;
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Unreadable response from Drupal: ${detail}` });
    return;
  }
  if (result.errors && result.errors.length > 0) {
    res.status(400).json({ error: result.errors[0].message });
    return;
  }

  const saved = result.data?.saveCharacterArc ?? null;
  if (!saved) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  res.status(200).json(saved);
}
