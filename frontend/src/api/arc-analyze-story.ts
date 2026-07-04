import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { htmlToText } from '../utils/aiSummary';

/**
 * Per-story arc analysis (one model call).
 *
 * POST `{ characterName, storyId }`. Fetches that one story's body from Drupal
 * and sends it to the sidecar `/character/arc/story`, returning the story's arc
 * data point. The console loops this once per story (showing progress), then
 * posts the collected points to `arc-aggregate.ts`. Keeping each call to a
 * single story avoids the multi-minute request that trips the fetch timeout.
 */

interface ArcStoryBody {
  characterName: string;
  storyId:       string;
  pronouns?:     string;
}

interface StoryNode {
  title:       string;
  storyNumber: number | null;
  body:        { processed: string } | null;
}

const STORY_QUERY = `
  query ($id: ID!) {
    node(id: $id) {
      ... on NodeStory { title storyNumber body { processed } }
    }
  }
`;

async function fetchStory(storyId: string): Promise<StoryNode | null> {
  const drupalUrl = (
    process.env.GATSBY_DRUPAL_BASE_URL ??
    process.env.DRUPAL_BASE_URL ??
    ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  if (!drupalUrl || !token) {
    throw new Error('Drupal credentials not configured');
  }
  const res = await fetch(`${drupalUrl}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({ query: STORY_QUERY, variables: { id: storyId } }),
  });
  const payload = (await res.json()) as {
    data?:   { node: StoryNode | null };
    errors?: Array<{ message: string }>;
  };
  if (payload.errors && payload.errors.length > 0) {
    throw new Error(payload.errors[0].message);
  }
  return payload.data?.node ?? null;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as ArcStoryBody;
  if (!body?.characterName?.trim() || !body?.storyId) {
    res.status(400).json({ error: 'characterName and storyId are required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Arc analysis sidecar is not configured' });
    return;
  }

  let story: StoryNode | null;
  try {
    story = await fetchStory(body.storyId);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to load story: ${message}` });
    return;
  }
  if (!story) {
    res.status(404).json({ error: 'Story not found' });
    return;
  }

  let sidecarRes: Response;
  try {
    sidecarRes = await fetch(`${sidecarUrl}/character/arc/story`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: body.characterName,
        content:        htmlToText(story.body?.processed ?? ''),
        title:          story.title,
        story_number:   story.storyNumber,
        pronouns:       body.pronouns ?? '',
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

  // The data point is opaque to the browser — pass it straight through to the
  // aggregate step.
  const dataPoint = await sidecarRes.json();
  res.status(200).json({ dataPoint });
}
