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
  regions?: boolean;
  review: string;
}

/**
 * Cap on appearance tags, so one long stored prompt cannot eat the scene.
 *
 * 140 was set when the field held a hand-written line. Captioned portraits
 * run to 220-300 characters, and 140 cut a rogue off after his gloves,
 * losing the daggers and boots that make him one - the wardrobe the caption
 * exists to supply. Region mode gives every character their own prompt, so
 * the length only has to fit one person.
 */
export const MAX_APPEARANCE_CHARS = 260;

/**
 * Trim tags to a budget without cutting one in half.
 *
 * A plain slice ends mid-tag - "black boots, ornate belt with circ" - and the
 * fragment is read as its own instruction rather than dropped.
 *
 * @param text Comma-separated tags.
 * @param budget Maximum characters.
 * @returns Whole tags only, within the budget.
 */
export function clipTags(text: string, budget: number): string {
  if (text.length <= budget) return text;
  const kept: string[] = [];
  let used = 0;
  for (const tag of text.split(',').map((part) => part.trim()).filter(Boolean)) {
    const cost = kept.length === 0 ? tag.length : tag.length + 2;
    if (used + cost > budget) break;
    kept.push(tag);
    used += cost;
  }
  return kept.join(', ');
}

/** Landscape scene size: larger than a 512x768 portrait, still SD 1.5-class. */
export const SCENE_WIDTH = 768;
export const SCENE_HEIGHT = 512;

/** Words that already fix a subject's gender, so no lead is needed. */
const GENDER_WORDS = [
  'male', 'female', 'man', 'woman', 'boy', 'girl', 'masculine', 'feminine',
];

/**
 * Whether a tag string already states a gender.
 *
 * @param text Comma-separated appearance tags.
 * @returns True when a gender word is already present.
 */
export function mentionsGender(text: string): boolean {
  const lower = text.toLowerCase();
  return GENDER_WORDS.some((word) => new RegExp(`\\b${word}\\b`).test(lower));
}

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
  gender?: string | null;
  imagePrompt?: string | null;
}): string {
  // The stored image prompt is what someone wrote down on purpose, so it
  // outranks lineage and class - it is the only place details like
  // spectacles or a scar are ever recorded. Gender still leads it: a
  // portrait description need not mention one, and a captioned male elf
  // whose tags said only "wood elf, long flowing black hair" came back a
  // woman. The stored text is trimmed to leave room for that word.
  const stored = person.imagePrompt?.trim();
  if (stored) {
    const gender = person.gender?.trim();
    if (!gender || mentionsGender(stored)) {
      return clipTags(stored, MAX_APPEARANCE_CHARS);
    }
    const lead = `${gender}, `;
    return lead + clipTags(stored, MAX_APPEARANCE_CHARS - lead.length);
  }
  // Gender leads. Left unsaid, the renderer picks one from its own bias and
  // returned a party of six women from a roster of three and three.
  return [person.gender, person.lineage, person.species, person.characterClass]
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
  gender?: string | null;
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
 * Appearance and action are separate on purpose. Appearance is who someone
 * is anywhere and comes from their Drupal image prompt; action is what they
 * are doing in this one scene. Left blank, the shot analysis fills it, so an
 * operator only types where they disagree.
 *
 * @param people Roster members left in the shot.
 * @param likeness Character ids whose portraits should drive likeness.
 * @param actions Per-character action text, keyed by character id.
 * @returns Payload rows.
 */
export function toPeoplePayload(
  people: StoryImageRosterPerson[],
  likeness: Set<string>,
  actions: ReadonlyMap<string, string> = new Map(),
): Array<Record<string, unknown>> {
  return people.map(person => ({
    name: person.name,
    character_id: person.characterId,
    portrait_url: person.portraitUrl,
    appearance: person.appearance,
    action: (actions.get(person.characterId) ?? '').trim(),
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

/**
 * Settings the scene renderer knows by name, mirroring
 * `src/story_images/staging.py`. Anything else an operator types is used as
 * the place, so this list is a convenience and not a restriction.
 * `tests/story_images/test_staging.py` fails if the two drift apart.
 */
export const SETTING_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: '',       label: 'From the story - let the analysis decide' },
  { value: 'yard',   label: 'Sparring ground' },
  { value: 'castle', label: 'Castle courtyard' },
  { value: 'forest', label: 'Forest clearing' },
  { value: 'ruins',  label: 'Ruined temple' },
  { value: 'snow',   label: 'Snowfield' },
  { value: 'hall',   label: 'Great hall' },
  { value: 'tavern', label: 'Tavern common room' },
  { value: 'road',   label: 'Country road' },
];

/** Overall tone, as light and colour. Mirrors `MOODS` in staging.py. */
export const MOOD_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: '',         label: 'From the story' },
  { value: 'neutral',  label: 'Neutral' },
  { value: 'tense',    label: 'Tense' },
  { value: 'heroic',   label: 'Heroic' },
  { value: 'grim',     label: 'Grim' },
  { value: 'warm',     label: 'Warm' },
  { value: 'eerie',    label: 'Eerie' },
  { value: 'peaceful', label: 'Peaceful' },
];

export const DEFAULT_SHOT = 'full';
export const DEFAULT_ANGLE = 'three_quarter';

/** Empty means "whatever the shot analysis wrote", which is the old behaviour. */
export const DEFAULT_SETTING = '';
export const DEFAULT_MOOD = '';

/** How much per-character action text the prompt can carry. */
export const MAX_ACTION_CHARS = 80;

/** One character's staging: where they stand, how far back, how turned. */
export interface StagePlacement {
  name:    string;
  lateral: number;
  depth:   number;
  pose:    string;
  facing:  string;
  toward:  string;
  /** 1 is painted last and comes out whole; 0 lets depth decide. */
  order:   number;
  /** left, top, width, height in canvas pixels; filled by the preview. */
  box?:    number[];
}

/**
 * Distance limits, mirroring NEAR_DEPTH / FAR_DEPTH in
 * `src/story_images/regions.py`. 1.0 is the front of the scene; larger is
 * further back, and both the figure's height and the floor it stands on
 * recede by the same factor - which is what makes distance read as distance
 * rather than as a short person standing at your feet.
 * `tests/story_images/test_staging.py` fails if these drift.
 */
export const NEAR_DEPTH = 1.0;
export const FAR_DEPTH = 3.0;

/**
 * Which way one character is turned. Per character, not per scene.
 *
 * Every figure is rendered alone against grey and composited, so one camera
 * angle for the whole cast cannot say that a group walks away while somebody
 * follows them. The composite path passed no angle at all, which is why a
 * render came back as a row of people looking at the lens.
 *
 * Mirrors `ANGLES` in `src/story_images/framing.py`; empty means the stance
 * decides and nothing is added to the prompt.
 */
export const FACING_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: '',              label: 'From the pose' },
  { value: 'front',         label: 'Facing the viewer' },
  { value: 'three_quarter', label: 'Three-quarter' },
  { value: 'side',          label: 'Side profile' },
  { value: 'behind',        label: 'Turned away' },
];

