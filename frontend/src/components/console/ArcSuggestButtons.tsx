/**
 * "Suggest relations" controls. One model call per party member, so the run
 * takes minutes locally and shows which subject is in flight.
 */

import * as React from 'react';
import { Icon, Spinner } from './atoms';
import type { DrupalCharacter, DrupalArcRelation } from './ConsoleContext';
import { suggestRelations, toDigest, type SuggestProgress } from '../../utils/arcSuggest';
import { enqueueJob, JOB_TYPES } from '../../utils/aiJobs';

export interface ArcSuggestButtonsProps {
  party:      DrupalCharacter[];
  npcs:       DrupalCharacter[];
  context:    string;
  onSuggested: (side: 'party' | 'npc', relations: DrupalArcRelation[]) => void;
  /** Set to offer the queued run; omitted before the arc exists. */
  arcId?:     string;
}

export function ArcSuggestButtons({
  party, npcs, context, onSuggested, arcId,
}: ArcSuggestButtonsProps): React.ReactElement {
  const [running, setRunning]   = React.useState<'party' | 'npc' | null>(null);
  const [progress, setProgress] = React.useState<SuggestProgress | null>(null);
  const [error, setError]       = React.useState<string | null>(null);
  const [notice, setNotice]     = React.useState<string | null>(null);

  async function run(side: 'party' | 'npc'): Promise<void> {
    setRunning(side);
    setError(null);
    setNotice(null);
    setProgress({ done: 0, total: party.length, current: '' });
    try {
      const relations = await suggestRelations(
        party,
        side === 'party' ? party : npcs,
        side,
        side === 'npc' ? context : '',
        setProgress,
      );
      onSuggested(side, relations);
      setNotice(
        relations.length === 0
          ? 'The model suggested nothing it could justify. Try again, or add detail to the sheets.'
          : `Suggested ${relations.length} connection${relations.length === 1 ? '' : 's'}. Review below before saving.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(null);
      setProgress(null);
    }
  }

  async function queue(side: 'party' | 'npc'): Promise<void> {
    if (!arcId) {
      return;
    }
    setError(null);
    setNotice(null);
    try {
      const candidates = side === 'party' ? party : npcs;
      await enqueueJob(JOB_TYPES.relations, `Relations: ${side}`, {
        arcId,
        side,
        subjects:   party.map(toDigest),
        candidates: candidates.map(toDigest),
        roster:     [...party, ...npcs].map(c => ({ id: c.id, title: c.title })),
        context:    side === 'npc' ? context : '',
      });
      setNotice('Queued. The activity bar links back here when it finishes.');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const partyReady = party.length >= 2;
  const npcReady   = party.length >= 1 && npcs.length >= 1;

  return (
    <div className="arc-suggest">
      <div className="arc-inline-actions">
        <button
          type="button"
          className="ghost-btn"
          disabled={running !== null || !partyReady}
          title={partyReady ? undefined : 'Needs at least two party members'}
          onClick={() => { void run('party'); }}
        >
          {running === 'party' ? <Spinner label="Suggesting" /> : <Icon name="sparkle" size={11} />}
          {' '}Suggest party relations
        </button>
        <button
          type="button"
          className="ghost-btn"
          disabled={running !== null || !npcReady}
          title={npcReady ? undefined : 'Needs a party and at least one NPC'}
          onClick={() => { void run('npc'); }}
        >
          {running === 'npc' ? <Spinner label="Suggesting" /> : <Icon name="sparkle" size={11} />}
          {' '}Suggest NPC relations
        </button>
      </div>

      {arcId && (
        <div className="arc-inline-actions">
          <button
            type="button"
            className="ghost-btn"
            disabled={running !== null || !partyReady}
            onClick={() => { void queue('party'); }}
          >
            Queue party run
          </button>
          <button
            type="button"
            className="ghost-btn"
            disabled={running !== null || !npcReady}
            onClick={() => { void queue('npc'); }}
          >
            Queue NPC run
          </button>
          <span className="arc-hint">
            Runs on the host, so you can leave this screen.
          </span>
        </div>
      )}

      {progress && (
        <div className="arc-progress">
          <div className="arc-progress-bar">
            <span style={{ width: `${(progress.done / Math.max(progress.total, 1)) * 100}%` }} />
          </div>
          <p className="arc-hint">
            {progress.current
              ? `Asking about ${progress.current} (${progress.done + 1} of ${progress.total})`
              : `Merging ${progress.total} batches`}
            {' '}- one model call per character, so this takes a few minutes.
          </p>
        </div>
      )}

      {error && <p className="arc-error">{error}</p>}
      {notice && !running && <p className="arc-saved">{notice}</p>}
    </div>
  );
}
