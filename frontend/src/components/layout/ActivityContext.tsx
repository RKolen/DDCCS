/**
 * ActivityContext — one activity log for the whole site.
 *
 * Polling, drawer state, and row handlers live here, mounted once by
 * GlobalLayout, so a queued job stays visible wherever you navigate rather
 * than only on the console route.
 *
 * StatelyLedger registers two console-only behaviours via `registerConsole()`
 * while mounted: resolving a character id to its screen, and opening a row in
 * place. Elsewhere the defaults deep-link back to `/`.
 */

import * as React from 'react';
import { navigate } from 'gatsby';
import {
  useJobActivity, jobResult, requeueJob, clearFinishedJobs, JOB_TYPES,
} from '../../utils/aiJobs';
import type { AiJob } from '../../utils/aiJobs';
import type { PortraitJobResult } from '../../utils/portraitProfile';
import type { ActivityItem, ActivityTarget } from '../console/menuData';

/** What the console supplies while it is the active page. */
export interface ConsoleActivityHandlers {
  /** Resolves a character id to the screen showing that character. */
  locate: (characterId: string) => ActivityTarget | undefined;
  /** Opens a row's screen in place, without a page load. */
  open: (item: ActivityItem) => void;
}

interface ActivityApi {
  items: ActivityItem[];
  open: boolean;
  setOpen: (open: boolean) => void;
  full: boolean;
  setFull: (full: boolean) => void;
  clearing: boolean;
  openRow: (item: ActivityItem) => void;
  requeueRow: (item: ActivityItem) => void;
  clearFinished: () => void;
  registerConsole: (handlers: ConsoleActivityHandlers | null) => void;
}

const ActivityContext = React.createContext<ActivityApi | null>(null);

/**
 * Read the shared activity log.
 *
 * Returns null when called outside GlobalLayout, which lets a component opt out
 * rather than crash — the log is an aid, never load-bearing.
 */
export function useActivity(): ActivityApi | null {
  return React.useContext(ActivityContext);
}

/**
 * Register the console's row handlers for as long as the caller is mounted.
 *
 * @param handlers The console's locate/open pair, or null to use the defaults.
 */
export function useConsoleActivity(handlers: ConsoleActivityHandlers | null): void {
  const api = React.useContext(ActivityContext);
  const register = api?.registerConsole;

  /* Registering the caller's object directly made this an update loop: the
     console rebuilds locate/open whenever its roster changes identity, the
     registration then set provider state, and that re-rendered the console.
     React caps it with "Maximum update depth exceeded". Register one stable
     proxy instead and keep the live pair behind a ref, so registration happens
     once per mount however often the handlers are rebuilt. */
  const latest = React.useRef(handlers);
  latest.current = handlers;

  const active = handlers != null;
  React.useEffect(() => {
    if (register == null || !active) return undefined;
    register({
      locate: (characterId: string) => latest.current?.locate(characterId),
      open:   (item: ActivityItem) => latest.current?.open(item),
    });
    return () => register(null);
  }, [register, active]);
}

/**
 * Render one queued AI job as an activity-drawer row.
 *
 * A job waiting for the processor reads as `queued`, not `running`: it is in
 * flight from the operator's point of view, but nothing is working on it yet and
 * showing it as busy has misled us before.
 *
 * Every portrait job gets a target - the screen its output lands on - so the row
 * is a way back to the work from the moment it is queued, not only once it has
 * finished. `subjectId` is what makes that possible before there is a result. A
 * finished job whose result is still `pending` additionally gets `needsReview`,
 * which is what turns the link into the accept/discard decision; without it a
 * render would sit in the media library with nothing pointing at it.
 *
 * @param job    The job as the queue reports it.
 * @param locate Resolves a character id to the screen showing that character.
 */
