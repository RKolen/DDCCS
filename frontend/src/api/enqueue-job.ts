import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Queue a heavy AI job and return its id immediately.
 *
 * POST `{ type, payload, label }` -> Drupal `enqueueAiJob` -> `{ job }`. Nothing
 * runs during this call: the work is picked up by the single queue processor on
 * the host, so the console can start several jobs and navigate away. Poll
 * `job-status.ts` with the returned id to follow one.
 */

interface EnqueueBody {
  /** Job type plugin id: dnd_portrait, dnd_arc_analysis, dnd_story_generation, dnd_session_summary. */
  type:    string;
  /** Job-type-specific payload; sent to Drupal JSON-encoded. */
  payload: Record<string, unknown>;
  /** Display name for the activity bar. */
  label:   string;
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
  data?:   { enqueueAiJob: AiJob | null };
  errors?: Array<{ message: string }>;
}

const ENQUEUE_MUTATION = `
  mutation EnqueueAiJob($type: String!, $payload: String!, $label: String!) {
    enqueueAiJob(type: $type, payload: $payload, label: $label) {
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

  const body = req.body as EnqueueBody;
  if (!body?.type?.trim() || !body?.label?.trim()) {
    res.status(400).json({ error: 'type and label are required' });
    return;
  }
  if (!body.payload || typeof body.payload !== 'object') {
    res.status(400).json({ error: 'payload is required' });
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
        query:     ENQUEUE_MUTATION,
        variables: {
          type:    body.type.trim(),
          payload: JSON.stringify(body.payload),
          label:   body.label.trim(),
        },
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

  const job = payload.data?.enqueueAiJob ?? null;
  if (!job) {
    res.status(502).json({ error: 'The queue returned no job' });
    return;
  }

  res.status(200).json({ job });
}
