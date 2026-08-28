import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';
import type { ArcFieldPayload } from '../utils/arcPayload';

/**
 * Write a partial patch onto an existing story arc.
 *
 * POST `{ id, fields }` -> the updated arc's `{ id, title, path }`.
 *
 * Only the keys present in `fields` are written, so the wizard saves one step
 * at a time and the arc overview screen can edit a single field without
 * round-tripping the whole arc. Relations go through `save-arc-relations.ts`.
 */

interface UpdateStoryArcBody {
  id:     string;
  fields: ArcFieldPayload;
}

interface ArcResult {
  id:    string;
  title: string;
  path:  string | null;
}

const UPDATE_STORY_ARC_MUTATION = `
  mutation UpdateStoryArc($id: ID!, $payload: String!) {
    updateStoryArc(id: $id, payload: $payload) {
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

  const body = req.body as UpdateStoryArcBody;
  if (!body?.id || !body?.fields || typeof body.fields !== 'object') {
    res.status(400).json({ error: 'id and fields are required' });
    return;
  }
  if (Object.keys(body.fields).length === 0) {
    res.status(400).json({ error: 'fields must contain at least one key' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ updateStoryArc: ArcResult | null }>(
      creds,
      UPDATE_STORY_ARC_MUTATION,
      { id: body.id, payload: JSON.stringify(body.fields) },
    );
    if (!data.updateStoryArc) {
      res.status(502).json({ error: 'Drupal did not return the updated arc.' });
      return;
    }
    res.status(200).json(data.updateStoryArc);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
