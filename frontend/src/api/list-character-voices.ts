import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * List character voice settings from Drupal for multi-voice story narration.
 *
 * graphql_compose caps `first` at 100, so this pages through `nodeCharacters`
 * with the cursor — same pattern as `list-portrait-media.ts` and the item
 * pagination in `gatsby-node.ts`.
 */

const PAGE_SIZE = 100;
const MAX_CHARACTERS = 1000;

export interface CharacterVoiceRow {
  title:      string;
  firstName:  string | null;
  nickname:   string | null;
  voiceId:    string | null;
  voicePitch: number | null;
  voiceSpeed: number | null;
}

interface RawCharacter {
  title:       string;
  firstName:   string | null;
  nickname:    string | null;
  voiceIdRef:  { name: string } | null;
  voicePitch:  number | null;
  voiceSpeed:  number | null;
}

interface CharacterPage {
  nodes:    RawCharacter[];
  pageInfo: { hasNextPage: boolean; endCursor: string | null };
}

interface GraphQlResponse {
  data?:   { nodeCharacters: CharacterPage | null };
  errors?: Array<{ message: string }>;
}

// Unprefixed types: hits Drupal's raw schema, not the Gatsby-stitched one.
const LIST_VOICES_QUERY = `
  query ListCharacterVoices($first: Int!, $after: Cursor) {
    nodeCharacters(first: $first, after: $after) {
      nodes {
        title
        firstName
        nickname
        voiceIdRef { ... on TermVoiceId { name } }
        voicePitch
        voiceSpeed
      }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
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

  const characters: CharacterVoiceRow[] = [];
  let after: string | null = null;

  while (characters.length < MAX_CHARACTERS) {
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
          query:     LIST_VOICES_QUERY,
          variables: { first: PAGE_SIZE, after },
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

    const page = payload.data?.nodeCharacters;
    if (!page) break;

    for (const n of page.nodes) {
      characters.push({
        title:      n.title,
        firstName:  n.firstName,
        nickname:   n.nickname,
        voiceId:    n.voiceIdRef?.name ?? null,
        voicePitch: n.voicePitch,
        voiceSpeed: n.voiceSpeed,
      });
    }

    if (!page.pageInfo.hasNextPage || !page.pageInfo.endCursor) break;
    after = page.pageInfo.endCursor;
  }

  res.status(200).json({ characters });
}
