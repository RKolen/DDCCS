import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';
import { summarizeSession } from '../utils/aiSummary';

/**
 * Summarise one stored story and persist the recap on its campaign.
 *
 * POST `{ campaignId, storyId }` -> `{ storyNumber, summary }`.
 *
 * `store-session-summary.ts` takes the body from the caller, which suits the
 * story that was just written. Backfilling an old campaign has only the story
 * id, so this fetches the body first. Persisting as it goes is what makes a
 * backfill resumable: a run that dies halfway leaves the recaps it earned.
 */

interface SummarizeStoryBody {
  campaignId: string;
  storyId:    string;
}

interface StoryNode {
  title:       string;
  storyNumber: number | null;
  body:        { processed: string } | null;
}

const STORY_QUERY = `
  query BackfillStory($id: ID!) {
    node(id: $id) {
      ... on NodeStory { title storyNumber body { processed } }
    }
  }
`;

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

  const body = req.body as SummarizeStoryBody;
  if (!body?.campaignId?.trim() || !body?.storyId?.trim()) {
    res.status(400).json({ error: 'campaignId and storyId are required' });
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
    const story = data.node;
    if (!story || story.storyNumber === null) {
      res.status(404).json({ error: 'Story not found, or it has no story number' });
      return;
    }
    const storyBody = story.body?.processed ?? '';
    if (!storyBody.trim()) {
      res.status(422).json({ error: `"${story.title}" has no body to summarise` });
      return;
    }

    const summary = await summarizeSession(storyBody);
    if (!summary.trim()) {
      res.status(502).json({ error: `The model returned no recap for "${story.title}"` });
      return;
    }

    await runDrupalMutation(creds, SET_SUMMARY_MUTATION, {
      campaignId:  body.campaignId.trim(),
      storyNumber: story.storyNumber,
      summary,
    });

    res.status(200).json({ storyNumber: story.storyNumber, summary });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
