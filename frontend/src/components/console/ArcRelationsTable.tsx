/**
 * Editable table of arc relationships, shared by the arc overview and the
 * character sheet's Relations tab. Rows may be filtered to one character; the
 * hook behind it still saves the whole side.
 */

import * as React from 'react';
import { Icon } from './atoms';
import type { DrupalCharacter } from './ConsoleContext';
import type { EditableRelation, RelationSide } from '../../utils/arcRelationsEdit';

const TIERS = [1, 2, 3] as const;
const TIER_TITLE: Record<number, string> = {
  1: 'Direct and personal',
  2: 'Thematic',
  3: 'Incidental',
};

export interface ArcRelationsTableProps {
  side:     RelationSide;
  rows:     EditableRelation[];
  /** Characters selectable as either end. */
  roster:   DrupalCharacter[];
  onUpdate: (side: RelationSide, key: string, patch: Partial<EditableRelation>) => void;
  onRemove: (side: RelationSide, key: string) => void;
  onAdd?:   (side: RelationSide) => void;
  empty:    string;
}

export function ArcRelationsTable({
  side, rows, roster, onUpdate, onRemove, onAdd, empty,
}: ArcRelationsTableProps): React.ReactElement {
  return (
    <div className="arc-rel-table">
      {rows.length === 0 ? (
        <p className="arc-empty">{empty}</p>
      ) : (
        <ul className="arc-rel-rows">
          {rows.map(row => (
            <li key={row.key}>
              <div className="arc-rel-line">
                <select
                  value={row.sourceId ?? ''}
                  aria-label="Source character"
                  onChange={e => onUpdate(side, row.key, {
                    sourceId:   e.target.value,
                    sourceName: roster.find(c => c.id === e.target.value)?.title ?? null,
                  })}
                >
                  <option value="">(choose)</option>
                  {roster.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                </select>

                <span className="arc-rel-arrow">-&gt;</span>

                <select
                  value={row.targetId ?? ''}
                  aria-label="Target character"
                  onChange={e => onUpdate(side, row.key, {
                    targetId:   e.target.value,
                    targetName: roster.find(c => c.id === e.target.value)?.title ?? null,
                  })}
                >
                  <option value="">(choose)</option>
                  {roster.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                </select>

                <input
                  type="text"
                  className="arc-rel-type-input"
                  aria-label="Relationship type"
                  placeholder="sworn protector"
                  value={row.type ?? ''}
                  onChange={e => onUpdate(side, row.key, { type: e.target.value })}
                />

                <select
                  value={row.tier ?? ''}
                  aria-label="Tier"
                  title={row.tier ? TIER_TITLE[row.tier] : 'Narrative weight'}
                  onChange={e => onUpdate(side, row.key, {
                    tier: e.target.value === '' ? null : Number(e.target.value),
                  })}
                >
                  <option value="">T-</option>
                  {TIERS.map(t => <option key={t} value={t}>T{t}</option>)}
                </select>

                <button
                  type="button"
                  className="ghost-btn arc-rel-delete"
                  title="Remove this relation"
                  onClick={() => onRemove(side, row.key)}
                >
                  <Icon name="close" size={11} />
                </button>
              </div>

              <textarea
                className="arc-rel-note-input"
                aria-label="Note"
                rows={2}
                placeholder="The connection, and how it can be used in play."
                value={row.note ?? ''}
                onChange={e => onUpdate(side, row.key, { note: e.target.value })}
              />
            </li>
          ))}
        </ul>
      )}

      {onAdd && (
        <button type="button" className="ghost-btn" onClick={() => onAdd(side)}>
          <Icon name="plus" size={11} /> Add relation
        </button>
      )}
    </div>
  );
}
