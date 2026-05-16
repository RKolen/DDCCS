import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Badge } from '../components/atoms/Badge';
import { Divider } from '../components/atoms/Divider';
import { GameIcon } from '../components/atoms/GameIcon';
import * as styles from './index.module.css';

interface CharacterNode {
  id: string;
  title: string;
  level: number | null;
  armorClass: number | null;
  maximumHitpoints: number | null;
  path: string | null;
}

interface StoryNode {
  id: string;
  title: string;
  storyNumber: number | null;
  path: string | null;
}

interface DashboardData {
  drupal: {
    nodeCharacters: { nodes: CharacterNode[] };
    nodeStories: { nodes: StoryNode[] };
  };
}

interface CharacterCardProps {
  char: CharacterNode;
}

function CharacterCard({ char }: CharacterCardProps): React.ReactElement {
  const hp = char.maximumHitpoints ?? 0;
  const href = char.path ?? '#';

  return (
    <Link to={href} className={styles.charCard}>
      <div className={styles.charCardTop}>
        <div className={styles.charCardIdent}>
          <GameIcon name="crossed-swords" size={24} colorFilter="var(--filter-gold-dim)" decorative />
          <span className={styles.charName}>{char.title}</span>
        </div>
        <span className={styles.charAc}>AC {char.armorClass ?? '—'}</span>
      </div>
      <div className={styles.charBadges}>
        {char.level !== null && <Badge label={`Lv ${char.level}`} size="sm" />}
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
  const characters = data.drupal.nodeCharacters.nodes;
  const stories = data.drupal.nodeStories.nodes;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Campaign Dashboard</h1>
          {characters.length > 0 && (
            <p className={styles.subtitle}>
              {characters.length} {characters.length === 1 ? 'adventurer' : 'adventurers'} &middot; {stories.length} {stories.length === 1 ? 'session' : 'sessions'} recorded
            </p>
          )}
        </header>

        <div className={styles.grid}>
          <section>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Character Database, total: {characters.length}</h3>
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
                    to={s.path ?? '#'}
                    className={`${styles.sessionRow} ${i === 0 ? styles.sessionFirst : ''} ${i === stories.length - 1 ? styles.sessionLast : ''}`}
                  >
                    <GameIcon name="scroll-unfurled" size={16} colorFilter="var(--filter-gold-dim)" decorative />
                    <div className={styles.sessionInfo}>
                      <span className={styles.sessionTitle}>{s.title}</span>
                      {s.storyNumber !== null && (
                        <span className={styles.sessionMeta}>Session {s.storyNumber}</span>
                      )}
                    </div>
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
    drupal {
      nodeCharacters(first: 20) {
        nodes {
          id
          title
          level
          armorClass
          maximumHitpoints
          path
        }
      }
      nodeStories(first: 3) {
        nodes {
          id
          title
          storyNumber
          path
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Dashboard | D&D Consultant</title>;

export default IndexPage;
