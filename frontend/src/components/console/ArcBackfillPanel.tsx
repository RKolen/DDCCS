/**
 * "Draft an arc from the stories so far" - the way in for a campaign that was
 * played before story arcs existed.
 *
 * Such a campaign has no arc, so the arc screen has nothing to show and
 * relationship suggestion has nothing to hang on. The run summarises any
 * session that has never been summarised (one model call each, minutes apiece
 * locally) and proposes the arc they add up to, which lands in an editable
 * review rather than in Drupal.
 */

import * as React from 'react';
import { drupalAdminUrl } from '../../utils/drupalLinks';
import { Icon, Spinner } from './atoms';
import type { DrupalCharacter } from './ConsoleContext';
import { ArcDraftReview } from './ArcDraftReview';
import {
  createArcFromDraft,
  createNpcStubs,
  runArcBackfill,
  type ArcDraft,
  type BackfillProgress,
  type BackfillStory,
  type DiscoveredNpc,
} from '../../utils/arcBackfill';
import { enqueueJob, JOB_TYPES } from '../../utils/aiJobs';

export interface ArcBackfillPanelProps {
  campaignId:   string;
  campaignName: string;
  stories:      BackfillStory[];
  party:        DrupalCharacter[];
  npcs:         DrupalCharacter[];
  /** A draft picked back up from a queued run, if any. */
  incoming?:    ArcDraft | null;
  /** The cast that came back with a queued run's draft. */
  incomingCast?: DiscoveredNpc[];
}

export function ArcBackfillPanel({
  campaignId, campaignName, stories, party, npcs, incoming, incomingCast,
}: ArcBackfillPanelProps): React.ReactElement {
  const [draft, setDraft]       = React.useState<ArcDraft | null>(null);
  const [cast, setCast]         = React.useState<DiscoveredNpc[]>([]);
  const [created, setCreated]   = React.useState<
    { title: string; path: string | null; npcsMade: number } | null
  >(null);
  const [running, setRunning]   = React.useState(false);
  const [progress, setProgress] = React.useState<BackfillProgress | null>(null);
  const [error, setError]       = React.useState<string | null>(null);
  const [notice, setNotice]     = React.useState<string | null>(null);

  /* A draft from a queued run replaces whatever is on screen: the operator
     followed the activity bar here to review that specific run. */
  React.useEffect(() => {
    if (incoming) {
      setDraft(incoming);
      setCast(incomingCast ?? []);
    }
  }, [incoming, incomingCast]);

  const numbered = React.useMemo(
    () => stories.filter(s => s.storyNumber !== null),
    [stories],
  );

  async function run(): Promise<void> {
    setRunning(true);
    setError(null);
    setNotice(null);
    setProgress({ done: 0, total: numbered.length, current: '', phase: 'summarising' });
    try {
      const result = await runArcBackfill(
        {
          campaignId,
          campaignName,
          stories: numbered,
          party:   party.map(p => p.title),
          npcs:    npcs.map(n => n.title),
        },
        setProgress,
      );
      if (result.draft === null) {
        setNotice('The model proposed nothing usable. Try again, or write the arc by hand.');
      }
      setDraft(result.draft);
      setCast(result.cast);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
      setProgress(null);
    }
  }

  async function queue(): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await enqueueJob(JOB_TYPES.backfill, `Arc backfill: ${campaignName}`, {
        campaignId,
        campaignName,
        stories: numbered,
        party:   party.map(p => p.title),
        npcs:    npcs.map(n => n.title),
      });
      setNotice('Queued. The activity bar links back here when it finishes.');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  /* NPCs are created before the arc, because the arc has to point at them.
     One that Drupal refuses is skipped rather than blocking the arc. */
  const accept = React.useCallback(
    async (
      edited: ArcDraft,
      partyIds: string[],
      knownNpcIds: string[],
      createNpcs: DiscoveredNpc[],
    ): Promise<void> => {
      const made = await createNpcStubs(
        campaignId, createNpcs, `Read from the sessions of ${campaignName}.`,
      );
      const arc = await createArcFromDraft(
        campaignId, edited, partyIds, [...knownNpcIds, ...made.values()],
      );
      setDraft(null);
      setCast([]);
      setCreated({ title: arc.title, path: arc.path, npcsMade: made.size });
    },
    [campaignId, campaignName],
  );

  if (numbered.length === 0) {
    return (
      <p className="arc-empty">
        {campaignName} has no numbered stories, so there is no play history to
        read an arc out of. Create one from &quot;Create New Story Arc&quot;.
      </p>
    );
  }

  return (
    <div className="arc-backfill">
      <p className="arc-hint">
        {campaignName} has {numbered.length} stor{numbered.length === 1 ? 'y' : 'ies'} but
        no arc. Reading them summarises any session that has not been summarised
        yet - one model call each, minutes apiece - and proposes the arc they add
        up to. You edit and accept it before anything is written.
      </p>

      <div className="arc-inline-actions">
        <button
          type="button"
          className="ghost-btn"
          disabled={running}
          onClick={() => { void run(); }}
        >
          {running ? <Spinner label="Reading" /> : <Icon name="sparkle" size={11} />}
          {' '}Draft an arc from the stories so far
        </button>
        <button
          type="button"
          className="ghost-btn"
          disabled={running}
          onClick={() => { void queue(); }}
        >
          Queue the run
        </button>
        <span className="arc-hint">Runs on the host, so you can leave this screen.</span>
      </div>

      {progress && (
        <div className="arc-progress">
          <div className="arc-progress-bar">
            <span style={{ width: `${(progress.done / Math.max(progress.total, 1)) * 100}%` }} />
          </div>
          <p className="arc-hint">
            {progress.phase === 'drafting'
              ? 'Reading the campaign and proposing its arc'
              : progress.phase === 'casting'
                ? 'Reading which NPCs the sessions name'
                : progress.total === 0
                  ? 'Every session is already summarised'
                  : `Summarising ${progress.current} (${progress.done + 1} of ${progress.total})`}
          </p>
        </div>
      )}

      {error && <p className="arc-error">{error}</p>}
      {notice && !running && <p className="arc-saved">{notice}</p>}

      {created && (
        <p className="arc-saved">
          Created &quot;{created.title}&quot; on {campaignName}
          {created.npcsMade > 0 && `, along with ${created.npcsMade} new NPC${created.npcsMade === 1 ? '' : 's'}`}.
          {' '}
          {created.path && (
            <a href={drupalAdminUrl(created.path)} target="_blank" rel="noreferrer">
              Open it in Drupal
            </a>
          )}
          {' '}The console lists it, and can suggest its relations, after the
          site data is rebuilt.
        </p>
      )}

      {draft && (
        <ArcDraftReview
          draft={draft}
          party={party}
          cast={cast}
          npcs={npcs}
          onAccept={accept}
          onDiscard={() => { setDraft(null); setCast([]); }}
        />
      )}
    </div>
  );
}

