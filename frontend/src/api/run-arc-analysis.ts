import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { runArcAnalysisServer } from '../utils/arcRun';
import { selfBaseUrl } from '../utils/selfUrl';

/**
 * Run a character's whole arc analysis server-side, for the queued arc job.
 *
 * POST `{ characterName, campaignId, characterId, pronouns?, storyIds }` ->
 * `{ storiesAnalysed, direction, stage, summary }`. The console's interactive
 * run loops chunk by chunk in the browser so it can show progress; a queued job
 * has no browser, so the Drupal worker calls this one endpoint and the loop
 * happens here. Each story is persisted as it completes, so a failed run
 * resumes rather than restarting.
 *
 * Long-running by nature (minutes): it is called by the queue worker, which is
 * what makes that acceptable.
 */

interface RunArcBody {
  characterName: string;
  campaignId:    string;
  characterId:   string;
  pronouns?:     string;
  storyIds:      string[];
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as RunArcBody;
  if (!body?.characterName?.trim() || !body?.characterId?.trim()) {
    res.status(400).json({ error: 'characterName and characterId are required' });
    return;
  }
  if (!Array.isArray(body.storyIds) || body.storyIds.length === 0) {
    res.status(400).json({ error: 'storyIds are required' });
    return;
  }

  const baseUrl = selfBaseUrl();
  if (!baseUrl) {
    res.status(500).json({ error: 'GATSBY_HOST and GATSBY_PORT must be set in the root .env' });
    return;
  }

  try {
    const result = await runArcAnalysisServer(baseUrl, {
      characterName: body.characterName.trim(),
      campaignId:    body.campaignId ?? '',
      characterId:   body.characterId.trim(),
      pronouns:      body.pronouns ?? '',
      storyIds:      body.storyIds,
    });
    res.status(200).json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
