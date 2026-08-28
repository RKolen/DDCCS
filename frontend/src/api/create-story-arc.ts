import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';
import type { ArcFieldPayload } from '../utils/arcPayload';

/**
 * Create a story arc for a campaign.
 *
 * POST `{ campaignId, title, fields? }` -> the created arc's `{ id, title, path }`.
 *
 * Only the campaign and title are required. The wizard calls this at the end
 * of its first step and patches the arc as the user advances
 * (`update-story-arc.ts`), so a refresh mid-wizard loses at most one step
 * rather than the whole arc.
 */

interface CreateStoryArcBody {
  campaignId: string;
  title:      string;
  fields?:    ArcFieldPayload;
}

interface ArcResult {
  id:    string;
  title: string;
  path:  string | null;
}

const CREATE_STORY_ARC_MUTATION = `
  mutation CreateStoryArc($campaignId: ID!, $title: String!, $payload: String) {
    createStoryArc(campaignId: $campaignId, title: $title, payload: $payload) {
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

  const body = req.body as CreateStoryArcBody;
  if (!body?.campaignId || !body?.title?.trim()) {
    res.status(400).json({ error: 'campaignId and title are required' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ createStoryArc: ArcResult | null }>(
      creds,
      CREATE_STORY_ARC_MUTATION,
      {
        campaignId: body.campaignId,
        title:      body.title.trim(),
        payload:    body.fields ? JSON.stringify(body.fields) : null,
      },
    );
    if (!data.createStoryArc) {
      res.status(502).json({ error: 'Drupal did not return the created arc.' });
      return;
    }
    res.status(200).json(data.createStoryArc);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
