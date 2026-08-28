import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';

/**
 * Create a minimal NPC for a campaign.
 *
 * POST `{ campaignId, name, role?, note? }` -> the NPC's `{ id, title }`.
 *
 * The counterpart to `create-character.ts`, which derives a full player sheet
 * through the sidecar and always creates a PC. An NPC read out of session
 * recaps has a name and a line about who they are; the stories rarely give a
 * stat block, and inventing one would put made-up numbers on record. Drupal
 * returns the existing NPC when the campaign already has that name, so a
 * rerun cannot fill the roster with duplicates.
 */

interface CreateNpcBody {
  campaignId?: string;
  name:        string;
  role?:       string;
  note?:       string;
}

interface NpcResult {
  id:    string;
  title: string;
}

const CREATE_NPC_MUTATION = `
  mutation CreateNpcStub($campaignId: ID, $name: String!, $role: String, $note: String) {
    createNpcStub(campaignId: $campaignId, name: $name, role: $role, note: $note) {
      id
      title
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

  const body = req.body as CreateNpcBody;
  if (!body?.name?.trim()) {
    res.status(400).json({ error: 'name is required' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ createNpcStub: NpcResult | null }>(
      creds,
      CREATE_NPC_MUTATION,
      {
        campaignId: body.campaignId?.trim() || null,
        name:       body.name.trim(),
        role:       body.role?.trim() || null,
        note:       body.note?.trim() || null,
      },
    );
    if (!data.createNpcStub) {
      res.status(502).json({ error: 'Drupal did not return the created NPC.' });
      return;
    }
    res.status(200).json(data.createNpcStub);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
