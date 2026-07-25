import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Generate a character portrait and attach it to the character node.
 *
 * Flow (Phase A, text-to-image only):
 *   1. POST the character profile to the Python sidecar `/character/portrait`,
 *      which drives local ComfyUI and returns a base64 PNG. CPU generation
 *      takes minutes, so `sidecarFetch` (no request timeout) is used.
 *   2. Persist the image via the Drupal `setCharacterPortrait` mutation, which
 *      creates a file + image media entity and points `field_image` at it.
 *   3. Return the persisted image URL so the console can show it immediately.
 *
 * The prompt is built from `profile` (species/lineage/character_class/pronouns/
 * background/personality_traits + optional appearance/arc_summary/backstory).
 * The console assembles that mapping from the character it already holds, so no
 * extra Drupal read is needed here.
 */

interface GeneratePortraitBody {
  /** UUID of the character node to attach the portrait to. */
  id:       string;
  /** Character fields the sidecar prompt builder understands. */
  profile:  Record<string, unknown>;
  /** Omit for a random seed; pass to reproduce a previous render. */
  seed?:    number | null;
  /** SD 1.5-class checkpoints need smaller dimensions than the SDXL defaults. */
  width?:   number | null;
  height?:  number | null;
  /** Explicit (edited/stored) prompt; when set it drives generation directly. */
  positive?: string | null;
}

/** Shape of the sidecar `/character/portrait` response (PortraitResponse). */
interface SidecarPortrait {
  image_base64: string;
  seed:         number;
  prompt:       string;
  alt:          string;
}

interface MediaImageResult {
  mediaImage: { url: string; alt: string } | null;
}

interface SetPortraitResult {
  id:     string;
  title:  string;
  image:  MediaImageResult | null;
}

interface GraphQlResponse {
  data?:   { setCharacterPortrait: SetPortraitResult | null };
  errors?: Array<{ message: string }>;
}

// `image` is a MediaUnion; MediaImage carries the flattened url/alt. Types are
// unprefixed here because this hits Drupal's raw schema, not the Gatsby-stitched
// one (which prefixes with Drupal_).
const SET_PORTRAIT_MUTATION = `
  mutation SetCharacterPortrait($id: ID!, $imageBase64: String!, $alt: String!) {
    setCharacterPortrait(id: $id, imageBase64: $imageBase64, alt: $alt) {
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

  const body = req.body as GeneratePortraitBody;
  if (!body?.id?.trim()) {
    res.status(400).json({ error: 'id is required' });
    return;
  }
  if (!body?.profile || Object.keys(body.profile).length === 0) {
    res.status(400).json({ error: 'profile is required' });
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

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Portrait sidecar is not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  // 1. Generate the portrait via the sidecar (long-running; no timeout).
  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/character/portrait`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profile:  body.profile,
        seed:     body.seed ?? null,
        width:    body.width ?? null,
        height:   body.height ?? null,
        positive: body.positive ?? null,
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Portrait sidecar unreachable: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    // Forward the sidecar's status (503 when ComfyUI is disabled/unreachable,
    // 500 when generation fails) so the console can show a precise message.
    const text = await sidecarRes.text();
    res.status(sidecarRes.status).json({ error: text });
    return;
  }

  const portrait = (await sidecarRes.json()) as SidecarPortrait;
  if (!portrait?.image_base64) {
    res.status(502).json({ error: 'Portrait generation returned no image' });
    return;
  }

  // 2. Persist the image on the character node.
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
        query:     SET_PORTRAIT_MUTATION,
        variables: {
          id:          body.id,
          imageBase64: portrait.image_base64,
          alt:         portrait.alt,
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

  const character = payload.data?.setCharacterPortrait ?? null;
  if (!character) {
    res.status(500).json({ error: 'Portrait mutation returned no data' });
    return;
  }

  res.status(200).json({
    id:       character.id,
    title:    character.title,
    imageUrl: character.image?.mediaImage?.url ?? null,
    alt:      portrait.alt,
    seed:     portrait.seed,
  });
}