/**
 * Stances the renderer can draw, mirroring `POSE_VARIANTS` in
 * `src/story_images/pose.py`. Blank deals a stance from the rotating default,
 * so a cast nobody posed is not a row of identical statues.
 *
 * This is the half of staging that "Doing" could never supply. Action text
 * only reaches the prompt, and a skeleton drawn standing to attention beats
 * the word "walking" every time - so a scene asked for on the move came back
 * as a line-up wearing the right clothes.
 * `tests/story_images/test_staging.py` fails if the two drift apart.
 */
export const POSE_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: '',             label: 'Choose for me' },
  { value: 'standing',     label: 'Standing' },
  { value: 'arms_crossed', label: 'Arms crossed' },
  { value: 'hand_on_hip',  label: 'Hand on hip' },
  { value: 'gesturing',    label: 'Gesturing' },
  { value: 'leaning',      label: 'Leaning' },
  { value: 'holding',      label: 'Holding something' },
  { value: 'sitting',      label: 'Sitting' },
  { value: 'walking',      label: 'Walking' },
  { value: 'laughing',     label: 'Laughing' },
];

/**
 * Which way along the frame a turned figure points. Mirrors `TOWARD_SIGN` in
 * `src/story_images/pose.py`.
 *
 * Facing says how far round someone is turned; it cannot say which way. Set
 * a whole cast to side profile and they all face the same way - a conga line,
 * when what the scene wanted was a group walking on and one person coming up
 * to meet them. Blank is to the right, so existing staging is unchanged.
 */
export const TOWARD_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'right', label: 'To the right' },
  { value: 'left',  label: 'To the left' },
];

/** What the renderer assumes when a placement names no direction. */
export const DEFAULT_TOWARD = 'right';

/**
 * Build the staging payload for the in-frame cast.
 *
 * Laterals are spaced evenly here rather than left to the renderer: it only
 * spaces people out when the list is empty, so sending placements that each
 * carry the default 0.5 would stack the whole cast in the middle of the frame.
 *
 * @param people Roster members left in the shot, in order.
 * @param facings Per-character facing, keyed by character id.
 * @param poses Per-character stance, keyed by character id.
 * @param towards Per-character turn direction, keyed by character id.
 * @returns Placement rows, one per person.
 */
