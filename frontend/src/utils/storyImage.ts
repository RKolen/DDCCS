/**
 * Helpers for the queued story-scene illustration pipeline.
 *
 * Event extraction and the ComfyUI render both run as Advanced Queue jobs so
 * the browser never holds a minutes-long ComfyUI request. Review-before-attach
 * matches portraits: the PNG sits in the media library until accept.
 */

export interface StoryImageRosterPerson {
  name: string;
  characterId: string;
  portraitUrl: string;
  appearance: string;
  isNpc: boolean;
}

export interface StoryEventChoice {
  title: string;
  oneLine: string;
  excerpt: string;
}

export interface StoryEventsJobResult {
  storyId: string;
  title?: string;
  events: Array<{ title: string; one_line?: string; excerpt?: string }>;
  review?: string;
}

export interface StoryIllustrationJobResult {
  storyId: string;
  mediaId: string;
  imageUrl: string | null;
  alt: string;
  seed: number | null;
  prompt?: string;
  usedIpadapter?: number;
  leadFaces?: string[];
  swappedFaces?: string[];
  review: string;
}

/** Cap on appearance tags, so one long stored prompt cannot eat the scene. */
export const MAX_APPEARANCE_CHARS = 140;

/** Landscape scene size: larger than a 512x768 portrait, still SD 1.5-class. */
export const SCENE_WIDTH = 768;
export const SCENE_HEIGHT = 512;

/**
 * Appearance tags the scene prompt can use when there is no portrait field.
 *
 * @param person Lineage, species, and class from Drupal.
 * @returns A short comma-separated tag string, possibly empty.
 */
export function appearanceFromCharacter(person: {
  lineage?: string | null;
  species?: string | null;
  characterClass?: string | null;
  imagePrompt?: string | null;
}): string {
  // The stored image prompt is what someone wrote down on purpose, so it
  // outranks lineage and class - it is the only place details like
  // spectacles or a scar are ever recorded.
  const stored = person.imagePrompt?.trim();
  if (stored) return stored.slice(0, MAX_APPEARANCE_CHARS);
  return [person.lineage, person.species, person.characterClass]
    .filter((part): part is string => Boolean(part && part.trim()))
    .join(', ');
}

/**
 * Map a Drupal character (console or story page) onto the wizard roster row.
 *
 * @param person Character fields the wizard needs.
 * @returns One roster person.
 */
export function rosterPersonFromCharacter(person: {
  id: string;
  title: string;
  imageUrl?: string | null;
  imagePrompt?: string | null;
  lineage?: string | null;
  species?: string | null;
  characterClass?: string | null;
  characterType?: boolean | null;
  isNpc?: boolean;
}): StoryImageRosterPerson {
  return {
    name: person.title,
    characterId: person.id,
    portraitUrl: person.imageUrl ?? '',
    appearance: appearanceFromCharacter(person),
    isNpc: person.isNpc ?? person.characterType === false,
  };
}

/**
 * Snake_case roster rows the sidecar / Drupal job payload expects.
 *
 * @param people Console or story-page roster.
 * @returns Payload rows.
 */
export function toRosterPayload(
  people: StoryImageRosterPerson[],
): Array<Record<string, unknown>> {
  return people.map(person => ({
    name: person.name,
    character_id: person.characterId,
    portrait_url: person.portraitUrl,
    appearance: person.appearance,
    is_npc: person.isNpc,
  }));
}

/**
 * Snake_case in-frame people for the illustration job.
 *
 * @param people Roster members left in the shot.
 * @param likeness Character ids whose portraits should drive likeness.
 * @returns Payload rows.
 */
export function toPeoplePayload(
  people: StoryImageRosterPerson[],
  likeness: Set<string>,
): Array<Record<string, unknown>> {
  return people.map(person => ({
    name: person.name,
    character_id: person.characterId,
    portrait_url: person.portraitUrl,
    appearance: person.appearance,
    is_npc: person.isNpc,
    known: person.characterId !== '',
    use_likeness: likeness.has(person.characterId) && person.portraitUrl !== '',
  }));
}

