import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';

/**
 * Read one story's body, for the console's reader.
 *
 * POST `{ storyId }` -> `{ title, storyNumber, body }` as Drupal's processed
 * HTML. No AI.
 *
 * Fetched on demand rather than carried in the console's page data: a campaign
 * runs to hundreds of thousands of characters of story text, and baking that
 * into every console load to show one story at a time is not a trade worth
 * making.
 */

interface StoryBodyBody {
  storyId: string;
}

interface StoryNode {
  title:       string;
  storyNumber: number | null;
  body:        { processed: string } | null;
}

const STORY_QUERY = `
  query StoryBody($id: ID!) {
    node(id: $id) {
      ... on NodeStory { title storyNumber body { processed } }
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

  const body = req.body as StoryBodyBody;
  if (!body?.storyId?.trim()) {
    res.status(400).json({ error: 'storyId is required' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ node: StoryNode | null }>(
      creds, STORY_QUERY, { id: body.storyId.trim() },
    );
    if (!data.node) {
      res.status(404).json({ error: 'Story not found' });
      return;
    }
    res.status(200).json({
      title:       data.node.title,
      storyNumber: data.node.storyNumber,
      body:        data.node.body?.processed ?? '',
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
