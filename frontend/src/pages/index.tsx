import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Badge } from '../components/atoms/Badge';
import { Divider } from '../components/atoms/Divider';
import { GameIcon } from '../components/atoms/GameIcon';
import type { GameIconName } from '../types/icons';
import * as styles from './index.module.css';

interface CharacterNode {
  id:                    string;
  title:                 string;
  fieldLevel:            number | null;
  fieldArmorClass:       number | null;
  fieldMaximumHitpoints: number | null;
  fieldMovementSpeed:    number | null;
  fieldSpecies:          Array<{ name: string }> | null;
  fieldClass:            Array<{ fieldClass: Array<{ name: string }> | null }> | null;
  path:                  { alias: string } | null;
}

interface StoryNode {
  id:               string;
  title:            string;
  fieldStoryNumber: number | null;
  fieldStoryHooks:  Array<{ value: string }> | null;
  path:             { alias: string } | null;
}

interface DashboardData {
  allNodeCharacter: { nodes: CharacterNode[] };
  allNodeStory:     { nodes: StoryNode[] };
}

const CLASS_ICONS: Record<string, GameIconName> = {
  Wizard:    'cowled',
  Ranger:    'crossed-swords',
  Rogue:     'hood',
  Fighter:   'knight-helmet',
  Paladin:   'knight-helmet',
  Cleric:    'holy-grail',
  Bard:      'scroll-unfurled',
  Druid:     'eye',
  Monk:      'muscle-up',
  Warlock:   'crystal-ball',
  Sorcerer:  'magic-swirl',
  Barbarian: 'broadsword',
};

const DEFAULT_ICON: GameIconName = 'crossed-swords';

interface CharacterCardProps {
  char: CharacterNode;
}

function CharacterCard({ char }: CharacterCardProps): React.ReactElement {
  const clsName   = char.fieldClass?.[0]?.fieldClass?.[0]?.name ?? 'Adventurer';
  const icon      = CLASS_ICONS[clsName] ?? DEFAULT_ICON;
  const species   = char.fieldSpecies?.[0]?.name ?? '';
  const hp        = char.fieldMaximumHitpoints ?? 0;
  const href      = char.path?.alias ?? `#`;

  return (
    <Link to={href} className={styles.charCard}>
      <div className={styles.charCardTop}>
        <div className={styles.charCardIdent}>
          <GameIcon name={icon} size={24} colorFilter="var(--filter-gold-dim)" decorative />
          <span className={styles.charName}>{char.title}</span>
        </div>
        <span className={styles.charAc}>AC {char.fieldArmorClass ?? '—'}</span>
      </div>
      <div className={styles.charBadges}>
        <Badge label={clsName} variant="class" size="sm" />
        {char.fieldLevel && <Badge label={`Lv ${char.fieldLevel}`} size="sm" />}
        {species && <Badge label={species} size="sm" />}
      </div>
      <div className={styles.hpRow}>
        <GameIcon name="heart-beats" size={14} colorFilter="var(--filter-green)" decorative />
        <div className={styles.hpBar}>
          <div className={styles.hpFill} />
        </div>
        <span className={styles.hpLabel}>{hp}/{hp}</span>
      </div>
    </Link>
  );
}

const IndexPage: React.FC<PageProps<DashboardData>> = ({ data, location }) => {
  const characters = data.allNodeCharacter.nodes;
  const stories    = data.allNodeStory.nodes;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Campaign Dashboard</h1>
          <p className={styles.subtitle}>New Beginnings — Dragon Heist Campaign</p>
        </header>

        <div className={styles.grid}>
          <section>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Active Party</h3>
              <Link to="/characters" className={styles.sectionLink}>Manage</Link>
            </div>
            <div className={styles.charList}>
              {characters.length > 0 ? (
                characters.map(c => <CharacterCard key={c.id} char={c} />)
              ) : (
                <p className={styles.empty}>No characters yet.</p>
              )}
            </div>
          </section>

          <section>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Recent Sessions</h3>
              <Link to="/stories" className={styles.sectionLink}>All Stories</Link>
            </div>
            <div className={styles.sessionList}>
              {stories.length > 0 ? (
                stories.map((s, i) => (
                  <Link
                    key={s.id}
                    to={s.path?.alias ?? '#'}
                    className={`${styles.sessionRow} ${i === 0 ? styles.sessionFirst : ''} ${i === stories.length - 1 ? styles.sessionLast : ''}`}
                  >
                    <GameIcon name="scroll-unfurled" size={16} colorFilter="var(--filter-gold-dim)" decorative />
                    <div className={styles.sessionInfo}>
                      <span className={styles.sessionTitle}>{s.title}</span>
                      {s.fieldStoryNumber && (
                        <span className={styles.sessionMeta}>Session {s.fieldStoryNumber}</span>
                      )}
                    </div>
                    {s.fieldStoryHooks && s.fieldStoryHooks.length > 0 && (
                      <Badge label={`${s.fieldStoryHooks.length} hooks`} variant="school" size="sm" />
                    )}
                  </Link>
                ))
              ) : (
                <p className={styles.empty}>No stories yet.</p>
              )}
            </div>

            <div className={styles.actions}>
              <Divider icon="stars-stack" />
              <div className={styles.actionButtons}>
                <Link to="/search" className={styles.actionBtn}>
                  <GameIcon name="crystal-ball" size={14} colorFilter="var(--filter-gold)" decorative />
                  Search Lore
                </Link>
                <Link to="/npcs" className={styles.actionBtn}>
                  <GameIcon name="swap-bag" size={14} colorFilter="var(--filter-gold)" decorative />
                  NPC Registry
                </Link>
              </div>
            </div>
          </section>
        </div>
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query Dashboard {
    allNodeCharacter {
      nodes {
        id
        title
        fieldLevel
        fieldArmorClass
        fieldMaximumHitpoints
        fieldMovementSpeed
        fieldSpecies { name }
        fieldClass {
          ... on paragraph__class {
            fieldClass { name }
          }
        }
        path { alias }
      }
    }
    allNodeStory(limit: 3, sort: { fieldStoryNumber: DESC }) {
      nodes {
        id
        title
        fieldStoryNumber
        fieldStoryHooks { value }
        path { alias }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Dashboard | D&D Consultant</title>;

export default IndexPage;
