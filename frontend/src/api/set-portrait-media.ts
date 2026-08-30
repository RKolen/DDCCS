import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Point a character's portrait (field_image) at an existing image media.
 *
 * Used by the media picker to select a previously generated or library image as
 * the active portrait, without creating new media. Calls the Drupal
 * `setCharacterImage` mutation and returns the resulting image URL.
 */

interface SetPortraitMediaBody {
  id:      string;
  mediaId: string;
}

interface MediaImageResult {
  mediaImage: { url: string; alt: string } | null;
}

interface SetImageResult {
  id:    string;
  title: string;
  image: MediaImageResult | null;
}

interface GraphQlResponse {
  data?:   { setCharacterImage: SetImageResult | null };
  errors?: Array<{ message: string }>;
}

// Unprefixed types: this hits Drupal's raw schema, not the Gatsby-stitched one.
const SET_IMAGE_MUTATION = `
  mutation SetCharacterImage($id: ID!, $mediaId: ID!) {
    setCharacterImage(id: $id, mediaId: $mediaId) {
      id
      title
      image {
        ... on MediaImage {
          mediaImage { url alt }
        }
      }
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

  const body = req.body as SetPortraitMediaBody;
  if (!body?.id?.trim() || !body?.mediaId?.trim()) {
    res.status(400).json({ error: 'id and mediaId are required' });
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
        query:     SET_IMAGE_MUTATION,
        variables: { id: body.id, mediaId: body.mediaId },
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

  const character = payload.data?.setCharacterImage ?? null;
  if (!character) {
    res.status(500).json({ error: 'Set-portrait mutation returned no data' });
    return;
  }

  res.status(200).json({
    id:       character.id,
    title:    character.title,
    imageUrl: character.image?.mediaImage?.url ?? null,
  });
}
