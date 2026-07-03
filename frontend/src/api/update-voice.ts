import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Update a character's voice settings (voice id, pitch, speed) via the Drupal
 * updateCharacter mutation. Used by the consultation screen's voice mini-wizard.
 */

interface UpdateVoiceBody {
  id:          string;
  voiceId?:    string | null;
  voicePitch?: number | null;
  voiceSpeed?: number | null;
}

interface GraphQlResponse {
  data?:   { updateCharacter: { id: string; title: string } | null };
  errors?: Array<{ message: string }>;
}

const MUTATION = `
  mutation UpdateVoice($id: ID!, $voiceId: String, $voicePitch: Float, $voiceSpeed: Float) {
    updateCharacter(id: $id, voiceId: $voiceId, voicePitch: $voicePitch, voiceSpeed: $voiceSpeed) {
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

  const body = req.body as UpdateVoiceBody;
  if (!body?.id) {
    res.status(400).json({ error: 'id is required' });
    return;
  }

  const url = (process.env.GATSBY_DRUPAL_BASE_URL ?? process.env.DRUPAL_BASE_URL ?? '').replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  if (!url || !token) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  let payload: GraphQlResponse;
  try {
    const drupalRes = await fetch(`${url}/graphql`, {
      method:  'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept:         'application/json',
      },
      body: JSON.stringify({
        query: MUTATION,
        variables: {
          id:         body.id,
          voiceId:    body.voiceId ?? null,
          voicePitch: body.voicePitch ?? null,
          voiceSpeed: body.voiceSpeed ?? null,
        },
      }),
    });
    payload = (await drupalRes.json()) as GraphQlResponse;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${msg}` });
    return;
  }

  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  res.status(200).json({ id: payload.data?.updateCharacter?.id ?? body.id });
}
