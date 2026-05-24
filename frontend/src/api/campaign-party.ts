import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

interface AddCharacterBody {
  campaignId:  string;
  characterId: string;
}

interface CampaignResult {
  id:   string;
  name: string;
}

interface GraphQlResponse {
  data?:   { addCharacterToCampaign: CampaignResult | null };
  errors?: Array<{ message: string }>;
}

const ADD_CHARACTER_MUTATION = `
  mutation AddCharacterToCampaign($campaignId: ID!, $characterId: ID!) {
    addCharacterToCampaign(campaignId: $campaignId, characterId: $characterId) {
      id
      name
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

  const body        = req.body as AddCharacterBody;
  const campaignId  = body?.campaignId?.trim();
  const characterId = body?.characterId?.trim();

  if (!campaignId || !characterId) {
    res.status(400).json({ error: 'campaignId and characterId are required' });
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
        query:     ADD_CHARACTER_MUTATION,
        variables: { campaignId, characterId },
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

  const campaign = payload.data?.addCharacterToCampaign ?? null;
  if (!campaign) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  res.status(200).json(campaign);
}