/**
 * Normalise an events job result into picker rows.
 *
 * @param result The job result.
 * @returns Events the operator can pick.
 */
export function eventsFromResult(result: StoryEventsJobResult | null): StoryEventChoice[] {
  if (result == null) return [];
  return (result.events ?? [])
    .map(event => ({
      title: event.title?.trim() ?? '',
      oneLine: (event.one_line ?? '').trim(),
      excerpt: (event.excerpt ?? '').trim(),
    }))
    .filter(event => event.title !== '' && event.excerpt !== '');
}

/** Longest hand-picked passage sent as an excerpt, matching the sidecar cap. */
export const MAX_PASSAGE_CHARS = 900;

/** Shortest passage worth offering; below this there is no scene to draw. */
const MIN_PASSAGE_CHARS = 80;

/** Longest title derived from a passage, before it is cut on a word break. */
const MAX_DERIVED_TITLE = 60;

const ENTITIES: Record<string, string> = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
  hellip: '…', mdash: '—', ndash: '–',
  lsquo: '‘', rsquo: '’', ldquo: '“', rdquo: '”',
};

/**
 * Strip markup and decode the entities a Drupal processed body carries.
 *
 * @param html Processed HTML or plain text.
 * @returns Plain prose with collapsed whitespace.
 */
function toProse(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&#(\d+);/g, (_, code: string) => String.fromCodePoint(Number(code)))
    .replace(/&([a-z]+);/gi, (whole, name: string) => ENTITIES[name.toLowerCase()] ?? whole)
    .split(/\s+/)
    .join(' ')
    .trim();
}

/**
 * Split a story body into passages the operator can illustrate directly.
 *
 * The model proposing nothing must never be the end of the road, so the
 * paragraphs the reader already sees are offered as moments in their own
 * right. Needs no model call, which is also why it is instant.
 *
 * @param body Processed HTML or plain text.
 * @returns Passages in story order, long enough to describe a scene.
 */
export function passagesFromBody(body: string): string[] {
  return body
    .split(/<\/p>|<br\s*\/?>|\n{2,}/i)
    .map(toProse)
    .filter(passage => passage.length >= MIN_PASSAGE_CHARS)
    .map(passage => (
      passage.length > MAX_PASSAGE_CHARS
        ? `${passage.slice(0, MAX_PASSAGE_CHARS).trimEnd()}…`
        : passage
    ));
}

/**
 * Name a passage the operator picked, for the job label and image alt text.
 *
 * @param passage   The chosen text.
 * @param fallback  Used when the passage yields nothing usable.
 * @returns A short title.
 */
export function passageTitle(passage: string, fallback: string): string {
  const prose = toProse(passage);
  if (prose === '') return fallback;
  const sentence = prose.split(/(?<=[.!?])\s/)[0] ?? prose;
  if (sentence.length <= MAX_DERIVED_TITLE) return sentence.replace(/[.!?]$/, '');
  const cut = sentence.slice(0, MAX_DERIVED_TITLE);
  const lastSpace = cut.lastIndexOf(' ');
  return `${(lastSpace > 20 ? cut.slice(0, lastSpace) : cut).trimEnd()}…`;
}

/** Shot types the scene renderer understands, in framing order. */
export const SHOT_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'wide',   label: 'Wide - figures small in the frame' },
  { value: 'full',   label: 'Full body - head to toe' },
  { value: 'medium', label: 'Medium - waist up' },
  { value: 'close',  label: 'Close - head and shoulders' },
];

/** Camera angles. Anything but "behind" bans rear views in the negative. */
export const ANGLE_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'front',         label: 'Facing the viewer' },
  { value: 'three_quarter', label: 'Three-quarter' },
  { value: 'side',          label: 'Side profile' },
  { value: 'behind',        label: 'From behind' },
];

export const DEFAULT_SHOT = 'full';
export const DEFAULT_ANGLE = 'three_quarter';
