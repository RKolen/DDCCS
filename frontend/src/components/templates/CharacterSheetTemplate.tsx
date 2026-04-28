import React, { useState } from 'react';
import { Divider } from '../atoms/Divider';
import * as styles from './CharacterSheetTemplate.module.css';

type TabKey = 'stats' | 'skills' | 'spells' | 'equipment';

interface CharacterSheetTemplateProps {
  header: React.ReactNode;
  stats: React.ReactNode;
  spellSlots?: React.ReactNode;
  skills: React.ReactNode;
  spells?: React.ReactNode;
  equipment: React.ReactNode;
}

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'stats',     label: 'Stats'     },
  { key: 'skills',    label: 'Skills'    },
  { key: 'spells',    label: 'Spells'    },
  { key: 'equipment', label: 'Equipment' },
];

export function CharacterSheetTemplate({
  header,
  stats,
  spellSlots,
  skills,
  spells,
  equipment,
}: CharacterSheetTemplateProps): React.ReactElement {
  const [tab, setTab] = useState<TabKey>('stats');

  return (
    <div className={styles.page}>
      {header}
      <Divider icon="crossed-swords" />

      <div className={styles.tabBar}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`${styles.tabBtn}${tab === t.key ? ` ${styles.tabBtnActive}` : ''}`}
          >
            {t.label.toUpperCase()}
          </button>
        ))}
      </div>

      {tab === 'stats' && (
        <div className={styles.statsGrid}>
          <div>{stats}</div>
          {spellSlots && <div>{spellSlots}</div>}
        </div>
      )}
      {tab === 'skills' && skills}
      {tab === 'spells' && (
        spells ?? (
          <p className={styles.empty}>No spells known.</p>
        )
      )}
      {tab === 'equipment' && equipment}
    </div>
  );
}
