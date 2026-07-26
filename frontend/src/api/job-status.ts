import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Read queued AI jobs: one by id, or the recent list for the activity bar.
 *
 * GET `?id=12` -> `{ job }` (the poll target after enqueueing).
 * GET `?states=queued,processing&limit=20` -> `{ jobs }` (activity bar).
 *
 * Job state lives outside any cache tag, so both queries are resolved
 * uncacheably in Drupal; a stale answer here would leave a finished job
 * spinning in the console forever.
 */

interface AiJob {
  id:        string;
  type:      string;
  state:     string;
  label:     string;
  message:   string | null;
  result:    string | null;
  created:   number | null;
  processed: number | null;
}

interface GraphQlResponse {
  data?:   { aiJob?: AiJob | null; aiJobs?: AiJob[] | null };
  errors?: Array<{ message: string }>;
}

const JOB_FIELDS = 'id type state label message result created processed';

const JOB_QUERY = `query AiJob($id: String!) { aiJob(id: $id) { ${JOB_FIELDS} } }`;

const JOBS_QUERY = `
  query AiJobs($states: [String!], $limit: Int) {
    aiJobs(states: $states, limit: $limit) { ${JOB_FIELDS} }
  }
`;

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
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

  const id = typeof req.query.id === 'string' ? req.query.id.trim() : '';
  const statesParam = typeof req.query.states === 'string' ? req.query.states : '';
  const limitParam = typeof req.query.limit === 'string' ? Number.parseInt(req.query.limit, 10) : NaN;

  const single = id !== '';
  const variables = single
    ? { id }
    : {
      states: statesParam
        ? statesParam.split(',').map(s => s.trim()).filter(Boolean)
        : null,
      limit: Number.isFinite(limitParam) ? limitParam : null,
    };

  let drupalRes: Response;
  try {
    drupalRes = await fetch(`${drupalUrl}/graphql`, {
      method:  'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept:         'application/json',
      },
      body: JSON.stringify({ query: single ? JOB_QUERY : JOBS_QUERY, variables }),
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

  if (single) {
    res.status(200).json({ job: payload.data?.aiJob ?? null });
    return;
  }
  res.status(200).json({ jobs: payload.data?.aiJobs ?? [] });
}
