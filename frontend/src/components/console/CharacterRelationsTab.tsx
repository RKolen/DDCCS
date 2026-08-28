/**
 * Arc relationships seen from one character's side, across every arc they
 * appear in. Editing is per-arc, because that is the unit the mutation
 * replaces.
 */

import * as React from 'react';
import { useConsoleData, relationsForCharacter } from './ConsoleContext';
import type { DrupalCharacter, DrupalStoryArc } from './ConsoleContext';
import { Icon, Spinner } from './atoms';
import { ArcRelationsTable } from './ArcRelationsTable';
import { useArcRelations } from '../../utils/arcRelationsEdit';
import { partyRoster, npcRoster } from '../../utils/arcRoster';

export function CharacterRelationsTab({ char }: { char: DrupalCharacter }): React.ReactElement {
  const data = useConsoleData();

  /* Arcs this character appears in, as a member or in a bond. */
  const arcs = React.useMemo<DrupalStoryArc[]>(() => {
    const touching = new Set(relationsForCharacter(data, char.id).map(r => r.arc.id));
    return data.storyArcs.filter(a =>
      touching.has(a.id) || a.partyIds.includes(char.id) || a.npcIds.includes(char.id));
  }, [data, char.id]);

  const [arcId, setArcId] = React.useState<string | null>(null);
  const active = arcs.find(a => a.id === arcId) ?? arcs[0] ?? null;

  const rel = useArcRelations(active);

  const campaignName = active?.campaign ?? char.campaign ?? null;
  const party = React.useMemo(() => partyRoster(data, campaignName), [data, campaignName]);
  const npcs  = React.useMemo(() => npcRoster(data, campaignName), [data, campaignName]);
  const everyone = React.useMemo(() => [...party, ...npcs], [party, npcs]);

  /* Show only this character's rows; the hook still holds and saves the rest. */
  const mine = React.useCallback(
    <T extends { sourceId: string | null; targetId: string | null }>(rows: T[]): T[] =>
      rows.filter(r => r.sourceId === char.id || r.targetId === char.id),
    [char.id],
  );

  const partyRows = mine(rel.party);
  const npcRows   = mine(rel.npc);

  if (arcs.length === 0) {
    return (
      <p className="arc-empty">
        {char.title} is not part of any story arc yet. Add them to an arc&apos;s party
        or NPC roster, or record a relationship on the arc overview.
      </p>
    );
  }

  return (
    <div className="char-relations">
      {arcs.length > 1 && (
        <div className="arc-tab-row">
          {arcs.map(a => (
            <button
              key={a.id}
              type="button"
              className={`arc-tab${a.id === active?.id ? ' active' : ''}`}
              onClick={() => setArcId(a.id)}
            >
              {a.title}
            </button>
          ))}
        </div>
      )}

      <section className="arc-prose">
        <h4>Within the party</h4>
        <ArcRelationsTable
          side="party"
          rows={partyRows}
          roster={party}
          onUpdate={rel.update}
          onRemove={rel.remove}
          empty={`No party bonds recorded for ${char.title} in this arc.`}
        />
      </section>

      <section className="arc-prose">
        <h4>With NPCs</h4>
        <ArcRelationsTable
          side="npc"
          rows={npcRows}
          roster={everyone}
          onUpdate={rel.update}
          onRemove={rel.remove}
          empty={`No NPC connections recorded for ${char.title} in this arc.`}
        />
      </section>

      {rel.error && <p className="arc-error">{rel.error}</p>}
      {rel.notice && <p className="arc-saved">{rel.notice}</p>}

      <p className="arc-hint">
        Saving writes the whole arc, including bonds not shown here.
      </p>
      <div className="wizard-foot">
        <button
          type="button"
          className="primary-btn"
          disabled={rel.saving}
          onClick={() => { void rel.save(); }}
        >
          {rel.saving ? <Spinner label="Saving" /> : <Icon name="scroll" size={11} />}
          {rel.saving ? ' Saving' : ' Save relations'}
        </button>
      </div>
    </div>
  );
}
