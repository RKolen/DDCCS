/**
 * Draft a story arc for a campaign that was played before arcs existed.
 *
 * Such a campaign has stories but no arc, so the arc screen has nothing to
 * show and relationship suggestion has nothing to hang on. This reads the
 * campaign's session recaps, summarises any session that has never been
 * summarised, and asks for the arc they add up to.
 *
 * The run is driven a session at a time rather than server-side in one call so
 * the console can show which session is being read: local inference takes
 * minutes per session, and a silent multi-minute request looks frozen.
 *
 * Nothing is written to the arc here. The draft comes back for review and only
 * `createArcFromDraft` - called after an explicit accept - creates the node.
 */

import type { ArcFieldPayload } from './arcPayload';

/** One session's recap, keyed by its position in the campaign. */
export interface ArcRecap {
  storyNumber: number;
  summary:     string;
}

/**
 * A proposed arc, as the sidecar returns it and the review screen edits it.
 *
 * Level range and target-story count are deliberately absent. Both stay fluid
 * for the life of an arc - a campaign can plan twenty-seven stories and write
 * fourteen - so a model reading the past has nothing to say about them. They
 * are set in the arc editor, where planning decisions belong.
 */
export interface ArcDraft {
  title:       string;
  premise:     string;
  overallPlot: string;
  faction:     string;
  /** Character titles, resolved against the roster by the review screen. */
  party:       string[];
  npcs:        string[];
}

/** The draft as it crosses the wire from the Python sidecar. */
export interface RawArcDraft {
  title?:        string;
  premise?:      string;
  overall_plot?: string;
  faction?:      string;
  party?:        string[];
  npcs?:         string[];
}

/**
 * One NPC the sessions name, whether or not a character node exists.
 *
 * `known` is what splits the review into "already on record, tick to include"
 * and "named in the stories but missing, tick to create".
 */
export interface DiscoveredNpc {
  name:  string;
  role:  string;
  known: boolean;
}

/** A story the backfill may need to summarise first. */
export interface BackfillStory {
  id:          string;
  title:       string;
  storyNumber: number | null;
}

export interface BackfillProgress {
  /** Sessions summarised so far in this run. */
  done: number;
  /** Sessions this run has to summarise. Zero when every recap already exists. */
  total: number;
  /** The session being read, or empty once the per-session pass is done. */
  current: string;
  phase: 'summarising' | 'drafting' | 'casting';
}

/** Normalise the sidecar's snake_case draft into the console's shape. */
export function toArcDraft(raw: RawArcDraft | null | undefined): ArcDraft | null {
  if (!raw?.title?.trim()) {
    return null;
  }
  return {
    title:       raw.title.trim(),
    premise:     (raw.premise ?? '').trim(),
    overallPlot: (raw.overall_plot ?? '').trim(),
    faction:     (raw.faction ?? '').trim(),
    party:       raw.party ?? [],
    npcs:        raw.npcs ?? [],
  };
}

/**
 * Which sessions still need summarising, in play order.
 *
 * A story with no number cannot be placed in the campaign's sequence, so it is
 * left out rather than summarised into an unorderable recap.
 */
export function storiesWithoutRecaps(
  stories: BackfillStory[],
  recaps: ArcRecap[],
): BackfillStory[] {
  const have = new Set(recaps.map(r => r.storyNumber));
  return stories
    .filter(s => s.storyNumber !== null && !have.has(s.storyNumber))
    .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0));
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  const payload = (await res.json()) as T & { error?: string };
  if (!res.ok || payload.error) {
    throw new Error(payload.error ?? `Request failed (${res.status})`);
  }
  return payload;
}

export interface BackfillInput {
  campaignId:   string;
  campaignName: string;
  stories:      BackfillStory[];
  /** Character titles the draft may name. */
  party:        string[];
  npcs:         string[];
}

/** What one backfill run produced. */
export interface BackfillResult {
  draft: ArcDraft | null;
  /** The cast the sessions name, known and missing alike. */
  cast:  DiscoveredNpc[];
}

/**
 * Summarise whatever the campaign is missing, then read its arc and its cast.
 *
 * @param input      The campaign, its stories, and the rosters the draft may name.
 * @param onProgress Called as each session is read and again for each later pass.
 * @returns The proposed arc and the NPCs the sessions name.
 * @throws Error when the campaign has no summarisable sessions at all.
 */
