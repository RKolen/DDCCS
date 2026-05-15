import * as https from 'https';
import * as nodePath from 'path';
import type { GatsbyNode } from 'gatsby';
import { createProxyMiddleware } from 'http-proxy-middleware';

// Accept DDEV's locally-signed certificate in the dev proxy.
// This agent is only used for the server-side proxy — never reaches the browser.
const devAgent = new https.Agent({ rejectUnauthorized: false });

interface DrupalNode {
  id: string;
  path: string | null;
}

interface DrupalStoryNode extends DrupalNode {
  title: string;
  storyNumber: number | null;
}

interface DrupalNodeConnection {
  nodes: DrupalNode[];
}

interface DrupalStoryConnection {
  nodes: DrupalStoryNode[];
}

interface CharactersQueryData {
  drupal: { nodeCharacters: DrupalNodeConnection };
}

interface NpcsQueryData {
  drupal: { nodeNpcs: DrupalNodeConnection };
}

interface StoriesQueryData {
  drupal: { nodeStories: DrupalStoryConnection };
}

export const createPages: GatsbyNode['createPages'] = async ({ graphql, actions }) => {
  const drupalUrl = process.env.DRUPAL_BASE_URL;
  if (!drupalUrl) {
    throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
  }

  const { createPage } = actions;

  const characterTemplate = nodePath.resolve('./src/templates/character.tsx');
  const npcTemplate       = nodePath.resolve('./src/templates/npc.tsx');
  const storyTemplate     = nodePath.resolve('./src/templates/story.tsx');

  const characterQuery = await graphql<CharactersQueryData>(`
    {
      drupal {
        nodeCharacters(first: 100) {
          nodes { id path }
        }
      }
    }
  `);

  const npcQuery = await graphql<NpcsQueryData>(`
    {
      drupal {
        nodeNpcs(first: 100) {
          nodes { id path }
        }
      }
    }
  `);

  const storyQuery = await graphql<StoriesQueryData>(`
    {
      drupal {
        nodeStories(first: 100) {
          nodes { id path title storyNumber }
        }
      }
    }
  `);

  characterQuery.data?.drupal.nodeCharacters.nodes.forEach(node => {
    const pagePath = node.path ? node.path : `/characters/${node.id}`;
    createPage({ path: pagePath, component: characterTemplate, context: { id: node.id } });
  });

  npcQuery.data?.drupal.nodeNpcs.nodes.forEach(node => {
    const pagePath = node.path ? node.path : `/npcs/${node.id}`;
    createPage({ path: pagePath, component: npcTemplate, context: { id: node.id } });
  });

  // Sort stories by storyNumber so prev/next are in session order.
  const stories = (storyQuery.data?.drupal.nodeStories.nodes ?? [])
    .slice()
    .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0));

  stories.forEach((node, idx) => {
    const pagePath = node.path ? node.path : `/stories/${node.id}`;
    const prev = idx > 0 ? stories[idx - 1] : null;
    const next = idx < stories.length - 1 ? stories[idx + 1] : null;

    createPage({
      path: pagePath,
      component: storyTemplate,
      context: {
        id: node.id,
        prevPath:  prev ? (prev.path ?? `/stories/${prev.id}`) : null,
        prevTitle: prev?.title ?? null,
        nextPath:  next ? (next.path ?? `/stories/${next.id}`) : null,
        nextTitle: next?.title ?? null,
      },
    });
  });
};

export const onCreateDevServer: GatsbyNode['onCreateDevServer'] = ({ app }) => {
  const drupalUrl = process.env.DRUPAL_BASE_URL;
  if (!drupalUrl) {
    throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
  }

  app.use(
    createProxyMiddleware({
      target: drupalUrl,
      changeOrigin: true,
      agent: devAgent,
      pathFilter: '/api',
      headers: { 'X-Forwarded-Proto': 'https' },
    }),
  );
};
