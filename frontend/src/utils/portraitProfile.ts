import * as React from 'react';
import type { DrupalCharacter } from '../components/console/ConsoleContext';
import {
  enqueueJob, fetchJob, isFinished, jobResult, resolveJob,
  useJobPolling, JOB_TYPES,
  type AiJob, type JobReview,
} from './aiJobs';

/**
 * Shared helpers for driving the ComfyUI portrait pipeline from the console.
 *
 * Both the character detail screen (one-click Generate) and the Portrait Studio
 * screen (parameterised generation) build the same profile shape and post it to
 * `/api/generate-portrait`, so the mapping lives here to stay in one place.
 *
 * `usePortraitReview` is the other shared piece: the queue-then-confirm cycle
 * both screens drive. Keeping it here is what guarantees neither screen can grow
 * a path that attaches a render without asking.
 */

// SD 1.5-class checkpoints render portraits best at 512x768; the sidecar's
// default (832x1216) is SDXL-shaped and degrades on SD 1.5 (doubled faces,
// slower on CPU). If an SDXL checkpoint is ever configured, these should move
// to sidecar config keyed off the checkpoint rather than being fixed here.
export const DEFAULT_PORTRAIT_WIDTH = 512;
export const DEFAULT_PORTRAIT_HEIGHT = 768;

// How strongly a reference portrait pulls a regeneration back towards the
// original face (IPAdapter). Matches the sidecar's own default; above ~0.9 the
// prompt stops mattering, below ~0.5 the likeness washes out.
export const DEFAULT_IDENTITY_WEIGHT = 0.8;

/**
 * What a finished `dnd_portrait` job carries back.
 *
 * The job stores the render in the media library but leaves the character's
 * portrait alone, so this describes a candidate: `review` is `pending` until the
 * console accepts it (which points `field_image` at `mediaId`) or discards it.
 */