export function toPlacementsPayload(
  people: StoryImageRosterPerson[],
  facings: ReadonlyMap<string, string> = new Map(),
  poses: ReadonlyMap<string, string> = new Map(),
  towards: ReadonlyMap<string, string> = new Map(),
  order: readonly string[] = [],
): StagePlacement[] {
  return people.map((person, index) => ({
    name: person.name,
    lateral: (index + 0.5) / Math.max(people.length, 1),
    depth: NEAR_DEPTH,
    pose: poses.get(person.characterId) ?? '',
    facing: facings.get(person.characterId) ?? '',
    toward: towards.get(person.characterId) ?? '',
    order: order.indexOf(person.characterId) + 1,
  }));
}

/**
 * Rank every staged character from the front of the scene backwards.
 *
 * 1 is nearest the camera, and nearest is what the compositor paints last,
 * so a number 1 comes out whole wherever two figures overlap.
 *
 * An operator's own number wins. Depth alone was not enough: depth also sets
 * apparent size, and apparent size is not distance here - a halfling at the
 * front of the scene is still smaller than an orc at the back, so the small
 * character had to be dragged forward, and made everyone else's distance
 * wrong, just to stop being swallowed whole. Numbering is the separate
 * control that problem needs.
 *
 * Ties break on depth and then cast order, so the same staging always ranks
 * the same way.
 *
 * @param placements The staging, in cast order.
 * @returns Character name -> rank, counting from 1 at the front.
 */
export function depthRanks(placements: StagePlacement[]): Map<string, number> {
  const ordered = placements
    .map((row, index) => ({ name: row.name, order: row.order, depth: row.depth, index }))
    .sort((a, b) => (
      (a.order === 0 ? 1 : 0) - (b.order === 0 ? 1 : 0)
      || (a.order - b.order)
      || (a.depth - b.depth)
      || (a.index - b.index)
    ));
  return new Map(ordered.map((row, rank) => [row.name, rank + 1]));
}

/**
 * Move one character to a position in the front-to-back order.
 *
 * Typing a number is a reorder, not an assignment: making someone number 1
 * has to push whoever was there back, or two characters hold the same rank
 * and the tiebreak decides, which is not what the operator asked for.
 *
 * @param names    Character names, front first.
 * @param name     The one being moved.
 * @param position Where they should end up, counting from 1.
 * @returns The new front-to-back order.
 */
export function reorderTo(
  names: string[], name: string, position: number,
): string[] {
  const without = names.filter(row => row !== name);
  const at = Math.min(Math.max(Math.round(position), 1), without.length + 1);
  without.splice(at - 1, 0, name);
  return without;
}

/**
 * How much of a figure's box is covered by the figures in front of it.
 *
 * A character can be staged perfectly and still never appear, because a
 * taller neighbour stands exactly where they do. That is invisible in a
 * skeleton preview and costs a full render to discover, so it is measured
 * from the boxes the preview already returns.
 *
 * @param boxes Character name -> [left, top, width, height] in canvas pixels.
 * @param ranks Character name -> front-to-back rank, 1 at the front.
 * @returns Character name -> covered fraction, 0 to 1.
 */
export function hiddenFractions(
  boxes: ReadonlyMap<string, number[]>,
  ranks: ReadonlyMap<string, number>,
): Map<string, number> {
  const hidden = new Map<string, number>();
  for (const [name, box] of boxes) {
    if (box.length !== 4 || box[2] <= 0 || box[3] <= 0) continue;
    const rank = ranks.get(name) ?? 0;
    let covered = 0;
    for (const [other, front] of boxes) {
      if (other === name || front.length !== 4) continue;
      if ((ranks.get(other) ?? 0) >= rank) continue;
      const wide = Math.min(box[0] + box[2], front[0] + front[2])
        - Math.max(box[0], front[0]);
      const tall = Math.min(box[1] + box[3], front[1] + front[3])
        - Math.max(box[1], front[1]);
      if (wide > 0 && tall > 0) covered += wide * tall;
    }
    hidden.set(name, Math.min(covered / (box[2] * box[3]), 1));
  }
  return hidden;
}

/** Above this covered fraction a figure is worth warning about. */
export const HIDDEN_WARNING = 0.6;

/**
 * Above this many people, paint each character in their own masked region.
 *
 * The whole-scene path puts everybody in one prompt and gives likeness to at
 * most two of them, so a large cast loses both ways: the shared prompt leaves
 * roughly a name's worth of description each, and everyone after the second
 * gets a face swap rather than being composed into the picture. Six people
 * rendered as one. Region mode gives each character their own prompt and
 * their own pass.
 */
export const REGION_CAST_THRESHOLD = 2;

/**
 * Whether a cast of this size should be painted region by region.
 *
 * @param castSize How many people are in the shot.
 * @returns True when region mode is the better default.
 */
export function prefersRegions(castSize: number): boolean {
  return castSize > REGION_CAST_THRESHOLD;
}
