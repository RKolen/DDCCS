import React, { useState, useMemo } from 'react';
import { SpellCard } from '../molecules/SpellCard';
import type { SpellSchool } from '../molecules/SpellCard';
import * as styles from './SpellList.module.css';

export interface SpellData {
  name: string;
  level: number;
  school: SpellSchool;
  concentration?: boolean;
  description?: string;
}

interface SpellListProps {
  spells: SpellData[];
  groupByLevel?: boolean;
}

const SCHOOLS: SpellSchool[] = [
  'Abjuration', 'Conjuration', 'Divination', 'Enchantment',
  'Evocation', 'Illusion', 'Necromancy', 'Transmutation',
];

const LEVEL_LABELS: Record<number, string> = {
  0: 'Cantrips', 1: '1st Level', 2: '2nd Level', 3: '3rd Level',
  4: '4th Level', 5: '5th Level', 6: '6th Level', 7: '7th Level',
  8: '8th Level', 9: '9th Level',
};

export function SpellList({ spells, groupByLevel = true }: SpellListProps): React.ReactElement {
  const [activeSchool, setActiveSchool] = useState<SpellSchool | null>(null);

  const visibleSchools = useMemo(
    () => SCHOOLS.filter(s => spells.some(sp => sp.school === s)),
    [spells],
  );

  const filtered = useMemo(
    () => activeSchool ? spells.filter(sp => sp.school === activeSchool) : spells,
    [spells, activeSchool],
  );

  const sorted = useMemo(
    () => [...filtered].sort((a, b) => a.level - b.level || a.name.localeCompare(b.name)),
    [filtered],
  );

  const groups = useMemo(() => {
    if (!groupByLevel || activeSchool) return null;
    const map = new Map<number, SpellData[]>();
    for (const sp of sorted) {
      if (!map.has(sp.level)) map.set(sp.level, []);
      map.get(sp.level)!.push(sp);
    }
    return map;
  }, [sorted, groupByLevel, activeSchool]);

  return (
    <div className={styles.container}>
      {visibleSchools.length > 1 && (
        <div className={styles.header}>
          <span className={styles.title}>Spells</span>
          <div className={styles.filters} role="group" aria-label="Filter by school">
            <button
              className={`${styles.filterBtn}${activeSchool === null ? ` ${styles.filterBtnActive}` : ''}`}
              onClick={() => setActiveSchool(null)}
            >
              All
            </button>
            {visibleSchools.map(school => (
              <button
                key={school}
                className={`${styles.filterBtn}${activeSchool === school ? ` ${styles.filterBtnActive}` : ''}`}
                onClick={() => setActiveSchool(school === activeSchool ? null : school)}
              >
                {school}
              </button>
            ))}
          </div>
        </div>
      )}

      {sorted.length === 0 && (
        <p className={styles.empty}>No spells found.</p>
      )}

      {groups ? (
        Array.from(groups.entries()).map(([level, levelSpells]) => (
          <div key={level} className={styles.group}>
            <span className={styles.groupLabel}>{LEVEL_LABELS[level] ?? `Level ${level}`}</span>
            <div className={styles.list}>
              {levelSpells.map(sp => (
                <SpellCard key={sp.name} {...sp} />
              ))}
            </div>
          </div>
        ))
      ) : (
        <div className={styles.list}>
          {sorted.map(sp => (
            <SpellCard key={sp.name} {...sp} />
          ))}
        </div>
      )}
    </div>
  );
}
