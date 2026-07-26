import * as React from 'react';

/**
 * Client-side helpers for the queued heavy AI actions.
 *
 * A console action no longer holds a request open for the minutes a model run
 * takes: it enqueues a job, gets an id back immediately, and polls. Navigating
 * away is safe - the work runs on the host either way, and the activity bar
 * picks it back up.
 */

/** The job states Advanced Queue reports. */
export type JobState = 'queued' | 'processing' | 'success' | 'failure';

/** Job type plugin ids, as registered by the dnd_jobs module. */
export const JOB_TYPES = {
  portrait:  'dnd_portrait',
  arc:       'dnd_arc_analysis',
  story:     'dnd_story_generation',
  summary:   'dnd_session_summary',
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
 */
export function useJobActivity(): { running: AiJob[]; recent: AiJob[] } {
  const [running, setRunning] = React.useState<AiJob[]>([]);
  const [recent, setRecent] = React.useState<AiJob[]>([]);

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
  }, []);

  return { running, recent };
}
