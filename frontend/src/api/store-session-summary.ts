import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { summarizeSession } from '../utils/aiSummary';

/**
 * Summarise a session and store it on the campaign, for the queued summary job.
 *
 * POST `{ campaignId, storyNumber, storyBody }` -> `{ summary }`. Combines the
 * summarise step (`summarize-session.ts`) with the `setSessionSummary` mutation
 * so a queued job is one call: the worker has nothing to hand back to a browser
 * mid-flight, so the summary is persisted as soon as it exists.
 */

interface StoreSummaryBody {
  campaignId:  string;
  storyNumber: number;
  storyBody:   string;
}

const SET_SUMMARY_MUTATION = `
  mutation SetSessionSummary($campaignId: ID!, $storyNumber: Int!, $summary: String!) {
    setSessionSummary(campaignId: $campaignId, storyNumber: $storyNumber, summary: $summary) {
      id
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

  const body = req.body as StoreSummaryBody;
  if (!body?.storyBody?.trim() || !body?.campaignId?.trim()) {
    res.status(400).json({ error: 'campaignId and storyBody are required' });
    return;
  }
  if (typeof body.storyNumber !== 'number') {
    res.status(400).json({ error: 'storyNumber is required' });
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

  let summary: string;
  try {
    summary = await summarizeSession(body.storyBody);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
    return;
  }

  const drupalRes = await fetch(`${drupalUrl}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({
      query:     SET_SUMMARY_MUTATION,
      variables: {
        campaignId:  body.campaignId,
        storyNumber: body.storyNumber,
        summary,
      },
    }),
  });

  let payload: { errors?: Array<{ message: string }> };
  try {
    payload = (await drupalRes.json()) as { errors?: Array<{ message: string }> };
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Unreadable response from Drupal: ${detail}` });
    return;
  }
  if (!drupalRes.ok || (payload.errors && payload.errors.length > 0)) {
    const message = payload.errors?.[0]?.message ?? `Drupal returned ${drupalRes.status}`;
    res.status(502).json({ error: message });
    return;
  }

  res.status(200).json({ summary });
}
