import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { htmlToText } from '../utils/aiSummary';

/**
 * Fetch a story and return it split into small analysis chunks.
 *
 * POST `{ storyId }` -> `{ chunks: string[], title, storyNumber }`. The console
 * then analyses each chunk as its own short request (`arc-analyze-story.ts`),
 * showing per-chunk progress and keeping every model call bounded — a large
 * story no longer sits in one multi-minute request that looks frozen.
 */

const CHUNK_CHARS = 4000;
const MAX_CHUNKS = 40;

interface StoryChunksBody {
  storyId: string;
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

/** Split plain text into fixed-size chunks (capped), for per-chunk analysis. */
function chunkText(text: string): string[] {
  const trimmed = text.trim();
  if (!trimmed) {
    return [];
  }
  const chunks: string[] = [];
  for (let i = 0; i < trimmed.length && chunks.length < MAX_CHUNKS; i += CHUNK_CHARS) {
    chunks.push(trimmed.slice(i, i + CHUNK_CHARS));
  }
  return chunks;
}

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

  const body = req.body as StoryChunksBody;
  if (!body?.storyId) {
    res.status(400).json({ error: 'storyId is required' });
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

  res.status(200).json({
    chunks:      chunkText(htmlToText(story.body?.processed ?? '')),
    title:       story.title,
    storyNumber: story.storyNumber,
  });
}
