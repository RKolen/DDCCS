import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Accept or discard a finished job's pending result.
 *
 * POST `{ id, accepted }` -> Drupal `resolveAiJob` -> `{ job }`. A job that
 * generates content stores it without applying it, so this is the call that
 * makes a queued portrait render the character's actual portrait. Discarding
 * changes nothing on the character; the render stays in the media library and
 * can still be picked later.
 *
 * The boolean is translated to the mutation's `decision` string here: Drupal
 * resolved a GraphQL `Boolean!` argument twice per request, once as false, which
 * discarded renders that had been accepted. Repeating the same decision is a
 * successful no-op, so a retry is safe.
 */

interface ResolveBody {
  /** The job id whose result is being reviewed. */
  id: string;
  /** True to apply the result, false to leave the content untouched. */
  accepted: boolean;
}

interface AiJob {
  id:        string;
  type:      string;
  state:     string;
  label:     string;
  message:   string | null;
  result:    string | null;
  subjectId: string | null;
  stalled:   boolean | null;
  created:   number | null;
  processed: number | null;
}

interface GraphQlResponse {
  data?:   { resolveAiJob: AiJob | null };
  errors?: Array<{ message: string }>;
}

const RESOLVE_MUTATION = `
  mutation ResolveAiJob($id: String!, $decision: String!) {
    resolveAiJob(id: $id, decision: $decision) {
      id type state label message result subjectId stalled created processed
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

  const body = req.body as ResolveBody;
  if (!body?.id?.trim()) {
    res.status(400).json({ error: 'id is required' });
    return;
  }
  if (typeof body.accepted !== 'boolean') {
    res.status(400).json({ error: 'accepted must be true or false' });
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
        query:     RESOLVE_MUTATION,
        variables: {
          id:       body.id.trim(),
          decision: body.accepted ? 'accept' : 'discard',
        },
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${message}` });
    return;
  }

  let payload: GraphQlResponse;
  try {
    payload = (await drupalRes.json()) as GraphQlResponse;
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Unreadable response from Drupal: ${detail}` });
    return;
  }
  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  const job = payload.data?.resolveAiJob ?? null;
  if (!job) {
    res.status(502).json({ error: 'The queue returned no job' });
    return;
  }

  res.status(200).json({ job });
}
