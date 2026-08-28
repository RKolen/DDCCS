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
  swappedFaces?: string[];
  review: string;
}

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
}): string {
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