export interface PortraitJobResult {
  characterId: string;
  mediaId:     string;
  imageUrl:    string | null;
  alt:         string;
  seed:        number | null;
  /**
   * Whether the render was actually conditioned on the previous portrait.
   * False when likeness was not asked for, and also when it was asked for but
   * could not be applied (IPAdapter not installed, reference unfetchable) - the
   * sidecar renders anyway rather than failing, so this is how a screen knows
   * not to promise a likeness the picture does not have.
   */
  usedReference?: boolean;
  review:      JobReview;
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

/** A finished render waiting on the operator's decision. */
export interface PortraitCandidate {
  /** The job that produced it, and the id `resolveJob` needs. */
  jobId:    string;
  /** Where the stored render can be previewed. */
  imageUrl: string;
  /** Seed it was rendered with, so a keeper can be reproduced. */
  seed:     number | null;
  /** True when the previous portrait's likeness was carried into this render. */
  usedReference: boolean;
}

/** What `usePortraitReview` hands a screen. */
export interface PortraitReview {
  /** True while a render is queued or running on the host. */
  running: boolean;
  /** The render awaiting Accept or Discard, or null. */
  candidate: PortraitCandidate | null;
  /** Which review call is in flight, or null. */
  reviewing: 'accept' | 'discard' | null;
  /** The portrait now stored on the character, once one was accepted. */
  attachedUrl: string | null;
  /** Last failure from generating or reviewing, or null. */
  error: string | null;
  /** Last outcome notice worth showing, or null. */
  notice: string | null;
  /** Queue a render. The payload is the `dnd_portrait` job payload. */
  generate: (label: string, payload: Record<string, unknown>) => Promise<void>;
  /** Make the candidate the character's portrait. */
  accept: () => Promise<void>;
  /** Leave the character alone; the render stays in the media library. */
  discard: () => Promise<void>;
  /** Drop all state, e.g. when the selected character changes. */
  reset: () => void;
}

/**
 * Drive one character's queue-render-then-confirm cycle.
 *
 * Generation is queued, so it outlives this screen: the host renders whether or
 * not anyone is watching. That is exactly why the result is not applied for you
 * - a job finishing in the background must not overwrite a portrait somebody
 * chose deliberately. What comes back is a candidate, and `accept` is the only
 * thing that touches the character.
 *
 * @param reviewJobId A job to pick back up, as passed by the activity bar when
 *   the operator clicks through to review it. Follows it if it is still running,
 *   and surfaces its candidate if it has already finished.
 * @returns The review state and the actions that move it along.
 */
export function usePortraitReview(reviewJobId?: string | null): PortraitReview {
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [running, setRunning] = React.useState(false);
  const [candidate, setCandidate] = React.useState<PortraitCandidate | null>(null);
  const [reviewing, setReviewing] = React.useState<'accept' | 'discard' | null>(null);
  const [attachedUrl, setAttachedUrl] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  /* Turn a finished job into a candidate, or an error. Shared by the poll that
     follows a render started here and the pickup of one started elsewhere. */
  const absorb = React.useCallback((job: AiJob): void => {
    if (job.state === 'failure') {
      setError(job.message ?? 'Portrait generation failed.');
      return;
    }
    const result = jobResult<PortraitJobResult>(job);
    if (result === null || !result.imageUrl) {
      setError('The render finished but produced no image.');
      return;
    }
    if (result.review === 'pending') {
      setCandidate({
        jobId:         job.id,
        imageUrl:      result.imageUrl,
        seed:          result.seed,
        usedReference: result.usedReference === true,
      });
      return;
    }
    // Already decided: drop any candidate we were showing, so the screen cannot
    // keep offering a decision the job has on record.
    setCandidate(null);
    if (result.review === 'accepted') {
      setAttachedUrl(result.imageUrl);
      setNotice('That render is already attached to this character.');
      return;
    }
    setNotice('That render was discarded. It is still in the media library.');
  }, []);

  useJobPolling(jobId, job => {
    setJobId(null);
    setRunning(false);
    absorb(job);
  });

  /* Pick up a job the activity bar sent us to, whether it is still rendering or
     already finished and waiting on a decision. */
  React.useEffect(() => {
    if (!reviewJobId) return undefined;
    let cancelled = false;
    void (async (): Promise<void> => {
      const job = await fetchJob(reviewJobId);
      if (cancelled || job === null) return;
      if (!isFinished(job)) {
        setJobId(job.id);
        setRunning(true);
        return;
      }
      absorb(job);
    })();
    return () => { cancelled = true; };
  }, [reviewJobId, absorb]);

  const generate = React.useCallback(async (
    label: string,
    payload: Record<string, unknown>,
  ): Promise<void> => {
    setRunning(true);
    setError(null);
    setNotice(null);
    setCandidate(null);
    try {
      const job = await enqueueJob(JOB_TYPES.portrait, label, payload);
      setJobId(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not queue the portrait.');
      setRunning(false);
    }
  }, []);

  const review = React.useCallback(async (accepted: boolean): Promise<void> => {
    if (candidate === null) return;
    setReviewing(accepted ? 'accept' : 'discard');
    setError(null);
    setNotice(null);
    try {
      await resolveJob(candidate.jobId, accepted);
      if (accepted) {
        setAttachedUrl(candidate.imageUrl);
        setNotice('Portrait attached to the character.');
      } else {
        setNotice('Render discarded. It stays in the media library if you want it later.');
      }
      setCandidate(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save that decision.');
      // Re-read the job so the screen shows what actually happened rather than
      // continuing to offer a decision the server may have already recorded.
      const current = await fetchJob(candidate.jobId);
      if (current !== null && isFinished(current)) absorb(current);
    } finally {
      setReviewing(null);
    }
  }, [candidate, absorb]);

  const accept = React.useCallback(() => review(true), [review]);
  const discard = React.useCallback(() => review(false), [review]);

  const reset = React.useCallback((): void => {
    setJobId(null);
    setRunning(false);
    setCandidate(null);
    setReviewing(null);
    setAttachedUrl(null);
    setError(null);
    setNotice(null);
  }, []);

  return { running, candidate, reviewing, attachedUrl, error, notice, generate, accept, discard, reset };
}
