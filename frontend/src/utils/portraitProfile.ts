import type { DrupalCharacter } from '../components/console/ConsoleContext';

/**
 * Shared helpers for driving the ComfyUI portrait pipeline from the console.
 *
 * Both the character detail screen (one-click Generate) and the Portrait Studio
 * screen (parameterised generation) build the same profile shape and post it to
 * `/api/generate-portrait`, so the mapping lives here to stay in one place.
 */

// SD 1.5-class checkpoints render portraits best at 512x768; the sidecar's
// default (832x1216) is SDXL-shaped and degrades on SD 1.5 (doubled faces,
// slower on CPU). If an SDXL checkpoint is ever configured, these should move
// to sidecar config keyed off the checkpoint rather than being fixed here.
export const DEFAULT_PORTRAIT_WIDTH = 512;
export const DEFAULT_PORTRAIT_HEIGHT = 768;

/**
 * What a finished `dnd_portrait` job carries back.
 *
 * The job attaches the image to the character itself, so the console only needs
 * the new URL to swap the portrait in place.
 */
export interface PortraitJobResult {
  characterId: string;
  mediaId:     string;
  imageUrl:    string | null;
  alt:         string;
  seed:        number | null;
}

/** Successful /api/generate-portrait response (the synchronous path). */
export interface GeneratePortraitResult {
  imageUrl: string | null;
  /** Seed actually used, echoed back so a pleasing render can be reproduced. */
  seed?: number;
  /** Alt text stored with the image. */
  alt?: string;
}

/**
 * Assemble the snake_case profile the sidecar portrait prompt builder reads
 * (see src/ai/portrait_prompt.py). Only the keys it uses are sent; empty fields
 * are omitted so a sparse character still yields a valid, non-generic prompt.
 */
export function buildPortraitProfile(char: DrupalCharacter): Record<string, unknown> {
  const profile: Record<string, unknown> = {};
  if (char.species) profile.species = char.species;
  if (char.lineage) profile.lineage = char.lineage;
  if (char.characterClass) profile.character_class = char.characterClass;
  if (char.pronouns) profile.pronouns = char.pronouns;
  if (char.background) profile.background = char.background;
  if (char.personalityTraits.length > 0) profile.personality_traits = char.personalityTraits;
  if (char.arc?.summary) profile.arc_summary = char.arc.summary;
  return profile;
}
