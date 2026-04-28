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
