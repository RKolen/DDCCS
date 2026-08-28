import * as React from 'react';

/**
 * Client-side helpers for the queued heavy AI actions.
 *
 * A console action no longer holds a request open for the minutes a model run
 * takes: it enqueues a job, gets an id back immediately, and polls. Navigating
 * away is safe - the work runs on the host either way, and the activity bar
 * picks it back up.
 *
 * Because a job can finish while nobody is watching the screen that started it,
 * a job that generates content stores its output without applying it. The
 * console reads that from the result's `review` marker and calls `resolveJob()`
 * once the operator has accepted or discarded it.
 */

/** The job states Advanced Queue reports. */
export type JobState = 'queued' | 'processing' | 'success' | 'failure';

/**
 * Where a finished job's result stands with the operator.
 *
 * A job that generates content stores it but does not apply it, so a render
 * finishing while nobody is looking can never replace something by itself.
 * `pending` means the console still owes a decision.
 */
export type JobReview = 'pending' | 'accepted' | 'discarded';

/** Job type plugin ids, as registered by the dnd_jobs module. */
export const JOB_TYPES = {
  portrait:      'dnd_portrait',
  arc:           'dnd_arc_analysis',
  story:         'dnd_story_generation',
  summary:       'dnd_session_summary',
  relations:     'dnd_arc_relations',
  backfill:      'dnd_arc_backfill',
  storyEvents:   'dnd_story_events',
  illustration:  'dnd_story_illustration',
} as const;

/** One queued job, as the console sees it. */
export interface AiJob {
  id:        string;
  type:      string;
  state:     JobState;
  label:     string;
  message:   string | null;
  /** JSON-encoded, job-type-specific result; use `jobResult` to read it. */
  result:    string | null;
  /**
   * UUID of the character the job is about, known from the moment it is queued.
   * Read from the request payload rather than the result, which is what lets the
   * activity bar link a job that is still running.
   */
  subjectId: string | null;
  /**
   * True when the job is claimed but its processing lease has expired: nothing is
   * working on it any more and it needs requeueing. Never true for live work.
   */
  stalled:   boolean | null;
  created:   number | null;
  processed: number | null;
}

/** How often a poll asks for a job's state. Model runs take minutes. */
const POLL_INTERVAL_MS = 3000;

/** True once a job has stopped moving, either way. */
export function isFinished(job: AiJob | null): boolean {
  return job?.state === 'success' || job?.state === 'failure';
}

/**
 * Decode a finished job's result payload.
 *
 * @param job The job to read.
 * @returns The decoded result object, or null when there is none.
 */
export function jobResult<T>(job: AiJob | null): T | null {
  if (!job?.result) return null;
  try {
    return JSON.parse(job.result) as T;
  } catch {
    return null;
  }
}

/**
 * Queue a job and return it.
 *
 * @param type    The job type plugin id (see JOB_TYPES).
 * @param label   Display name shown in the activity bar.
 * @param payload Job-type-specific payload.
 * @throws Error when the queue rejects the job or is unreachable.
 */
export async function enqueueJob(
  type: string,
  label: string,
  payload: Record<string, unknown>,
): Promise<AiJob> {
  const res = await fetch('/api/enqueue-job', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ type, label, payload }),
  });
  const data = (await res.json()) as { job?: AiJob; error?: string };
  if (!res.ok || !data.job) {
    throw new Error(data.error ?? `Could not queue the job (${res.status})`);
  }
  return data.job;
}

/**
 * Accept or discard a finished job's pending result.
 *
 * Accepting is what writes the result onto the content - until then a queued
 * portrait is only a file in the media library. Discarding leaves the content
 * as it was and marks the job decided, so the activity bar stops asking.
 *
 * @param id       The job to review.
 * @param accepted True to apply the result, false to leave it unapplied.
 * @returns The reviewed job, whose result now records the decision.
 * @throws Error when the job cannot be reviewed or Drupal is unreachable.
 */
export async function resolveJob(id: string, accepted: boolean): Promise<AiJob> {
  const res = await fetch('/api/resolve-job', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id, accepted }),
  });
  const data = (await res.json()) as { job?: AiJob; error?: string };
  if (!res.ok || !data.job) {
    throw new Error(data.error ?? `Could not review the job (${res.status})`);
  }
  return data.job;
}

/**
 * Put a stalled job back on the queue.
 *
 * For a job whose worker went away mid-run - a restarted sidecar, a host that
 * ran out of memory - which otherwise holds a claim nobody is honouring. Drupal
 * cron recovers these on its own once the lease expires; this is the button for
 * not waiting.
 *
 * @param id The job to requeue.
 * @returns The requeued job, back in the queued state.
 * @throws Error when the job does not exist or Drupal is unreachable.
 */
