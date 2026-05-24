import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

interface CreateCampaignBody {
  name:    string;
  status?: string;
}

interface CampaignResult {
  id:             string;
  name:           string;
  campaignStatus: string | null;
}

interface GraphQlResponse {
  data?:   { createCampaign: CampaignResult | null };
  errors?: Array<{ message: string }>;
}

const CREATE_CAMPAIGN_MUTATION = `
  mutation CreateCampaign($name: String!, $status: String) {
    createCampaign(name: $name, status: $status) {
      id
      name
      campaignStatus
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

  const body   = req.body as CreateCampaignBody;
  const name   = body?.name?.trim();

  if (!name) {
    res.status(400).json({ error: 'Campaign name is required' });
    return;
  }

  // GATSBY_DRUPAL_BASE_URL is the HTTP version of the Drupal URL — preferred
  // here to avoid Node.js rejecting DDEV's self-signed TLS certificate.
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
      method: 'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept:         'application/json',
      },
      body: JSON.stringify({
        query:     CREATE_CAMPAIGN_MUTATION,
        variables: {
          name,
          status: body.status ?? null,
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

  const campaign = payload.data?.createCampaign ?? null;
  if (!campaign) {
    res.status(500).json({ error: 'Campaign creation returned no data' });
    return;
  }

  res.status(201).json(campaign);
}
