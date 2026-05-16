import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Badge } from '../components/atoms/Badge';
import { Divider } from '../components/atoms/Divider';
import * as styles from './characters.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignRef {
  name: string;
}

interface CharacterImage {
  mediaImage: { url: string; alt: string } | null;
}

interface CharacterNode {
  id:               string;
  title:            string;
  firstName:        string | null;
  level:            number | null;
  armorClass:       number | null;
  maximumHitpoints: number | null;
  path:             string | null;
  campaign:         CampaignRef | null;
  image:            CharacterImage | null;
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
  const initial = char.title.charAt(0).toUpperCase();

  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cardAvatar} aria-hidden="true">
        {char.image?.mediaImage?.url ? (
          <img
            src={char.image.mediaImage.url}
            alt={char.image.mediaImage.alt || char.title}
            className={styles.cardAvatarImg}
          />
        ) : (
          <span className={styles.cardAvatarInitial}>{initial}</span>
        )}
      </div>

      <div className={styles.cardBody}>
        <div className={styles.cardTop}>
          <span className={styles.cardName}>{char.title}</span>
          {char.armorClass !== null && (
            <span className={styles.cardAc}>AC {char.armorClass}</span>
          )}
        </div>

        {char.campaign && (
          <p className={styles.cardCampaign}>{char.campaign.name}</p>
        )}

        <div className={styles.cardBadges}>
          {char.level !== null && (
            <Badge label={`Level ${char.level}`} size="sm" />
          )}
          {char.maximumHitpoints !== null && (
            <Badge label={`HP ${char.maximumHitpoints}`} size="sm" />
          )}
        </div>
      </div>
    </Link>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState(): React.ReactElement {
  return (
    <div className={styles.emptyPanel}>
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
          <h1 className={styles.heading}>Characters</h1>
          <p className={styles.subtitle}>All adventurers across every campaign.</p>
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
          campaign {
            ... on Drupal_TermCampaign {
              name
            }
          }
          image {
            ... on Drupal_MediaImage {
              mediaImage { url alt }
            }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Characters | D&D Consultant</title>;

export default CharactersPage;
