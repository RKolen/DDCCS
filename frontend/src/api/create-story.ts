import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

interface CreateStoryBody {
  campaignId:   string;
  title:        string;
  body:         string;
  storyNumber:  number;
  sessionDate?: string;
}

interface StoryResult {
  id:    string;
  title: string;
  path:  string | null;
}

interface GraphQlResponse {
  data?:   { createStory: StoryResult | null };
  errors?: Array<{ message: string }>;
}

const CREATE_STORY_MUTATION = `
  mutation CreateStory(
    $campaignId:  ID!
    $title:       String!
    $body:        String!
    $storyNumber: Int!
    $sessionDate: String
  ) {
    createStory(
      campaignId:  $campaignId
      title:       $title
      body:        $body
      storyNumber: $storyNumber
      sessionDate: $sessionDate
    ) {
      id
      title
      path
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

  const body = req.body as CreateStoryBody;
  if (!body?.campaignId || !body?.title || !body?.body) {
    res.status(400).json({ error: 'campaignId, title, and body are required' });
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
        query:     CREATE_STORY_MUTATION,
        variables: {
          campaignId:  body.campaignId,
          title:       body.title,
          body:        body.body,
          storyNumber: body.storyNumber,
          sessionDate: body.sessionDate ?? new Date().toISOString().slice(0, 10),
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

  const story = payload.data?.createStory ?? null;
  if (!story) {
    res.status(500).json({ error: 'Mutation returned no data' });
    return;
  }

  res.status(200).json(story);
}
