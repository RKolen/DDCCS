import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { selfBaseUrl } from '../utils/selfUrl';
import { toArcRelations, type SuggestDigest, type SuggestedRelation } from '../utils/arcSuggest';
import type { DrupalArcRelation } from '../components/console/ConsoleContext';

/**
 * Run a whole relation-suggestion side server-side, for the queued job.
 *
 * The console's interactive run loops in the browser so it can show progress;
 * a queued job has no browser, so the worker calls this one endpoint and the
 * loop happens here.
 *
 * Long-running by nature (one model call per subject), which is what makes the
 * queue the right home for it. Nothing is written to Drupal: the suggestions
 * come back as the job's result for the operator to accept or reject, the same
 * as a queued portrait.
 */

interface RunRelationsBody {
  side:       'party' | 'npc';
  subjects:   SuggestDigest[];
  candidates: SuggestDigest[];
  roster:     Array<{ id: string; title: string }>;
  context?:   string;
  arcId?:     string;
}

interface RunRelationsResult {
  arcId:       string;
  side:        'party' | 'npc';
  subjectsRun: number;
  suggested:   DrupalArcRelation[];
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

  const body = req.body as RunRelationsBody;
  if (!Array.isArray(body?.subjects) || body.subjects.length === 0) {
    res.status(400).json({ error: 'subjects are required' });
    return;
  }
  if (!Array.isArray(body.candidates) || body.candidates.length === 0) {
    res.status(400).json({ error: 'candidates are required' });
    return;
  }

  const baseUrl = selfBaseUrl();
  if (!baseUrl) {
    res.status(500).json({ error: 'GATSBY_HOST and GATSBY_PORT must be set in the root .env' });
    return;
  }

  const side = body.side === 'npc' ? 'npc' : 'party';
  const batches: SuggestedRelation[][] = [];
  let subjectsRun = 0;

  for (const subject of body.subjects) {
    const others = side === 'party'
      ? body.candidates.filter(c => c.name !== subject.name)
      : body.candidates;
    if (others.length === 0) {
      continue;
    }
    try {
      const result = await callApi<{ relations: SuggestedRelation[] }>(
        baseUrl, 'suggest-arc-relations',
        { subject, others, kind: side, context: body.context ?? '' },
      );
      batches.push(result.relations ?? []);
      subjectsRun += 1;
    } catch {
      /* One failing subject must not lose a run that is already minutes old. */
      batches.push([]);
    }
  }

  let merged: SuggestedRelation[] = [];
  try {
    const result = await callApi<{ relations: SuggestedRelation[] }>(
      baseUrl, 'merge-arc-relations', { batches },
    );
    merged = result.relations ?? [];
  } catch {
    merged = batches.flat();
  }

  const out: RunRelationsResult = {
    arcId:       body.arcId ?? '',
    side,
    subjectsRun,
    suggested:   toArcRelations(merged, body.roster ?? []),
  };
  res.status(200).json(out);
}
