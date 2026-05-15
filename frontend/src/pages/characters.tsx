import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Badge } from '../components/atoms/Badge';
import { Divider } from '../components/atoms/Divider';
import { GameIcon } from '../components/atoms/GameIcon';
import * as styles from './characters.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CharacterNode {
  id:               string;
  title:            string;
  firstName:        string | null;
  level:            number | null;
  armorClass:       number | null;
  maximumHitpoints: number | null;
  path:             string | null;
}

interface CharactersData {
  drupal: {
    nodeCharacters: { nodes: CharacterNode[] };
  };
}

// ── Character card ────────────────────────────────────────────────────────────

interface CharacterCardProps {
  char: CharacterNode;
}

function CharacterCard({ char }: CharacterCardProps): React.ReactElement {
  const href = char.path ?? '#';

  const statParts: string[] = [];
  if (char.maximumHitpoints !== null) {
    statParts.push(`HP ${char.maximumHitpoints}`);
  }

  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cardTop}>
        <div className={styles.cardIdent}>
          <GameIcon name="crossed-swords" size={24} colorFilter="var(--filter-gold-dim)" decorative />
          <span className={styles.cardName}>{char.title}</span>
        </div>
        <span className={styles.cardAc}>AC {char.armorClass ?? '—'}</span>
      </div>

      <div className={styles.cardBadges}>
        {char.level !== null && (
          <Badge label={`Lv ${char.level}`} size="sm" />
        )}
      </div>

      {statParts.length > 0 && (
        <div className={styles.cardStats}>
          {statParts.join(' · ')}
        </div>
      )}
    </Link>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState(): React.ReactElement {
  return (
    <div className={styles.emptyPanel}>
      <GameIcon name="crossed-swords" size={32} colorFilter="var(--filter-gold-dim)" decorative />
      <h2 className={styles.emptyHeading}>No characters yet.</h2>
      <p className={styles.emptyBody}>
        Add characters via the Python CLI then sync to Drupal.
      </p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const CharactersPage: React.FC<PageProps<CharactersData>> = ({ data, location }) => {
  const characters = data.drupal.nodeCharacters.nodes;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Party</h1>
          <p className={styles.subtitle}>Active adventurers in this campaign.</p>
        </header>

        <Divider icon="crossed-swords" />

        <div className={styles.dividerSpacer} />

        {characters.length > 0 ? (
          <div className={styles.grid}>
            {characters.map(char => (
              <CharacterCard key={char.id} char={char} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </BaseTemplate>
  );
};

// ── GraphQL query ─────────────────────────────────────────────────────────────

export const query = graphql`
  query CharactersList {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id
          title
          firstName
          level
          armorClass
          maximumHitpoints
          path
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Party | D&D Consultant</title>;

export default CharactersPage;
