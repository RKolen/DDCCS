import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import {
  summarizeSession,
  synthesizeOverview,
  htmlToText,
  type SessionSummary,
} from '../utils/aiSummary';

interface CreateStoryBody {
  campaignId:   string;
  title:        string;
  body:         string;
  storyNumber:  number;
  sessionDate?: string;
}

interface StoryResult {
  id:    string;
  title: string;
  path:  string | null;
}

interface GraphQlResponse {
  data?:   { createStory: StoryResult | null };
  errors?: Array<{ message: string }>;
}

interface SetSummaryResponse {
  data?: {
    setSessionSummary: {
      sessionSummaries?: Array<{
        storyNumber: number | null;
        text?:       Array<{ processed: string }> | { processed: string } | null;
      }> | null;
    } | null;
  };
  errors?: Array<{ message: string }>;
}

const SET_SESSION_SUMMARY_MUTATION = `
  mutation SetSessionSummary(
    $campaignId:  ID!
    $storyNumber: Int!
    $summary:     String!
    $overview:    String
  ) {
    setSessionSummary(
      campaignId:  $campaignId
      storyNumber: $storyNumber
      summary:     $summary
      overview:    $overview
    ) {
      sessionSummaries {
        ... on ParagraphSessionSummary {
          storyNumber
          text { processed }
        }
      }
    }
  }
`;

/** Read the first `processed` value regardless of list/single field shape. */
function readProcessed(
  text?: Array<{ processed: string }> | { processed: string } | null,
): string {
  if (Array.isArray(text)) {
    return text[0]?.processed ?? '';
  }
  return text?.processed ?? '';
}

async function setSessionSummary(
  drupalUrl: string,
  token: string,
  vars: { campaignId: string; storyNumber: number; summary: string; overview?: string },
): Promise<SessionSummary[]> {
  const res = await fetch(`${drupalUrl}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({ query: SET_SESSION_SUMMARY_MUTATION, variables: vars }),
  });
  const payload = (await res.json()) as SetSummaryResponse;
  if (payload.errors && payload.errors.length > 0) {
    throw new Error(payload.errors[0].message);
  }
  const rows = payload.data?.setSessionSummary?.sessionSummaries ?? [];
  return rows
    .filter((r): r is { storyNumber: number; text?: typeof r.text } => r.storyNumber !== null)
    .map((r) => ({ storyNumber: r.storyNumber, summary: htmlToText(readProcessed(r.text)) }));
}

/**
 * Summarise the new session and refresh the campaign overview.
 *
 * Best-effort: upserts this session's recap, synthesises the "story so far" from
 * every recap, then stores the overview. Any failure is swallowed so story
 * creation still succeeds. Returns a warning string when summarisation fails.
 */
async function refreshCampaignSummary(
  drupalUrl: string,
  token: string,
  body: CreateStoryBody,
): Promise<string | null> {
  try {
    const summary = await summarizeSession(body.body);
    const allSummaries = await setSessionSummary(drupalUrl, token, {
      campaignId:  body.campaignId,
      storyNumber: body.storyNumber,
      summary,
    });
    const overview = await synthesizeOverview(allSummaries);
    await setSessionSummary(drupalUrl, token, {
      campaignId:  body.campaignId,
      storyNumber: body.storyNumber,
      summary,
      overview,
    });
    return null;
  } catch (err) {
    return err instanceof Error ? err.message : String(err);
  }
}

const CREATE_STORY_MUTATION = `
  mutation CreateStory(
    $campaignId:  ID!
    $title:       String!
    $body:        String!
    $storyNumber: Int!
    $sessionDate: String
  ) {
    createStory(
      campaignId:  $campaignId
      title:       $title
      body:        $body
      storyNumber: $storyNumber
      sessionDate: $sessionDate
    ) {
      id
      title
      path
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

  const body = req.body as CreateStoryBody;
  if (!body?.campaignId || !body?.title || !body?.body) {
    res.status(400).json({ error: 'campaignId, title, and body are required' });
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
        query:     CREATE_STORY_MUTATION,
        variables: {
          campaignId:  body.campaignId,
          title:       body.title,
          body:        body.body,
          storyNumber: body.storyNumber,
          sessionDate: body.sessionDate ?? new Date().toISOString().slice(0, 10),
        },
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

  const payload = (await drupalRes.json()) as GraphQlResponse;

  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  const story = payload.data?.createStory ?? null;
  if (!story) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  // Best-effort: generate this session's recap and refresh the campaign
  // overview. Never let a summarisation failure block story creation.
  const summaryWarning = await refreshCampaignSummary(drupalUrl, token, body);

  res.status(200).json({ ...story, summaryWarning });
}
