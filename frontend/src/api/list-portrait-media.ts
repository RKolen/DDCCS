import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * List image media from the Drupal media library for the portrait picker.
 *
 * Returns every published image media (id, name, url, alt) so the console can
 * offer a "choose an existing image" gallery - e.g. a previously generated
 * portrait - alongside fresh ComfyUI generation. Read-only; the caller sets the
 * chosen one as a character's portrait via `set-portrait-media.ts`.
 *
 * The graphql_compose connection caps `first` at 100, so this pages through in
 * chunks with the cursor, up to MAX_MEDIA overall (a picker never needs more).
 */

const PAGE_SIZE = 100;
const MAX_MEDIA = 1000;

interface RawMediaImage {
  id:         string;
  name:       string;
  mediaType:  string | null;
  mediaImage: { url: string; alt: string } | null;
}

interface MediaPage {
  nodes:    RawMediaImage[];
  pageInfo: { hasNextPage: boolean; endCursor: string | null };
}

interface GraphQlResponse {
  data?:   { mediaImages: MediaPage | null };
  errors?: Array<{ message: string }>;
}

interface MediaOption { id: string; name: string; url: string; alt: string }

// Unprefixed types: this hits Drupal's raw schema, not the Gatsby-stitched one.
const LIST_MEDIA_QUERY = `
  query ListPortraitMedia($first: Int!, $after: Cursor) {
    mediaImages(first: $first, after: $after) {
      nodes {
        id
        name
        mediaType
        mediaImage { url alt }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
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

  // Optional ?type=character_portrait filter: the browser then only receives
  // and renders the relevant subset, keeping the picker list and its thumbnail
  // downloads small.
  const wantType = typeof req.query?.type === 'string' && req.query.type.trim() !== ''
    ? req.query.type.trim()
    : null;

  const media: MediaOption[] = [];
  let after: string | null = null;

  while (media.length < MAX_MEDIA) {
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
          query:     LIST_MEDIA_QUERY,
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

    const page = payload.data?.mediaImages;
    if (!page) break;

    for (const n of page.nodes) {
      if (!n.mediaImage?.url) continue;
      if (wantType !== null && n.mediaType !== wantType) continue;
      media.push({ id: n.id, name: n.name, url: n.mediaImage.url, alt: n.mediaImage.alt ?? '' });
    }

    if (!page.pageInfo.hasNextPage || !page.pageInfo.endCursor) break;
    after = page.pageInfo.endCursor;
  }

  res.status(200).json({ media });
}
