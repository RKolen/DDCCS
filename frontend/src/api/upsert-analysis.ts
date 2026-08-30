import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Persist a character_analysis node: one story's analysis and/or the summary.
 *
 * POST `{ campaignId, characterId, storyNumber?, storyText?, summary? }` ->
 * Drupal `upsertCharacterAnalysis`. The console calls this per story as each
 * completes (crash-safe persistence) and once more with the final summary.
 */

interface UpsertBody {
  campaignId:   string;
  characterId:  string;
  storyNumber?: number | null;
  storyText?:   string;
  datapoint?:   string;
  summary?:     string;
}

interface GraphQlResponse {
  data?:   { upsertCharacterAnalysis: { id: string } | null };
  errors?: Array<{ message: string }>;
}

const MUTATION = `
  mutation UpsertAnalysis(
    $campaignId:  ID!
    $characterId: ID!
    $storyNumber: Int
    $storyText:   String
    $datapoint:   String
    $summary:     String
  ) {
    upsertCharacterAnalysis(
      campaignId:  $campaignId
      characterId: $characterId
      storyNumber: $storyNumber
      storyText:   $storyText
      datapoint:   $datapoint
      summary:     $summary
    ) { id }
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

  const body = req.body as UpsertBody;
  if (!body?.characterId) {
    res.status(400).json({ error: 'characterId is required' });
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
        query: MUTATION,
        variables: {
          campaignId:  body.campaignId ?? '',
          characterId: body.characterId,
          storyNumber: body.storyNumber ?? null,
          storyText:   body.storyText ?? null,
          datapoint:   body.datapoint ?? null,
          summary:     body.summary ?? null,
        },
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${message}` });
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
  res.status(200).json(payload.data?.upsertCharacterAnalysis ?? { id: '' });
}
