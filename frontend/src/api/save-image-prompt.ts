import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Save a character's reusable image-generation prompt (field_image_prompt).
 *
 * POST `{ id, prompt }` -> Drupal `updateCharacter(imagePrompt:)`. Stores the
 * edited prompt so several renders can share it without rebuilding.
 */

interface SavePromptBody {
  id:     string;
  prompt: string;
}

interface GraphQlResponse {
  data?:   { updateCharacter: { id: string; imagePrompt: string | null } | null };
  errors?: Array<{ message: string }>;
}

const SAVE_PROMPT_MUTATION = `
  mutation SaveImagePrompt($id: ID!, $imagePrompt: String!) {
    updateCharacter(id: $id, imagePrompt: $imagePrompt) {
      id
      imagePrompt
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

  const body = req.body as SavePromptBody;
  if (!body?.id?.trim() || typeof body.prompt !== 'string') {
    res.status(400).json({ error: 'id and prompt are required' });
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
        query:     SAVE_PROMPT_MUTATION,
        variables: { id: body.id, imagePrompt: body.prompt },
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

  const character = payload.data?.updateCharacter ?? null;
  if (!character) {
    res.status(500).json({ error: 'Save-prompt mutation returned no data' });
    return;
  }

  res.status(200).json({ id: character.id, imagePrompt: character.imagePrompt });
}
