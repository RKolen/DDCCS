import * as https from 'https';
import * as nodePath from 'path';
import type { GatsbyNode } from 'gatsby';
import { createProxyMiddleware } from 'http-proxy-middleware';

const DRUPAL_URL = 'https://drupal-cms.ddev.site';

// Accept DDEV's locally-signed certificate in the dev proxy.
// This agent is only used for the server-side proxy — never reaches the browser.
const devAgent = new https.Agent({ rejectUnauthorized: false });

interface NodeWithPath {
  id: string;
  drupalInternalNid: number;
  path: { alias: string } | null;
}

interface GraphQLResult<T> {
  data?: T;
  errors?: unknown[];
}

export const createPages: GatsbyNode['createPages'] = async ({ graphql, actions }) => {
  const { createPage } = actions;

  const characterTemplate = nodePath.resolve('./src/templates/character.tsx');
  const npcTemplate       = nodePath.resolve('./src/templates/npc.tsx');
  const storyTemplate     = nodePath.resolve('./src/templates/story.tsx');

  const [charactersResult, npcsResult, storiesResult] = await Promise.all([
    graphql<{ allNodeCharacter: { nodes: NodeWithPath[] } }>(`
      { allNodeCharacter { nodes { id drupalInternalNid path { alias } } } }
    `),
    graphql<{ allNodeNpc: { nodes: NodeWithPath[] } }>(`
      { allNodeNpc { nodes { id drupalInternalNid path { alias } } } }
    `),
    graphql<{ allNodeStory: { nodes: NodeWithPath[] } }>(`
      { allNodeStory { nodes { id drupalInternalNid path { alias } } } }
    `),
  ]);

  (charactersResult as GraphQLResult<{ allNodeCharacter: { nodes: NodeWithPath[] } }>)
    .data?.allNodeCharacter.nodes.forEach(node => {
      createPage({
        path: node.path?.alias ?? `/characters/${node.drupalInternalNid}`,
        component: characterTemplate,
        context: { id: node.id },
      });
    });

  (npcsResult as GraphQLResult<{ allNodeNpc: { nodes: NodeWithPath[] } }>)
    .data?.allNodeNpc.nodes.forEach(node => {
      createPage({
        path: node.path?.alias ?? `/npcs/${node.drupalInternalNid}`,
        component: npcTemplate,
        context: { id: node.id },
      });
    });

  (storiesResult as GraphQLResult<{ allNodeStory: { nodes: NodeWithPath[] } }>)
    .data?.allNodeStory.nodes.forEach(node => {
      createPage({
        path: node.path?.alias ?? `/stories/${node.drupalInternalNid}`,
        component: storyTemplate,
        context: { id: node.id },
      });
    });
};

export const createSchemaCustomization: GatsbyNode['createSchemaCustomization'] = ({ actions }) => {
  const { createTypes } = actions;

  createTypes(`
    # -------------------------------------------------------------------------
    # Scalar / value-object helpers (not Drupal entities, no Node interface)
    # -------------------------------------------------------------------------
    type FieldTextValue {
      value: String
    }
    type FieldTextWithSummary {
      value: String
      processed: String
    }
    type FilePath {
      alias: String
    }

    # -------------------------------------------------------------------------
    # Taxonomy terms — stub fields so fragments compile when terms are empty
    # -------------------------------------------------------------------------
    type TaxonomyTermSpecies implements Node {
      name: String
    }
    type TaxonomyTermCharacterClass implements Node {
      name: String
    }
    type TaxonomyTermBackground implements Node {
      name: String
    }
    type TaxonomyTermSkill implements Node {
      name: String
    }
    type TaxonomyTermRole implements Node {
      name: String
    }
    type TaxonomyTermLocation implements Node {
      name: String
    }
    type TaxonomyTermSpellSchool implements Node {
      name: String
    }

    # -------------------------------------------------------------------------
    # Paragraph types — defined so inline fragments compile when empty
    # -------------------------------------------------------------------------
    type paragraph__class implements Node {
      fieldClass: [TaxonomyTermCharacterClass]
      fieldSubclassRef: [TaxonomyTermCharacterClass]
    }
    type paragraph__ability_scores implements Node {
      fieldStrength: Int
      fieldDexterity: Int
      fieldConstitution: Int
      fieldIntelligence: Int
      fieldWisdom: Int
      fieldCharisma: Int
    }
    type paragraph__spell_slot implements Node {
      fieldSpellLevel: Int
      fieldSpellSlotsTotal: Int
      fieldSpellSlotsAvailable: Int
    }
    type paragraph__spell_reference implements Node {
      fieldSpell: [node__spell]
    }
    type paragraph__relationship implements Node {
      fieldRelatedCharacter: [node__character]
      fieldRelationshipDescription: [FieldTextValue]
    }

    # -------------------------------------------------------------------------
    # Content types — ensures allNodeX queries exist even with no nodes
    # -------------------------------------------------------------------------
    type node__spell implements Node {
      title: String
      fieldSpellLevel: Int
      fieldSpellSchool: [TaxonomyTermSpellSchool]
      fieldConcentration: Boolean
    }
    type node__item implements Node {
      title: String
      fieldItemType: String
      fieldItemRarity: String
      fieldDescription: [FieldTextValue]
      drupalInternalNid: Int
      path: FilePath
    }
    type node__npc implements Node {
      title: String
      fieldRole: [TaxonomyTermRole]
      fieldLocation: [TaxonomyTermLocation]
      fieldPersonality: [FieldTextValue]
      fieldRelationships: [paragraph__relationship]
      drupalInternalNid: Int
      path: FilePath
    }
    type node__story implements Node {
      title: String
      fieldStoryNumber: Int
      fieldSessionDate: Date
      fieldBody: FieldTextWithSummary
      fieldStoryHooks: [FieldTextValue]
      fieldCharacters: [node__character]
      drupalInternalNid: Int
      path: FilePath
    }
    type node__character implements Node {
      title: String
      fieldFirstName: String
      fieldNickname: String
      fieldLevel: Int
      fieldArmorClass: Int
      fieldMaximumHitpoints: Int
      fieldMovementSpeed: Int
      fieldProficiencyBonus: Int
      fieldPersonality: [FieldTextValue]
      fieldSpecies: [TaxonomyTermSpecies]
      fieldBackground: [TaxonomyTermBackground]
      fieldClass: [paragraph__class]
      fieldAbilityScores: [paragraph__ability_scores]
      fieldSpellSlots: [paragraph__spell_slot]
      fieldSpellsRef: [paragraph__spell_reference]
      fieldSkills: [TaxonomyTermSkill]
      fieldEquipmentItems: [node__item]
      drupalInternalNid: Int
      path: FilePath
    }
  `);
};

export const onCreateDevServer: GatsbyNode['onCreateDevServer'] = ({ app }) => {
  app.use(
    createProxyMiddleware({
      target: DRUPAL_URL,
      changeOrigin: true,
      agent: devAgent,
      pathFilter: '/api',
      // Tell Drupal the connection is HTTPS so basic_auth doesn't redirect to
      // HTTPS when an Authorization header is present.
      headers: { 'X-Forwarded-Proto': 'https' },
    }),
  );
};
