/**
 * Story-arc payload contract, shared by the console and the API functions.
 * Mirrors what Drupal's `StoryArcWriter` accepts.
 *
 * Every key is optional: all three arc mutations take partial patches, so the
 * wizard writes what the current step knows. References may be a UUID or an
 * exact name; unresolvable ones are skipped by Drupal, not fatal.
 */

export interface ArcFieldPayload {
  /** The full premise. */
  body?:          string;
  /** Act structure / campaign spine. */
  overallPlot?:   string;
  /** Levels the arc spans, e.g. "4-10". */
  levelRange?:    string;
  targetStories?: number | null;
  /** factions-vocabulary term UUID or exact name. */
  faction?:       string;
  /** Character node UUIDs or exact titles. */
  party?:         string[];
  npcs?:          string[];
  /** Update only. */
  title?:         string;
  /** Update only: campaign term UUID or exact name. */
  campaign?:      string;
}

/** 1 = direct and personal, 2 = thematic, 3 = incidental. */
export type ArcRelationTier = 1 | 2 | 3;

export interface ArcRelationPayload {
  /** Character node UUID or exact title. */
  source: string;
  target: string;
  /** Short label, e.g. "sworn protector". */
  type?:  string;
  tier?:  ArcRelationTier;
  note?:  string;
}

/** Only the sides present are replaced, so each side saves independently. */
export interface ArcRelationsPayload {
  party?: ArcRelationPayload[];
  npc?:   ArcRelationPayload[];
}