function jobToActivityItem(
  job: AiJob,
  locate: (characterId: string) => ActivityTarget | undefined,
): ActivityItem {
  const stalled = Boolean(job.stalled);
  const status: ActivityItem['status'] =
    job.state === 'success' ? 'done'
      : job.state === 'failure' ? 'failed'
        : job.state === 'queued' ? 'queued'
        // A claimed job whose lease lapsed is not running, whatever the state
        // column says; drawing it as busy is what left us watching a spinner.
          : stalled ? 'failed' : 'running';
  const elapsed = job.processed && job.created && job.processed > job.created
    ? `${job.processed - job.created}s`
    : undefined;

  const isPortrait = job.type === JOB_TYPES.portrait;
  const portrait = isPortrait ? jobResult<PortraitJobResult>(job) : null;
  const needsReview = portrait?.review === 'pending';
  const subject = portrait?.characterId ?? job.subjectId;
  const target = isPortrait && subject ? locate(subject) : undefined;

  const detail = needsReview
    ? 'Rendered - not attached until you accept it'
    : stalled
      ? 'Stalled - the host stopped responding; requeue to run it again'
      : job.state === 'queued'
        ? 'Waiting for the host queue'
        : job.message ?? (job.state === 'processing' ? 'Running on the host' : '');

  return {
    kind: 'ai',
    status,
    label: job.label,
    detail,
    elapsed,
    jobId: job.id,
    target,
    subjectId: subject ?? undefined,
    needsReview,
    stalled,
  };
}

/**
 * Where a portrait row points when the console is not mounted to resolve it.
 *
 * The console addresses a character by roster index, which only it can compute.
 * Off-console the id is all we have, so the row targets the same screen and
 * leaves the id for the deep link to resolve.
 */
const OFF_CONSOLE_TARGET: ActivityTarget = { sectionId: 'characters', itemId: 'ascii' };

export function ActivityProvider(
  { children }: { children: React.ReactNode },
): React.ReactElement {
  const { running, recent, refresh } = useJobActivity();
  const [open, setOpen] = React.useState(true);
  const [full, setFull] = React.useState(false);
  const [clearing, setClearing] = React.useState(false);
  const [console_, setConsole] = React.useState<ConsoleActivityHandlers | null>(null);

  const registerConsole = React.useCallback(
    (handlers: ConsoleActivityHandlers | null) => setConsole(handlers),
    [],
  );

  const locate = React.useCallback(
    (characterId: string): ActivityTarget | undefined => (
      console_ != null ? console_.locate(characterId) : OFF_CONSOLE_TARGET
    ),
    [console_],
  );

  const items = React.useMemo(
    () => [...running, ...recent].map(job => jobToActivityItem(job, locate)),
    [running, recent, locate],
  );

  /* On the console, open the row's screen in place. Anywhere else, hand the
     character id to the console route's `?char=` deep link, which resolves it
     against the roster the console alone has. */
  const openRow = React.useCallback((item: ActivityItem): void => {
    if (item.target == null) return;
    setFull(false);
    if (console_ != null) {
      console_.open(item);
      return;
    }
    const query = new URLSearchParams({
      section: item.target.sectionId,
      item:    item.target.itemId,
    });
    if (item.subjectId != null) query.set('char', item.subjectId);
    void navigate(`/?${query.toString()}`);
  }, [console_]);

  /* Put a stalled job back on the queue, then re-read so the row updates now
     rather than on the next tick. */
  const requeueRow = React.useCallback((item: ActivityItem): void => {
    if (item.jobId == null) return;
    void requeueJob(item.jobId)
      .catch(() => {
        /* The refresh below re-reads the truth either way. */
      })
      .finally(() => refresh());
  }, [refresh]);

  /* Clear the finished jobs. Drupal decides what is safe to delete; anything it
     keeps back (a result still awaiting a decision) reappears on the refresh. */
  const clearFinished = React.useCallback((): void => {
    setClearing(true);
    void clearFinishedJobs()
      .catch(() => {
        /* Nothing was deleted; the refresh shows the list unchanged. */
      })
      .finally(() => {
        setClearing(false);
        refresh();
      });
  }, [refresh]);

  const value = React.useMemo<ActivityApi>(() => ({
    items, open, setOpen, full, setFull, clearing,
    openRow, requeueRow, clearFinished, registerConsole,
  }), [items, open, full, clearing, openRow, requeueRow, clearFinished, registerConsole]);

  return <ActivityContext.Provider value={value}>{children}</ActivityContext.Provider>;
}
