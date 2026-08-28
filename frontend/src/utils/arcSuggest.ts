/**
 * Drive batched relationship suggestion from the browser.
 *
 * One request per party member, looped here rather than server-side, so the
 * console can show which subject is being worked on and how far along the run
 * is.
 * 
 * A failing subject does not abort the run: its batch is skipped and the rest
 * continue, because a partial web is still useful and a rerun is cheap.
 */

import type { DrupalCharacter, DrupalArcRelation } from '../components/console/ConsoleContext';
import type { ArcRelationTier } from './arcPayload';

/** Digest of one character, matching the sidecar's CharacterDigest. */
export interface SuggestDigest {
  name: string;
  summary: string;
  origin: string;
  faction: string;
  hooks: string[];
}

/** A suggestion as the sidecar returns it. */
export interface SuggestedRelation {
  source: string;
  target: string;
  relation_type?: string;
  tier?: number;
  note?: string;
}

export interface SuggestProgress {
  /** Subjects finished so far. */
  done: number;
  /** Subjects in the run. */
  total: number;
  /** The subject currently being asked about. */
  current: string;
}

/** Reduce a character to the few fields that actually generate connections. */
export function toDigest(char: DrupalCharacter): SuggestDigest {
  const hooks = [
    ...(char.plotHooks ?? []),
    ...(char.bonds ?? []),
    ...(char.majorPlotActions ?? []),
  ]
    .map(h => h.trim())
    .filter(Boolean)
    .slice(0, 3);

  return {
    name: char.title,
    summary: [char.species, char.characterClass, char.role].filter(Boolean).join(' '),
    /* No dedicated origin field exists on the character; the sheet's own hooks
       carry that detail, so origin stays empty rather than being invented. */
    origin: '',
    faction: char.faction ?? '',
    hooks,
  };
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const payload = (await res.json()) as T & { error?: string };
  if (!res.ok || payload.error) {
    throw new Error(payload.error ?? `Request failed (${res.status})`);
  }
  return payload;
}

/** Run one relation side, one subject at a time, then merge the batches. */
export async function suggestRelations(
  subjects: DrupalCharacter[],
  candidates: DrupalCharacter[],
  kind: 'party' | 'npc',
  context: string,
  onProgress: (progress: SuggestProgress) => void,
): Promise<DrupalArcRelation[]> {
  const batches: SuggestedRelation[][] = [];

  for (let i = 0; i < subjects.length; i += 1) {
    const subject = subjects[i];
    const others = kind === 'party'
      ? candidates.filter(c => c.id !== subject.id)
      : candidates;
    if (others.length === 0) {
      continue;
    }
    onProgress({ done: i, total: subjects.length, current: subject.title });
    try {
      const result = await postJson<{ relations: SuggestedRelation[] }>(
        '/api/suggest-arc-relations',
        {
          subject: toDigest(subject),
          others: others.map(toDigest),
          kind,
          context,
        },
      );
      batches.push(result.relations ?? []);
    } catch {
      /* One failure must not lose the subjects that succeeded. */
      batches.push([]);
    }
  }
  onProgress({ done: subjects.length, total: subjects.length, current: '' });

  if (batches.length === 0) {
    return [];
  }

  let merged: SuggestedRelation[] = [];
  try {
    const result = await postJson<{ relations: SuggestedRelation[] }>(
      '/api/merge-arc-relations',
      { batches },
    );
    merged = result.relations ?? [];
  } catch {
    merged = batches.flat();
  }

  return toArcRelations(merged, [...subjects, ...candidates]);
}

/**
 * Resolve suggested names back to character UUIDs. A name not on the roster is
 * dropped rather than stored half-anchored.
 */
export function toArcRelations(
  suggestions: SuggestedRelation[],
  roster: Array<{ id: string; title: string }>,
): DrupalArcRelation[] {
  const byName = new Map<string, { id: string; title: string }>();
  for (const char of roster) {
    byName.set(char.title.toLowerCase(), char);
  }

  const out: DrupalArcRelation[] = [];
  const seen = new Set<string>();
  for (const s of suggestions) {
    const source = byName.get((s.source ?? '').trim().toLowerCase());
    const target = byName.get((s.target ?? '').trim().toLowerCase());
    if (!source || !target || source.id === target.id) {
      continue;
    }
    const key = [source.id, target.id].sort().join('|');
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    const tier = s.tier === 1 || s.tier === 2 || s.tier === 3
      ? (s.tier as ArcRelationTier)
      : 2;
    out.push({
      sourceId: source.id,
      sourceName: source.title,
      targetId: target.id,
      targetName: target.title,
      type: s.relation_type ?? '',
      tier,
      note: s.note ?? '',
    });
  }
  return out;
}
