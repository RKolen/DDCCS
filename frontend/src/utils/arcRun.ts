/**
 * Arc-analysis pieces shared by the console run and the queued job.
 *
 * The console (CharacterArcScreen) runs an arc analysis chunk by chunk so it
 * can show per-passage progress; the queued job has no browser attached and
 * runs the same sequence server-side via `runArcAnalysisServer`. Both use the
 * merge/format helpers here, so a queued arc and a hand-run arc are built from
 * identical data points.
 */

export interface StoryChunks {
  title:       string;
  storyNumber: number | null;
  chunks:      string[];
}

/** One story's arc data point (the shape the sidecar returns per chunk). */
export interface ArcDataPointDict {
  story_file:    string;
  session_id:    string;
  timestamp:     string;
  metric_values: Record<string, number>;
  observations:  string[];
  key_events:    string[];
  ai_analysis:   string;
}

/**
 * Merge a story's per-chunk data points into one story-level data point:
 * metrics averaged, observations/events/summaries collected. Keeps the aggregate
 * payload small (per-story, not per-chunk) so it stays under the request limit.
 */
export function mergeStoryChunks(
  parts: ArcDataPointDict[],
  title: string,
  storyNumber: number | null,
): ArcDataPointDict {
  const totals: Record<string, number> = {};
  const counts: Record<string, number> = {};
  const observations: string[] = [];
  const keyEvents: string[] = [];
  const summaries: string[] = [];
  for (const part of parts) {
    for (const [key, value] of Object.entries(part.metric_values ?? {})) {
      if (typeof value === 'number') {
        totals[key] = (totals[key] ?? 0) + value;
        counts[key] = (counts[key] ?? 0) + 1;
      }
    }
    observations.push(...(part.observations ?? []));
    keyEvents.push(...(part.key_events ?? []));
    if (part.ai_analysis) {
      summaries.push(part.ai_analysis);
    }
  }
  const metricValues: Record<string, number> = {};
  for (const key of Object.keys(totals)) {
    metricValues[key] = Math.round((totals[key] / counts[key]) * 10) / 10;
  }
  return {
    story_file:    title,
    session_id:    storyNumber != null ? String(storyNumber) : '',
    timestamp:     new Date().toISOString(),
    metric_values: metricValues,
    observations:  observations.slice(0, 8),
    key_events:    keyEvents.slice(0, 8),
    ai_analysis:   summaries.join(' '),
  };
}

/** Format a merged story data point into readable prose for the wysiwyg node. */
export function formatStoryAnalysis(part: ArcDataPointDict): string {
  const sections: string[] = [];
  if (part.ai_analysis) {
    sections.push(part.ai_analysis);
  }
  if (part.key_events?.length) {
    sections.push(`Key events: ${part.key_events.join('; ')}`);
  }
  if (part.observations?.length) {
    sections.push(`Observations: ${part.observations.join('; ')}`);
  }
  return sections.join('\n\n');
}


/* ────────────────────────────────────────────────────────────
   Server-side runner (queued job)
   ──────────────────────────────────────────────────────────── */

/** What a queued arc run needs to know about its target. */
export interface ArcRunParams {
  characterName: string;
  campaignId:    string;
  characterId:   string;
  pronouns:      string;
  storyIds:      string[];
}

/** What a finished arc run reports back onto the job. */
export interface ArcRunResult {
  storiesAnalysed: number;
  direction:       string;
  stage:           string;
  summary:         string;
}

/** POST JSON to one of this site's own API routes and parse the response. */
async function callApi<T>(baseUrl: string, route: string, body: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}/api/${route}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  // Read as text first so an error page yields a useful message rather than a
  // raw JSON parse error.
  const raw = await res.text();
  let data: unknown = null;
  try {
    data = raw ? JSON.parse(raw) : null;
  } catch {
    throw new Error(raw.slice(0, 200) || `${route} failed (${res.status})`);
  }
  if (!res.ok) {
    const message = (data as { error?: string } | null)?.error;
    throw new Error(message || `${route} failed (${res.status})`);
  }
  return data as T;
}

/**
 * Run a character's arc analysis to completion, server-side.
 *
 * Mirrors the console's chunk-at-a-time run - every model call stays small and
 * bounded - but without a browser to report progress to: the queue is what
 * tracks it now. Each story's analysis is persisted as it finishes, so a story
 * already stored is skipped and a crashed run resumes. Synthesis reads those
 * stored data points and saves the arc onto the character.
 *
 * @param baseUrl Origin of this site, used to reach its sibling API routes.
 * @param params The character, campaign, and stories to analyse.
 */
export async function runArcAnalysisServer(
  baseUrl: string,
  params: ArcRunParams,
): Promise<ArcRunResult> {
  const { characterName, campaignId, characterId, pronouns, storyIds } = params;

  const stories: StoryChunks[] = [];
  for (const storyId of storyIds) {
    try {
      const data = await callApi<{ chunks?: string[]; title?: string; storyNumber?: number | null }>(
        baseUrl, 'arc-story-chunks', { storyId },
      );
      if (Array.isArray(data.chunks) && data.chunks.length > 0) {
        stories.push({
          title:       data.title ?? '',
          storyNumber: data.storyNumber ?? null,
          chunks:      data.chunks,
        });
      }
    } catch {
      // Skip a story whose chunks cannot be fetched; the rest still run.
    }
  }
  if (stories.length === 0) {
    throw new Error('No story text found to analyse.');
  }

  // Resume signal: story numbers already stored on the analysis node.
  let done = new Set<number>();
  try {
    const stored = await callApi<{ storyNumbers?: unknown[] }>(
      baseUrl, 'get-analysis', { campaignId, characterId },
    );
    done = new Set((stored.storyNumbers ?? []).filter((n): n is number => typeof n === 'number'));
  } catch {
    // No resume data available; every story is analysed.
  }

  let analysed = 0;
  for (const story of stories) {
    if (story.storyNumber !== null && done.has(story.storyNumber)) {
      continue;
    }
    const parts: ArcDataPointDict[] = [];
    for (const chunk of story.chunks) {
      // One retry, then the passage is skipped: one bad passage must not
      // abort a run that may already be many minutes old.
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          const data = await callApi<{ dataPoint: ArcDataPointDict }>(
            baseUrl, 'arc-analyze-story',
            { characterName, content: chunk, title: story.title, storyNumber: story.storyNumber, pronouns },
          );
          parts.push(data.dataPoint);
          break;
        } catch {
          // Retried by the loop; an unrecovered passage is skipped.
        }
      }
    }
    if (parts.length === 0) {
      continue;
    }
    const merged = mergeStoryChunks(parts, story.title, story.storyNumber);
    analysed += 1;
    await callApi(baseUrl, 'upsert-analysis', {
      campaignId,
      characterId,
      storyNumber: story.storyNumber,
      storyText:   formatStoryAnalysis(merged),
      datapoint:   JSON.stringify(merged),
    });
  }

  if (analysed === 0 && done.size === 0) {
    throw new Error('Every passage failed to analyse - is the sidecar running?');
  }

  // Synthesis aggregates every stored data point (this run plus earlier ones)
  // and saves the arc onto the character.
  const arc = await callApi<{ direction?: string; stage?: string; summary?: string; storiesAnalyzed?: number }>(
    baseUrl, 'synthesize-analysis', { campaignId, characterId, characterName, pronouns },
  );

  return {
    storiesAnalysed: arc.storiesAnalyzed ?? analysed,
    direction:       arc.direction ?? '',
    stage:           arc.stage ?? '',
    summary:         arc.summary ?? '',
  };
}
