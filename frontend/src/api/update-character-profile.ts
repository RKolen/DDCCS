import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Write a character's editable profile fields.
 *
 * The browser posts `{ id, fields }`, where `fields` holds only what the
 * operator changed; it is forwarded verbatim as the mutation's JSON payload and
 * Drupal writes just those keys. Anything the mutation does not recognise is
 * ignored there, so this function does not need its own field whitelist.
 *
 * Portrait, voice, and arc analysis are not writable here — they belong to
 * /api/set-portrait-media, /api/update-voice, and /api/save-arc respectively.
 */

interface UpdateProfileBody {
  id:     string;
  fields: Record<string, unknown>;
}

interface CharacterResult {
  id:    string;
  title: string;
}

interface GraphQlResponse {
  data?:   { updateCharacterProfile: CharacterResult | null };
  errors?: Array<{ message: string }>;
}

const UPDATE_CHARACTER_PROFILE_MUTATION = `
  mutation UpdateCharacterProfile($id: ID!, $payload: String!) {
    updateCharacterProfile(id: $id, payload: $payload) {
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

  const body = req.body as UpdateProfileBody;
  if (!body?.id?.trim()) {
    res.status(400).json({ error: 'id is required' });
    return;
  }
  if (body.fields == null || typeof body.fields !== 'object' || Array.isArray(body.fields)) {
    res.status(400).json({ error: 'fields must be an object' });
    return;
  }
  if (Object.keys(body.fields).length === 0) {
    res.status(400).json({ error: 'No fields to update' });
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
        query:     UPDATE_CHARACTER_PROFILE_MUTATION,
        variables: {
          id:      body.id,
          payload: JSON.stringify(body.fields),
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

  let payload: GraphQlResponse;
  try {
    payload = (await drupalRes.json()) as GraphQlResponse;
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Unreadable response from Drupal: ${detail}` });
    return;
  }

  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  const character = payload.data?.updateCharacterProfile ?? null;
  if (!character) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  res.status(200).json(character);
}
