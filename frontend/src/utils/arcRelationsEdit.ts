/**
 * Editing state and the single save path for both relation editors.
 *
 * Saving replaces a whole side of an arc, so the hook holds both sides in full
 * even when the caller shows only one character's rows. It keeps its own state
 * after a save: page data is build-time and would revert the write.
 */

import * as React from 'react';
import type { DrupalArcRelation, DrupalStoryArc } from '../components/console/ConsoleContext';
import type { ArcRelationPayload, ArcRelationTier } from './arcPayload';

export type RelationSide = 'party' | 'npc';

/** A relation being edited, with a stable key for React and for row identity. */
export interface EditableRelation extends DrupalArcRelation {
  key: string;
}

export interface ArcRelationsState {
  party: EditableRelation[];
  npc:   EditableRelation[];
  saving: boolean;
  error:  string | null;
  notice: string | null;
  add:    (side: RelationSide, relation: DrupalArcRelation) => void;
  update: (side: RelationSide, key: string, patch: Partial<DrupalArcRelation>) => void;
  remove: (side: RelationSide, key: string) => void;
  save:   () => Promise<void>;
}

let keySeed = 0;

function withKeys(rels: DrupalArcRelation[]): EditableRelation[] {
  return rels.map(r => {
    keySeed += 1;
    return { ...r, key: `rel-${keySeed}` };
  });
}

function toPayload(rels: EditableRelation[]): ArcRelationPayload[] {
  return rels
    .filter(r => r.sourceId && r.targetId)
    .map(r => ({
      source: r.sourceId as string,
      target: r.targetId as string,
      type:   r.type ?? '',
      tier:   (r.tier ?? undefined) as ArcRelationTier | undefined,
      note:   r.note ?? '',
    }));
}

/**
 * Hold and save one arc's relations.
 *
 * @param arc
 *   The arc being edited, or null when nothing is selected.
 */
export function useArcRelations(arc: DrupalStoryArc | null): ArcRelationsState {
  const [party, setParty]   = React.useState<EditableRelation[]>([]);
  const [npc, setNpc]       = React.useState<EditableRelation[]>([]);
  const [saving, setSaving] = React.useState(false);
  const [error, setError]   = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  /* Reload on arc change only; a re-render from the save must not discard edits. */
  const arcId = arc?.id ?? null;
  const loadedFor = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (loadedFor.current === arcId) {
      return;
    }
    loadedFor.current = arcId;
    setParty(withKeys(arc?.partyRelations ?? []));
    setNpc(withKeys(arc?.npcRelations ?? []));
    setError(null);
    setNotice(null);
  }, [arcId, arc]);

  const setter = (side: RelationSide): React.Dispatch<React.SetStateAction<EditableRelation[]>> =>
    (side === 'party' ? setParty : setNpc);

  const add = React.useCallback((side: RelationSide, relation: DrupalArcRelation): void => {
    keySeed += 1;
    const row: EditableRelation = { ...relation, key: `rel-${keySeed}` };
    setter(side)(rows => [...rows, row]);
    setNotice(null);
  }, []);

  const update = React.useCallback(
    (side: RelationSide, key: string, patch: Partial<DrupalArcRelation>): void => {
      setter(side)(rows => rows.map(r => (r.key === key ? { ...r, ...patch } : r)));
      setNotice(null);
    }, []);

  const remove = React.useCallback((side: RelationSide, key: string): void => {
    setter(side)(rows => rows.filter(r => r.key !== key));
    setNotice(null);
  }, []);

  const save = React.useCallback(async (): Promise<void> => {
    if (!arcId) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch('/api/save-arc-relations', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          id:        arcId,
          relations: { party: toPayload(party), npc: toPayload(npc) },
        }),
      });
      const payload = (await res.json()) as {
        partySaved?: number; npcSaved?: number; error?: string;
      };
      if (!res.ok || payload.error) {
        throw new Error(payload.error ?? `Request failed (${res.status})`);
      }
      const sent = toPayload(party).length + toPayload(npc).length;
      const kept = (payload.partySaved ?? 0) + (payload.npcSaved ?? 0);
      setNotice(
        kept === sent
          ? `Saved ${kept} relation${kept === 1 ? '' : 's'}.`
          : `Saved ${kept} of ${sent}; the rest could not be matched to characters.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }, [arcId, party, npc]);

  return { party, npc, saving, error, notice, add, update, remove, save };
}
