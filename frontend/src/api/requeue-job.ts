import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Put a stalled job back on the queue.
 *
 * POST `{ id }` -> Drupal `requeueAiJob` -> `{ job }`. For a job whose worker
 * went away mid-run: the claim is cleared so the processor runs it again. Drupal
 * cron does this automatically once a lease expires; this is the operator's
 * manual trigger from the activity drawer, and it does not count against the
 * automatic retry budget.
 */

interface RequeueBody {
  /** The job id to requeue. */
  id: string;
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
  data?:   { requeueAiJob: AiJob | null };
  errors?: Array<{ message: string }>;
}

const REQUEUE_MUTATION = `
  mutation RequeueAiJob($id: String!) {
    requeueAiJob(id: $id) {
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

  const body = req.body as RequeueBody;
  if (!body?.id?.trim()) {
    res.status(400).json({ error: 'id is required' });
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
        query:     REQUEUE_MUTATION,
        variables: { id: body.id.trim() },
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

  const job = payload.data?.requeueAiJob ?? null;
  if (!job) {
    res.status(502).json({ error: 'The queue returned no job' });
    return;
  }

  res.status(200).json({ job });
}
