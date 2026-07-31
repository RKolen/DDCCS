import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Clear finished jobs from the activity log.
 *
 * POST `{ states? }` -> Drupal `clearAiJobs` -> `{ cleared, kept }`. The drawer
 * is a live view of Drupal's job table with no copy of its own, so clearing it
 * really does delete rows. Drupal refuses non-terminal states and keeps back any
 * finished job still awaiting a decision, so this cannot discard live work or
 * strand a render nobody has accepted yet.
 */

interface ClearBody {
  /** Terminal states to clear (success, failure). Omit for both. */
  states?: string[];
}

interface ClearResult {
  cleared: number;
  kept:    number;
}

interface GraphQlResponse {
  data?:   { clearAiJobs: ClearResult | null };
  errors?: Array<{ message: string }>;
}

const CLEAR_MUTATION = `
  mutation ClearAiJobs($states: [String!]) {
    clearAiJobs(states: $states) { cleared kept }
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

  const body = (req.body ?? {}) as ClearBody;
  const states = Array.isArray(body.states) && body.states.length > 0
    ? body.states.filter(s => typeof s === 'string' && s.trim() !== '')
    : null;

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
        query:     CLEAR_MUTATION,
        variables: { states },
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${message}` });
    return;
  }

  const payload = (await drupalRes.json()) as GraphQlResponse;
  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  const result = payload.data?.clearAiJobs ?? null;
  if (!result) {
    res.status(502).json({ error: 'The queue returned no result' });
    return;
  }

  res.status(200).json(result);
}
