/**
 * Review, edit, and accept a drafted story arc.
 *
 * The model proposes; the operator decides. Every field is editable and both
 * rosters are ticked by hand before anything is written, so an arc is never
 * created from text nobody read - the same accept/reject contract a queued
 * portrait and a suggested relation already use.
 *
 * Level range and target-story count are deliberately not here. Both stay
 * fluid for the life of an arc, so they are set in the arc editor rather than
 * guessed at from what has already been played.
 */

import * as React from 'react';
import { Icon, Spinner } from './atoms';
import type { DrupalCharacter } from './ConsoleContext';
import type { ArcDraft, DiscoveredNpc } from '../../utils/arcBackfill';

export interface ArcDraftReviewProps {
  draft: ArcDraft;
  party: DrupalCharacter[];
  /** NPCs the sessions name, known and missing alike. */
  cast:  DiscoveredNpc[];
  /** NPCs already on record, used to resolve the known half of the cast. */
  npcs:  DrupalCharacter[];
  /** Called with the edited draft, the ticked party, and the ticked cast. */
  onAccept: (
    draft: ArcDraft,
    partyIds: string[],
    knownNpcIds: string[],
    createNpcs: DiscoveredNpc[],
  ) => Promise<void>;
  onDiscard: () => void;
}

/** Index a roster by lowercased title, for matching model-written names. */
function idByTitle(roster: DrupalCharacter[]): Map<string, string> {
  return new Map(roster.map(c => [c.title.toLowerCase(), c.id]));
}

/** Match names to roster ids by exact title, dropping the unmatched. */
function idsForNames(names: string[], index: Map<string, string>): Set<string> {
  const ids = new Set<string>();
  for (const name of names) {
    const id = index.get(name.trim().toLowerCase());
    if (id) {
      ids.add(id);
    }
  }
  return ids;
}

export function ArcDraftReview({
  draft, party, cast, npcs, onAccept, onDiscard,
}: ArcDraftReviewProps): React.ReactElement {
  const [title, setTitle]             = React.useState(draft.title);
  const [premise, setPremise]         = React.useState(draft.premise);
  const [overallPlot, setOverallPlot] = React.useState(draft.overallPlot);
  const [faction, setFaction]         = React.useState(draft.faction);

  const [partyIds, setPartyIds] = React.useState(
    () => idsForNames(draft.party, idByTitle(party)),
  );

  /* The cast splits by whether a character node exists. Known NPCs are ticked
     into the arc; missing ones are ticked to be created and then included. */
  const npcIndex = React.useMemo(() => idByTitle(npcs), [npcs]);
  const known   = React.useMemo(() => cast.filter(n => n.known), [cast]);
  const missing = React.useMemo(() => cast.filter(n => !n.known), [cast]);

  const [knownIds, setKnownIds] = React.useState(
    () => idsForNames(known.map(n => n.name), npcIndex),
  );
  const [toCreate, setToCreate] = React.useState<Set<string>>(
    () => new Set(missing.map(n => n.name)),
  );

  const [busy, setBusy]   = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function toggleIn<T>(set: Set<T>, apply: (next: Set<T>) => void, value: T): void {
    const next = new Set(set);
    if (next.has(value)) {
      next.delete(value);
    } else {
      next.add(value);
    }
    apply(next);
  }

  async function accept(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await onAccept(
        {
          title:       title.trim(),
          premise:     premise.trim(),
          overallPlot: overallPlot.trim(),
          faction:     faction.trim(),
          party:       draft.party,
          npcs:        draft.npcs,
        },
        Array.from(partyIds),
        Array.from(knownIds),
        missing.filter(n => toCreate.has(n.name)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="arc-preview arc-draft-review">
      <h4>Proposed arc</h4>
      <p className="arc-hint">
        Read from the sessions this campaign has already played. Nothing is
        written until you accept it, and every field here is yours to change
        first. Levels and story count are set later, in the arc itself.
      </p>

      {error && <p className="arc-error">{error}</p>}

      <label className="form-row">
        <span>Arc title</span>
        <input type="text" value={title} onChange={e => setTitle(e.target.value)} />
      </label>

      <label className="form-row">
        <span>Premise</span>
        <textarea
          className="arc-textarea"
          rows={4}
          value={premise}
          onChange={e => setPremise(e.target.value)}
        />
      </label>

      <label className="form-row">
        <span>Act spine</span>
        <textarea
          className="arc-textarea"
          rows={5}
          value={overallPlot}
          onChange={e => setOverallPlot(e.target.value)}
        />
      </label>

      <label className="form-row">
        <span>Antagonist faction</span>
        <input
          type="text"
          value={faction}
          onChange={e => setFaction(e.target.value)}
          placeholder="Left empty if none was identified"
        />
      </label>

      <div className="form-row">
        <span>Party in this arc</span>
        {party.length === 0 ? (
          <p className="arc-empty">
            This campaign has no player characters on record. Add them to the
            campaign&apos;s party first.
          </p>
        ) : (
          <ul className="arc-picker">
            {party.map(p => (
              <li key={p.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={partyIds.has(p.id)}
                    onChange={() => toggleIn(partyIds, setPartyIds, p.id)}
                  />
                  <span className="arc-picker-name">{p.title}</span>
                  {p.characterClass && (
                    <span className="arc-picker-meta">{p.characterClass}</span>
                  )}
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="form-row">
        <span>NPCs named in the sessions</span>
        {cast.length === 0 ? (
          <p className="arc-empty">
            No NPCs were read out of the sessions. Add them to the arc by hand
            once it exists.
          </p>
        ) : (
          <>
            {known.length > 0 && (
              <ul className="arc-picker">
                {known.map(npc => {
                  const id = npcIndex.get(npc.name.trim().toLowerCase());
                  return (
                    <li key={npc.name}>
                      <label>
                        <input
                          type="checkbox"
                          checked={id !== undefined && knownIds.has(id)}
                          disabled={id === undefined}
                          onChange={() => id && toggleIn(knownIds, setKnownIds, id)}
                        />
                        <span className="arc-picker-name">{npc.name}</span>
                        {npc.role && <span className="arc-picker-meta">{npc.role}</span>}
                      </label>
                    </li>
                  );
                })}
              </ul>
            )}

            {missing.length > 0 && (
              <>
                <p className="arc-hint">
                  These appear in the stories but have no character yet. Ticked
                  ones are created as NPCs on this campaign - a name and this
                  one line, nothing invented - and added to the arc.
                </p>
                <ul className="arc-picker">
                  {missing.map(npc => (
                    <li key={npc.name}>
                      <label>
                        <input
                          type="checkbox"
                          checked={toCreate.has(npc.name)}
                          onChange={() => toggleIn(toCreate, setToCreate, npc.name)}
                        />
                        <span className="arc-picker-name">{npc.name}</span>
                        {npc.role && <span className="arc-picker-meta">{npc.role}</span>}
                        <span className="arc-picker-tag">new</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </>
        )}
      </div>

      <div className="arc-inline-actions">
        <button
          type="button"
          className="primary-btn"
          disabled={busy || !title.trim()}
          onClick={() => { void accept(); }}
        >
          {busy ? <Spinner label="Creating" /> : <Icon name="scroll" size={11} />}
          {busy ? ' Creating' : ' Create this arc'}
        </button>
        <button type="button" className="ghost-btn" disabled={busy} onClick={onDiscard}>
          Discard draft
        </button>
      </div>
    </div>
  );
}
