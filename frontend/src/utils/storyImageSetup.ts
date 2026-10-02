/**
 * Remembering a story's last illustration setup.
 *
 * A scene is tuned by repetition - queue it, look at it, change one thing,
 * queue it again. Between attempts the whole form has to be retyped: the
 * passage, who is in the shot, a facing and an action for each of them, the
 * framing and the staging. That costs more operator time than the render
 * costs GPU time, and the event extraction the wizard opens with is a
 * minutes-long Ollama job that a repeat run never uses.
 *
 * The setup is stored per story in the browser. None of it reaches the
 * repository, which is why it may hold whatever names a live campaign uses.
 */

import { DEFAULT_ANGLE, DEFAULT_MOOD, DEFAULT_SETTING, DEFAULT_SHOT,
  type StageLimb, type StagePlacement } from './storyImage';

const KEY_PREFIX = 'ddccs:storyImageSetup:';

/** Everything the cast step holds, flattened so it survives JSON. */
export interface StoryImageSetup {
  title:         string;
  excerpt:       string;
  inShot:        string[];
  likeness:      string[];
  facings:       Array<[string, string]>;
  poses:         Array<[string, string]>;
  towards:       Array<[string, string]>;
  order:         string[];
  actions:       Array<[string, string]>;
  shot:          string;
  angle:         string;
  setting:       string;
  mood:          string;
  regionsChoice: boolean | null;
  placements:    StagePlacement[];
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((row): row is string => typeof row === 'string') : [];
}

function pairs(value: unknown): Array<[string, string]> {
  if (!Array.isArray(value)) return [];
  return value.filter((row): row is [string, string] => (
    Array.isArray(row) && row.length === 2
    && typeof row[0] === 'string' && typeof row[1] === 'string'
  ));
}

function text(value: unknown, fallback: string): string {
  return typeof value === 'string' ? value : fallback;
}

function limbs(value: unknown): StageLimb[] {
  if (!Array.isArray(value)) return [];
  return value.filter((row): row is StageLimb => (
    typeof row === 'object' && row !== null
    && typeof (row as StageLimb).joint === 'string'
    && typeof (row as StageLimb).x === 'number'
    && typeof (row as StageLimb).y === 'number'
  ));
}

function placements(value: unknown): StagePlacement[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((row): row is StagePlacement => (
      typeof row === 'object' && row !== null
      && typeof (row as StagePlacement).name === 'string'
      && typeof (row as StagePlacement).lateral === 'number'
      && typeof (row as StagePlacement).depth === 'number'
    ))
    // Setups saved before limbs existed have none; a malformed list would
    // fail at the sidecar rather than here.
    .map(row => ({ ...row, limbs: limbs(row.limbs) }));
}

/**
 * Read back a stored setup, or null when there is none to read.
 *
 * Every field is checked rather than cast. A setup written by an older build
 * is still sitting in the browser after a deploy, and a missing array read as
 * one would fail inside the wizard rather than here, where it can simply be
 * treated as absent.
 *
 * @param storyId The Drupal story node id.
 * @returns The stored setup, or null.
 */
export function loadSetup(storyId: string): StoryImageSetup | null {
  if (typeof window === 'undefined' || storyId === '') return null;
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(KEY_PREFIX + storyId);
  } catch {
    return null;
  }
  if (raw === null) return null;
  let parsed: unknown = null;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof parsed !== 'object' || parsed === null) return null;
  const row = parsed as Record<string, unknown>;
  const excerpt = text(row.excerpt, '');
  if (excerpt.trim() === '') return null;
  return {
    title:         text(row.title, ''),
    excerpt,
    inShot:        strings(row.inShot),
    likeness:      strings(row.likeness),
    facings:       pairs(row.facings),
    poses:         pairs(row.poses),
    towards:       pairs(row.towards),
    order:         strings(row.order),
    actions:       pairs(row.actions),
    shot:          text(row.shot, DEFAULT_SHOT),
    angle:         text(row.angle, DEFAULT_ANGLE),
    setting:       text(row.setting, DEFAULT_SETTING),
    mood:          text(row.mood, DEFAULT_MOOD),
    regionsChoice: typeof row.regionsChoice === 'boolean' ? row.regionsChoice : null,
    placements:    placements(row.placements),
  };
}

/**
 * Store the setup a render was just queued with.
 *
 * @param storyId The Drupal story node id.
 * @param setup   What the cast step held at queue time.
 */
export function saveSetup(storyId: string, setup: StoryImageSetup): void {
  if (typeof window === 'undefined' || storyId === '') return;
  try {
    window.localStorage.setItem(KEY_PREFIX + storyId, JSON.stringify(setup));
  } catch {
    /* A full or blocked store costs a convenience, never the render. */
  }
}

/**
 * Forget a story's setup.
 *
 * @param storyId The Drupal story node id.
 */
export function clearSetup(storyId: string): void {
  if (typeof window === 'undefined' || storyId === '') return;
  try {
    window.localStorage.removeItem(KEY_PREFIX + storyId);
  } catch {
    /* Nothing to do; the next save overwrites it anyway. */
  }
}

/**
 * One line describing a stored setup, for the repeat button's tooltip.
 *
 * @param setup A stored setup.
 * @returns Cast size and passage title.
 */
export function setupSummary(setup: StoryImageSetup): string {
  const cast = setup.inShot.length;
  const who = cast === 1 ? '1 character' : `${cast} characters`;
  return setup.title === '' ? who : `${who} - ${setup.title}`;
}
