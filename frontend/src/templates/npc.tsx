import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { NPCCard } from '../components/organisms/NPCCard';

interface NpcNode {
  title:       string;
  personality: { value: string } | null;
  role:        string | null;
  path:        string | null;
}

interface NPCData {
  drupal: {
    node: Partial<NpcNode> | null;
  };
}

const NPCPage: React.FC<PageProps<NPCData>> = ({ data, location }) => {
  const npc = data.drupal?.node as NpcNode | null;

  if (!npc || !npc.title) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>NPC not found.</p>
      </BaseTemplate>
    );
  }

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div style={{ padding: 'var(--space-8) var(--space-10)', maxWidth: 760, margin: '0 auto' }}>
        <NPCCard
          name={npc.title}
          role={npc.role ?? ''}
          location={undefined}
          personality={npc.personality?.value ?? ''}
          relationships={undefined}
        />
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query NPCPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeCharacter {
          title
          personality { value }
          role
          path
        }
      }
    }
  }
`;

export const Head: HeadFC<NPCData> = ({ data }) => {
  const npc = data.drupal?.node as NpcNode | null;
  return <title>{npc?.title ?? 'NPC'} | D&D Consultant</title>;
};

export default NPCPage;