export async function requeueJob(id: string): Promise<AiJob> {
  const res = await fetch('/api/requeue-job', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ id }),
  });
  const data = (await res.json()) as { job?: AiJob; error?: string };
  if (!res.ok || !data.job) {
    throw new Error(data.error ?? `Could not requeue the job (${res.status})`);
  }
  return data.job;
}

/** What clearing the activity log did. */
export interface ClearJobsResult {
  /** How many finished jobs were deleted. */
  cleared: number;
  /** How many were kept back because their result still needs a decision. */
  kept: number;
}

/**
 * Clear finished jobs from the activity log.
 *
 * The drawer has no local copy to forget - it is a live view of Drupal's job
 * table - so this deletes those rows. Live and pending jobs are never touched,
 * and a finished job still awaiting accept/discard is kept back, since deleting
 * it would strand the render it produced.
 *
 * @param states Terminal states to clear. Omit for both success and failure.
 * @returns How many jobs were deleted and how many were kept.
 * @throws Error when Drupal rejects the states or is unreachable.
 */
export async function clearFinishedJobs(states?: JobState[]): Promise<ClearJobsResult> {
  const res = await fetch('/api/clear-jobs', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(states ? { states } : {}),
  });
  const data = (await res.json()) as Partial<ClearJobsResult> & { error?: string };
  if (!res.ok || typeof data.cleared !== 'number') {
    throw new Error(data.error ?? `Could not clear the activity log (${res.status})`);
  }
  return { cleared: data.cleared, kept: data.kept ?? 0 };
}

/** Read one job's current state. */
export async function fetchJob(id: string): Promise<AiJob | null> {
  const res = await fetch(`/api/job-status?id=${encodeURIComponent(id)}`);
  if (!res.ok) return null;
  const data = (await res.json()) as { job?: AiJob | null };
  return data.job ?? null;
}

/** List recent jobs, optionally filtered by state. */
export async function fetchJobs(states: JobState[], limit = 20): Promise<AiJob[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (states.length > 0) params.set('states', states.join(','));
  const res = await fetch(`/api/job-status?${params.toString()}`);
  if (!res.ok) return [];
  const data = (await res.json()) as { jobs?: AiJob[] };
  return data.jobs ?? [];
}

/**
 * Follow one job to completion.
 *
 * Pass a job id to start polling; the hook stops as soon as the job succeeds or
 * fails, and `onFinish` fires once with the final job. Remounting with the same
 * id resumes following it, which is what makes navigating away safe.
 *
 * @param jobId    The job to follow, or null to poll nothing.
 * @param onFinish Called once when the job reaches a final state.
 */
export function useJobPolling(
  jobId: string | null,
  onFinish?: (job: AiJob) => void,
): AiJob | null {
  const [job, setJob] = React.useState<AiJob | null>(null);
  // Held in a ref so a re-rendered parent passing a new closure does not
  // restart the interval mid-run.
  const finishRef = React.useRef(onFinish);
  finishRef.current = onFinish;

  React.useEffect(() => {
    if (!jobId) {
      setJob(null);
      return undefined;
    }
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const poll = async (): Promise<void> => {
      const next = await fetchJob(jobId);
      if (cancelled) return;
      if (next) {
        setJob(next);
        if (isFinished(next)) {
          finishRef.current?.(next);
          return;
        }
      }
      timer = setTimeout(() => void poll(), POLL_INTERVAL_MS);
    };
    void poll();

    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [jobId]);

  return job;
}

/**
 * Watch everything in flight, for the activity bar.
 *
 * Polls the running and pending jobs plus the most recent finished ones, so a
 * job that completed while you were on another screen still shows up.
 *
 * `refresh` re-reads immediately, for right after an action that changed the
 * list (clearing it, requeueing something) where waiting out the poll interval
 * would make the console look like it ignored the click.
 */
export function useJobActivity(): {
  running: AiJob[];
  recent: AiJob[];
  refresh: () => void;
} {
  const [running, setRunning] = React.useState<AiJob[]>([]);
  const [recent, setRecent] = React.useState<AiJob[]>([]);
  // Bumped to force the polling effect to restart, which re-reads at once.
  const [nonce, setNonce] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const poll = async (): Promise<void> => {
      const [live, done] = await Promise.all([
        fetchJobs(['processing', 'queued'], 20),
        fetchJobs(['success', 'failure'], 5),
      ]);
      if (cancelled) return;
      setRunning(live);
      setRecent(done);
      timer = setTimeout(() => void poll(), POLL_INTERVAL_MS);
    };
    void poll();

    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [nonce]);

  const refresh = React.useCallback(() => setNonce(n => n + 1), []);

  return { running, recent, refresh };
}
