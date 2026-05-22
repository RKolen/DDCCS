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
  characterType: boolean | null;
}

interface DrupalStoryNode {
  id: string;
  path: string | null;
  title: string;
  storyNumber: number | null;
}

interface CharactersQueryData {
  drupal: { nodeCharacters: { nodes: DrupalNode[] } };
}

interface StoriesQueryData {
  drupal: { nodeStories: { nodes: DrupalStoryNode[] } };
}

export const createPages: GatsbyNode['createPages'] = async ({ graphql, actions }) => {
  const drupalUrl = process.env.DRUPAL_BASE_URL;
  if (!drupalUrl) {
    throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
  }

  const { createPage } = actions;

  const characterTemplate = nodePath.resolve('./src/templates/character.tsx');
  const storyTemplate     = nodePath.resolve('./src/templates/story.tsx');

  const characterQuery = await graphql<CharactersQueryData>(`
    {
      drupal {
        nodeCharacters(first: 100) {
          nodes { id path characterType }
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

  /* Both PCs and NPCs use the same character sheet template — NPCs are
     character nodes with characterType === false, same data shape. */
  characterQuery.data?.drupal.nodeCharacters.nodes.forEach(node => {
    const isNpc   = node.characterType === false;
    const pagePath = node.path
      ? node.path
      : isNpc ? `/npcs/${node.id}` : `/characters/${node.id}`;
    createPage({ path: pagePath, component: characterTemplate, context: { id: node.id } });
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
