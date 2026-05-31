import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * PATCH the optional richness fields on a character node.
 * Portrait/image upload is intentionally excluded — that requires
 * a multipart upload handled separately.
 */

interface UpdateCharacterBody {
  id:                string;
  pronouns?:         string | null;
  background?:       string | null;
  personalityTraits?: string[];
  ideals?:           string[];
  bonds?:            string[];
  flaws?:            string[];
}

interface CharacterResult {
  id:    string;
  title: string;
}

interface GraphQlResponse {
  data?:   { updateCharacter: CharacterResult | null };
  errors?: Array<{ message: string }>;
}

const UPDATE_CHARACTER_MUTATION = `
  mutation UpdateCharacter(
    $id:                ID!
    $pronouns:          String
    $background:        String
    $personalityTraits: [String!]
    $ideals:            [String!]
    $bonds:             [String!]
    $flaws:             [String!]
  ) {
    updateCharacter(
      id:                $id
      pronouns:          $pronouns
      background:        $background
      personalityTraits: $personalityTraits
      ideals:            $ideals
      bonds:             $bonds
      flaws:             $flaws
    ) {
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

  const body = req.body as UpdateCharacterBody;
  if (!body?.id?.trim()) {
    res.status(400).json({ error: 'id is required' });
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
        query:     UPDATE_CHARACTER_MUTATION,
        variables: {
          id:                body.id,
          pronouns:          body.pronouns ?? undefined,
          background:        body.background ?? undefined,
          personalityTraits: body.personalityTraits ?? undefined,
          ideals:            body.ideals ?? undefined,
          bonds:             body.bonds ?? undefined,
          flaws:             body.flaws ?? undefined,
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

  const payload = (await drupalRes.json()) as GraphQlResponse;

  if (payload.errors && payload.errors.length > 0) {
    res.status(400).json({ error: payload.errors[0].message });
    return;
  }

  const character = payload.data?.updateCharacter ?? null;
  if (!character) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  res.status(200).json(character);
}