export async function runArcBackfill(
  input: BackfillInput,
  onProgress: (progress: BackfillProgress) => void,
): Promise<BackfillResult> {
  const existing = await postJson<{ recaps: ArcRecap[] }>(
    '/api/campaign-recaps', { campaignId: input.campaignId },
  );
  const recaps = [...(existing.recaps ?? [])];
  const pending = storiesWithoutRecaps(input.stories, recaps);

  for (let i = 0; i < pending.length; i += 1) {
    const story = pending[i];
    onProgress({ done: i, total: pending.length, current: story.title, phase: 'summarising' });
    try {
      const recap = await postJson<ArcRecap>(
        '/api/summarize-story', { campaignId: input.campaignId, storyId: story.id },
      );
      recaps.push(recap);
    } catch {
      /* A story with no body, or one call the model fumbled, must not lose the
         sessions already read: the arc is drafted from what did come back. */
    }
  }

  if (recaps.length === 0) {
    throw new Error('None of this campaign\'s stories could be summarised.');
  }

  recaps.sort((a, b) => a.storyNumber - b.storyNumber);
  const done = pending.length;

  onProgress({ done, total: pending.length, current: '', phase: 'drafting' });
  const drafted = await postJson<{ draft: RawArcDraft | null }>('/api/draft-arc', {
    campaignName: input.campaignName,
    recaps,
    party: input.party,
    npcs:  input.npcs,
  });

  /* The cast is a second question of the same recaps. A failure here costs the
     discovered NPCs, not the arc, so it never aborts the run. */
  onProgress({ done, total: pending.length, current: '', phase: 'casting' });
  let cast: DiscoveredNpc[] = [];
  try {
    const found = await postJson<{ npcs: DiscoveredNpc[] }>('/api/extract-story-npcs', {
      campaignName: input.campaignName,
      recaps,
      party: input.party,
      known: input.npcs,
    });
    cast = found.npcs ?? [];
  } catch {
    cast = [];
  }

  return { draft: toArcDraft(drafted.draft), cast };
}

/**
 * Create the NPCs ticked for creation, in order, and return their ids by name.
 *
 * Drupal returns the existing NPC when the campaign already has that name, so
 * a rerun adds nothing. One that fails is skipped rather than blocking the arc.
 *
 * @param campaignId The campaign to scope the new NPCs to.
 * @param npcs       The discovered NPCs the operator ticked.
 * @param note       Provenance recorded on each stub.
 * @returns A map of NPC name to the created character's UUID.
 */
export async function createNpcStubs(
  campaignId: string,
  npcs: DiscoveredNpc[],
  note: string,
): Promise<Map<string, string>> {
  const created = new Map<string, string>();
  for (const npc of npcs) {
    try {
      const made = await postJson<{ id: string; title: string }>('/api/create-npc', {
        campaignId,
        name: npc.name,
        role: npc.role,
        note,
      });
      created.set(npc.name, made.id);
    } catch {
      /* One NPC Drupal would not take must not cost the arc. */
    }
  }
  return created;
}

/** Map an accepted draft onto the arc field payload Drupal writes. */
export function draftToFields(
  draft: ArcDraft,
  partyIds: string[],
  npcIds: string[],
): ArcFieldPayload {
  const fields: ArcFieldPayload = {
    body:        draft.premise,
    overallPlot: draft.overallPlot,
    party:       partyIds,
    npcs:        npcIds,
  };
  /* An unmatched faction name is skipped by Drupal, but sending an empty one
     would clear a field the operator may have set on the form. */
  if (draft.faction.trim()) {
    fields.faction = draft.faction.trim();
  }
  return fields;
}

/**
 * Create the arc an accepted draft describes.
 *
 * @param campaignId The campaign the arc belongs to.
 * @param draft      The draft as the operator edited it.
 * @param partyIds   Character UUIDs for the party, as ticked on the review.
 * @param npcIds     Character UUIDs for the NPCs, as ticked on the review.
 * @returns The created arc.
 * @throws Error when Drupal rejects the arc.
 */
export async function createArcFromDraft(
  campaignId: string,
  draft: ArcDraft,
  partyIds: string[],
  npcIds: string[],
): Promise<{ id: string; title: string; path: string | null }> {
  const created = await postJson<{ id: string; title: string; path: string | null }>(
    '/api/create-story-arc',
    { campaignId, title: draft.title, fields: draftToFields(draft, partyIds, npcIds) },
  );
  return created;
}
