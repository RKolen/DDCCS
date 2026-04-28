import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { NPCCard } from '../components/organisms/NPCCard';

interface NPCData {
  nodeNpc: {
    title:            string;
    fieldRole:        Array<{ name: string }> | null;
    fieldLocation:    Array<{ name: string }> | null;
    fieldPersonality: { value: string } | null;
    fieldRelationships: Array<{
      fieldRelatedCharacter:     Array<{ title: string }> | null;
      fieldRelationshipDescription: { value: string } | null;
    }> | null;
  } | null;
}

const NPCPage: React.FC<PageProps<NPCData>> = ({ data, location }) => {
  const npc = data.nodeNpc;

  if (!npc) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>NPC not found.</p>
      </BaseTemplate>
    );
  }

  const relationships = (npc.fieldRelationships ?? [])
    .map(rel => ({
      name:        rel.fieldRelatedCharacter?.[0]?.title ?? 'Unknown',
      description: rel.fieldRelationshipDescription?.value ?? '',
    }))
    .filter(r => r.description.length > 0);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div style={{ padding: 'var(--space-8) var(--space-10)', maxWidth: 760, margin: '0 auto' }}>
        <NPCCard
          name={npc.title}
          role={npc.fieldRole?.[0]?.name ?? ''}
          location={npc.fieldLocation?.[0]?.name}
          personality={npc.fieldPersonality?.value ?? ''}
          relationships={relationships.length > 0 ? relationships : undefined}
        />
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query NPCPage($id: String!) {
    nodeNpc(id: { eq: $id }) {
      title
      fieldRole { name }
      fieldLocation { name }
      fieldPersonality { value }
      fieldRelationships {
        ... on paragraph__relationship {
          fieldRelatedCharacter { ... on node__character { title } }
          fieldRelationshipDescription { value }
        }
      }
    }
  }
`;

export const Head: HeadFC<NPCData> = ({ data }) => (
  <title>{data.nodeNpc?.title ?? 'NPC'} | D&D Consultant</title>
);

export default NPCPage;
