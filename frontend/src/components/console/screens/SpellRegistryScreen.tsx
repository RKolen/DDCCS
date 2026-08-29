/**
 * SpellRegistryScreen — `spells/sp-list`.
 *
 * Filterable catalogue of Drupal spell nodes. A row jumps to Read Spell
 * with ctx.spellIdx set, the same way the loot vault jumps to the item sheet.
 */

import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { SpellCard } from '../../molecules/SpellCard';
import { levelLabel, schoolName } from '../../../types/spell';

interface ListNode {
  id: string;
  title: string;
  path: string | null;
  spellLevel: number;
  castingTime: string | null;
  spellRange: string | null;
  concentration: boolean | null;
  ritual: boolean | null;
  spellSchool: { name: string | null } | null;
}

interface ListQuery {
  drupal: { nodeSpells: { nodes: ListNode[] } };
}

export function SpellRegistryScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useStaticQuery<ListQuery>(graphql`
    query ConsoleSpellsList {
      drupal {
        nodeSpells(first: 100) {
          nodes {
            id title path spellLevel castingTime spellRange concentration ritual
            spellSchool { ... on Drupal_TermSpellSchool { name } }
          }
        }
      }
    }
  `);

  const nodes = data?.drupal?.nodeSpells?.nodes ?? [];
  const [search, setSearch] = React.useState('');
  const [levels, setLevels] = React.useState<Set<number>>(new Set());
  const [ritualOnly, setRitualOnly] = React.useState(false);
  const [concOnly, setConcOnly] = React.useState(false);

  const counts = React.useMemo(() => {
    const c: Partial<Record<number, number>> = {};
    nodes.forEach(node => {
      c[node.spellLevel] = (c[node.spellLevel] ?? 0) + 1;
    });
    return c;
  }, [nodes]);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return nodes
      .map((node, origIdx) => ({ node, origIdx }))
      .filter(({ node }) => {
        if (levels.size > 0 && !levels.has(node.spellLevel)) return false;
        if (ritualOnly && node.ritual !== true) return false;
        if (concOnly && node.concentration !== true) return false;
        if (q !== '' && !node.title.toLowerCase().includes(q)) return false;
        return true;
      });
  }, [nodes, search, levels, ritualOnly, concOnly]);

  const toggleLevel = (level: number): void => {
    const next = new Set(levels);
    if (next.has(level)) next.delete(level);
    else next.add(level);
    setLevels(next);
  };

  const openSpell = (origIdx: number): void => {
    setCtx({
      ...ctx,
      spellIdx: origIdx,
      _jumpTo: { sectionId: 'spells', itemId: 'sp-read' },
    });
  };

  if (nodes.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Spells</span>
            <h2>Spell Compendium</h2>
            <p className="screen-blurb">No spells in Drupal yet.</p>
          </div>
          <div className="screen-head-actions">
            <button
              type="button"
              className="ghost-btn"
              onClick={() => setCtx({
                ...ctx,
                _jumpTo: { sectionId: 'spells', itemId: 'sp-search' },
              })}
            >
              <Icon name="search" size={12} /> Search wiki
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={() => setCtx({
                ...ctx,
                _jumpTo: { sectionId: 'spells', itemId: 'sp-create' },
              })}
            >
              <Icon name="plus" size={11} /> Custom spell
            </button>
          </div>
        </header>
        <p className="screen-blurb">
          Search the rules wiki for an official spell, or create a homebrew
          entry. Either path writes a Spell node.
        </p>
      </div>
    );
  }

  const usedLevels = Object.keys(counts)
    .map(key => Number(key))
    .sort((a, b) => a - b);

  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Spells</span>
          <h2>Spell Compendium</h2>
          <p className="screen-blurb">
            {filtered.length} of {nodes.length} spell{nodes.length === 1 ? '' : 's'}
          </p>
        </div>
        <div className="screen-head-actions">
          <button
            type="button"
            className="ghost-btn"
            onClick={() => setCtx({
              ...ctx,
              _jumpTo: { sectionId: 'spells', itemId: 'sp-search' },
            })}
          >
            <Icon name="search" size={12} /> Search wiki
          </button>
          <button
            type="button"
            className="primary-btn"
            onClick={() => setCtx({
              ...ctx,
              _jumpTo: { sectionId: 'spells', itemId: 'sp-create' },
            })}
          >
            <Icon name="plus" size={11} /> Custom spell
          </button>
        </div>
      </header>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        <div className="search-field" style={{ flex: 1, minWidth: 220, maxWidth: 360 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder="Search spells..."
            value={search}
            onChange={event => setSearch(event.target.value)}
          />
        </div>
        {usedLevels.map(level => (
          <button
            key={level}
            type="button"
            className="filter-chip"
            data-active={levels.has(level) || undefined}
            onClick={() => toggleLevel(level)}
          >
            {levelLabel(level)} · {counts[level]}
          </button>
        ))}
        <button
          type="button"
          className="filter-chip"
          data-active={concOnly || undefined}
          onClick={() => setConcOnly(value => !value)}
        >
          Concentration
        </button>
        <button
          type="button"
          className="filter-chip"
          data-active={ritualOnly || undefined}
          onClick={() => setRitualOnly(value => !value)}
        >
          Ritual
        </button>
      </div>

      {filtered.length === 0 ? (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          No spells match those filters.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(({ node, origIdx }) => (
            <SpellCard
              key={node.id}
              name={node.title}
              level={node.spellLevel}
              school={schoolName(node.spellSchool)}
              concentration={node.concentration === true}
              ritual={node.ritual === true}
              description={[node.castingTime, node.spellRange].filter(Boolean).join(' · ')}
              onClick={() => openSpell(origIdx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
