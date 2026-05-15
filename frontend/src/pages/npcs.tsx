import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { NPCCard } from '../components/organisms/NPCCard';
import * as styles from './npcs.module.css';

interface NPCNode {
  id:          string;
  title:       string;
  role:        string | null;
  personality: { value: string } | null;
}

interface NPCListData {
  drupal: {
    nodeNpcs: { nodes: NPCNode[] };
  };
}

const NPCsPage: React.FC<PageProps<NPCListData>> = ({ data, location }) => {
  const npcs = data.drupal.nodeNpcs.nodes;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.header}>
          <h1>NPC Registry</h1>
          <p className={styles.subtitle}>Recurring characters in your campaign</p>
        </header>

        {npcs.length > 0 ? (
          <div className={styles.list}>
            {npcs.map(npc => (
              <NPCCard
                key={npc.id}
                name={npc.title}
                role={npc.role ?? ''}
                personality={npc.personality?.value ?? ''}
              />
            ))}
          </div>
        ) : (
          <p className={styles.empty}>No NPCs in the registry yet.</p>
        )}
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query NPCList {
    drupal {
      nodeNpcs(first: 100) {
        nodes {
          id
          title
          role
          personality { value }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>NPC Registry | D&D Consultant</title>;

export default NPCsPage;
