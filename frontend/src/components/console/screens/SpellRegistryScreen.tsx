/**
 * SpellRegistryScreen — `spells/sp-list`.
 *
 * Filterable catalogue of Drupal spells-vocabulary terms. A row jumps to
 * Read Spell with ctx.spellIdx set, the same way the loot vault jumps to
 * the item sheet.
 */

import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { SpellCard } from '../../molecules/SpellCard';
import {
  levelLabel,
  schoolName,
  type SpellTermNode,
} from '../../../types/spell';
import '../../../graphql/spellTerm';

interface ListQuery {
  drupal: { termSpells: { nodes: SpellTermNode[] } };
}

export function SpellRegistryScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useStaticQuery<ListQuery>(graphql`
    query ConsoleSpellsList {
      drupal {
        termSpells(first: 500) {
          nodes {
            ...SpellTermFields
          }
        }
      }
    }
  `);

  const nodes = data?.drupal?.termSpells?.nodes ?? [];
  const [search, setSearch] = React.useState('');
  const [levels, setLevels] = React.useState<Set<number>>(new Set());
  const [schools, setSchools] = React.useState<Set<string>>(new Set());
  const [ritualOnly, setRitualOnly] = React.useState(false);
  const [concOnly, setConcOnly] = React.useState(false);

  const counts = React.useMemo(() => {
    const c: Partial<Record<number, number>> = {};
    nodes.forEach(node => {
      const level = node.spellLevel ?? 0;
      c[level] = (c[level] ?? 0) + 1;
    });
    return c;
  }, [nodes]);

  const schoolCounts = React.useMemo(() => {
    const c = new Map<string, number>();
    nodes.forEach(node => {
      const name = schoolName(node.spellSchool);
      if (name == null) return;
      c.set(name, (c.get(name) ?? 0) + 1);
    });
    return Array.from(c.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [nodes]);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return nodes
      .map((node, origIdx) => ({ node, origIdx }))
      .filter(({ node }) => {
        const level = node.spellLevel ?? 0;
        if (levels.size > 0 && !levels.has(level)) return false;
        const school = schoolName(node.spellSchool);
        if (schools.size > 0 && (school == null || !schools.has(school))) {
          return false;
        }
        if (ritualOnly && node.spellRitual !== true) return false;
        if (concOnly && node.spellConcentration !== true) return false;
        if (q !== '' && !node.name.toLowerCase().includes(q)) return false;
        return true;
      });
  }, [nodes, search, levels, schools, ritualOnly, concOnly]);

  const toggleLevel = (level: number): void => {
    const next = new Set(levels);
    if (next.has(level)) next.delete(level);
    else next.add(level);
    setLevels(next);
  };

  const toggleSchool = (name: string): void => {
    const next = new Set(schools);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setSchools(next);
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
          entry. Either path writes a spells-vocabulary term.
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
        {schoolCounts.map(([name, count]) => (
          <button
            key={name}
            type="button"
            className="filter-chip"
            data-active={schools.has(name) || undefined}
            onClick={() => toggleSchool(name)}
          >
            {name} · {count}
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
              name={node.name}
              level={node.spellLevel ?? 0}
              school={schoolName(node.spellSchool)}
              concentration={node.spellConcentration === true}
              ritual={node.spellRitual === true}
              description={[node.spellCastingTime, node.spellRange].filter(Boolean).join(' · ')}
              onClick={() => openSpell(origIdx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
