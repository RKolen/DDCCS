import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { selfBaseUrl } from '../utils/selfUrl';
import {
  storiesWithoutRecaps,
  toArcDraft,
  type ArcDraft,
  type ArcRecap,
  type BackfillStory,
  type DiscoveredNpc,
  type RawArcDraft,
} from '../utils/arcBackfill';

/**
 * Run a whole arc backfill server-side, for the queued job.
 *
 * The console's interactive run loops in the browser so it can show which
 * session is being read; a queued job has no browser, so the Drupal worker
 * calls this one endpoint and the loop happens here.
 *
 * Long-running by nature - one model call per unsummarised session - which is
 * what makes the queue the right home for it. Nothing is written to an arc:
 * the draft comes back as the job's result for the operator to edit and accept,
 * the same as a queued portrait. The recaps themselves are persisted as they
 * are produced, so a rerun resumes rather than restarting.
 */

interface RunBackfillBody {
  campaignId:   string;
  campaignName: string;
  stories:      BackfillStory[];
  party?:       string[];
  npcs?:        string[];
}

interface RunBackfillResult {
  campaignId:  string;
  summarised:  number;
  recapsUsed:  number;
  draft:       ArcDraft | null;
  cast:        DiscoveredNpc[];
}

async function callApi<T>(baseUrl: string, route: string, body: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}/api/${route}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  const payload = (await res.json()) as T & { error?: string };
  if (!res.ok || payload.error) {
    throw new Error(payload.error ?? `${route} failed (${res.status})`);
  }
  return payload;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as RunBackfillBody;
  if (!body?.campaignId?.trim()) {
    res.status(400).json({ error: 'campaignId is required' });
    return;
  }
  if (!Array.isArray(body.stories) || body.stories.length === 0) {
    res.status(400).json({ error: 'stories are required' });
    return;
  }

  const baseUrl = selfBaseUrl();
  if (!baseUrl) {
    res.status(500).json({ error: 'GATSBY_HOST and GATSBY_PORT must be set in the root .env' });
    return;
  }

  const campaignId = body.campaignId.trim();
  let recaps: ArcRecap[] = [];
  try {
    const existing = await callApi<{ recaps: ArcRecap[] }>(
      baseUrl, 'campaign-recaps', { campaignId },
    );
    recaps = [...(existing.recaps ?? [])];
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not read the campaign's recaps: ${message}` });
    return;
  }

  let summarised = 0;
  for (const story of storiesWithoutRecaps(body.stories, recaps)) {
    try {
      const recap = await callApi<ArcRecap>(
        baseUrl, 'summarize-story', { campaignId, storyId: story.id },
      );
      recaps.push(recap);
      summarised += 1;
    } catch {
      /* One unreadable story must not lose a run that is already minutes old. */
    }
  }

  if (recaps.length === 0) {
    res.status(422).json({ error: 'None of this campaign\'s stories could be summarised.' });
    return;
  }
  recaps.sort((a, b) => a.storyNumber - b.storyNumber);

  try {
    const drafted = await callApi<{ draft: RawArcDraft | null }>(baseUrl, 'draft-arc', {
      campaignName: body.campaignName ?? '',
      recaps,
      party: body.party ?? [],
      npcs:  body.npcs ?? [],
    });

    /* The cast is a second question of the same recaps. Losing it costs the
       discovered NPCs, not the arc, so it never fails the job. */
    let cast: DiscoveredNpc[] = [];
    try {
      const found = await callApi<{ npcs: DiscoveredNpc[] }>(
        baseUrl, 'extract-story-npcs',
        {
          campaignName: body.campaignName ?? '',
          recaps,
          party: body.party ?? [],
          known: body.npcs ?? [],
        },
      );
      cast = found.npcs ?? [];
    } catch {
      cast = [];
    }

    const result: RunBackfillResult = {
      campaignId,
      summarised,
      recapsUsed: recaps.length,
      draft:      toArcDraft(drafted.draft),
      cast,
    };
    res.status(200).json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
