import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Badge } from '../components/atoms/Badge';
import { Divider } from '../components/atoms/Divider';
import * as styles from './characters.module.css';

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
  characterType:    boolean | null;
  role:             string | null;
  armorClass:       number | null;
  maximumHitpoints: number | null;
  path:             string | null;
  campaign:         CampaignRef | null;
  image:            CharacterImage | null;
}

interface NPCListData {
  drupal: {
    nodeCharacters: { nodes: CharacterNode[] };
  } | null;
}

function NPCCard({ npc }: { npc: CharacterNode }): React.ReactElement {
  const href = npc.path ?? '#';
  const initial = npc.title.charAt(0).toUpperCase();

  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cardAvatar} aria-hidden="true">
        {npc.image?.mediaImage?.url ? (
          <img
            src={npc.image.mediaImage.url}
            alt={npc.image.mediaImage.alt || npc.title}
            className={styles.cardAvatarImg}
          />
        ) : (
          <span className={styles.cardAvatarInitial}>{initial}</span>
        )}
      </div>

      <div className={styles.cardBody}>
        <div className={styles.cardTop}>
          <span className={styles.cardName}>{npc.title}</span>
          {npc.armorClass !== null && (
            <span className={styles.cardAc}>AC {npc.armorClass}</span>
          )}
        </div>

        {npc.campaign && (
          <p className={styles.cardCampaign}>{npc.campaign.name}</p>
        )}

        <div className={styles.cardBadges}>
          {npc.role && <Badge label={npc.role} size="sm" />}
          {npc.maximumHitpoints !== null && (
            <Badge label={`HP ${npc.maximumHitpoints}`} size="sm" />
          )}
        </div>
      </div>
    </Link>
  );
}

function EmptyState(): React.ReactElement {
  return (
    <div className={styles.emptyPanel}>
      <h2 className={styles.emptyHeading}>No NPCs yet.</h2>
      <p className={styles.emptyBody}>
        Add NPCs in Drupal as Character nodes with Character Type set to NPC.
      </p>
    </div>
  );
}

const NPCsPage: React.FC<PageProps<NPCListData>> = ({ data, location }) => {
  const npcs = data.drupal?.nodeCharacters.nodes.filter(n => n.characterType === false) ?? [];

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>NPCs</h1>
          <p className={styles.subtitle}>Recurring non-player characters across every campaign.</p>
        </header>

        <Divider icon="scroll-unfurled" />

        <div className={styles.dividerSpacer} />

        {npcs.length > 0 ? (
          <div className={styles.grid}>
            {npcs.map(npc => (
              <NPCCard key={npc.id} npc={npc} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query NPCList {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id
          title
          firstName
          characterType
          role
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

export const Head: HeadFC = () => <title>NPC Registry | D&D Consultant</title>;

export default NPCsPage;
