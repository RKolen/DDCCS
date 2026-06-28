import * as https from 'https';
import * as nodePath from 'path';
import type { GatsbyNode } from 'gatsby';
import { createProxyMiddleware } from 'http-proxy-middleware';

// Accept DDEV's locally-signed certificate in the dev proxy.
// This agent is only used for the server-side proxy — never reaches the browser.
const devAgent = new https.Agent({ rejectUnauthorized: false });

/* ── Item pagination query ───────────────────────────────────────
   gatsby-source-graphql caps each query at 100 results. Items can
   exceed that, so we fetch all pages directly and create Gatsby
   nodes — type `AllItem` — bypassing the single-pass limit.
   ──────────────────────────────────────────────────────────────── */

const ITEM_FIELDS = `
  id title path source
  itemType isMagic itemRarity itemRequiresAttunement
  damage itemBonus itemCost itemWeight
  nonidentifiedName armorCategory armorAcBase armorStrRequirement
  edition     { ... on TermGameEdition   { name } }
  vestigeLevel { ... on TermVestigeLevel { name } }
  damageTypes      { ... on TermDamageType    { name } }
  weaponProperties { ... on TermWeaponProperty { name } }
  weaponMastery    { ... on TermWeaponMastery  { name } }
  weaponSubtype    { ... on TermWeaponSubtype  { name } }
  itemProperties {
    ... on TermMagicalProperty {
      name
      effect { ... on ParagraphWysiwyg { text { processed } } }
    }
  }
  image   { ... on MediaImage      { mediaImage { url alt } } }
  description { ... on ParagraphWysiwyg { text { processed } } }
`;

const ITEMS_PAGE_QUERY = (cursor: string | null): string => `{
  nodeItems(first: 100${cursor ? `, after: "${cursor}"` : ''}) {
    nodes { ${ITEM_FIELDS} }
    pageInfo { hasNextPage endCursor }
  }
}`;

interface RawItemNode {
  id:                     string;
  title:                  string;
  path:                   string | null;
  source:                 string | null;
  itemType:               string | null;
  isMagic:                boolean | null;
  itemRarity:             string | null;
  itemRequiresAttunement: boolean | null;
  damage:                 string | null;
  itemBonus:              number | null;
  itemCost:               string | null;
  itemWeight:             number | null;
  nonidentifiedName:      string | null;
  armorCategory:          string | null;
  armorAcBase:            number | null;
  armorStrRequirement:    number | null;
  edition:                { name: string } | null;
  vestigeLevel:           { name: string } | null;
  damageTypes:            Array<{ name: string }> | null;
  weaponProperties:       Array<{ name: string }> | null;
  weaponMastery:          Array<{ name: string }> | null;
  weaponSubtype:          Array<{ name: string }> | null;
  itemProperties:         Array<{
    name: string;
    effect: Array<{ text: Array<{ processed: string }> }> | null;
  }> | null;
  image:                  { mediaImage: { url: string; alt: string } | null } | null;
  description:            Array<{ text: Array<{ processed: string }> }> | null;
}

export const createSchemaCustomization: GatsbyNode['createSchemaCustomization'] = ({ actions }) => {
  const { createTypes } = actions;
  createTypes(`
    type AllItemImage {
      url: String
      alt: String
    }
    type AllItemMediaImage {
      mediaImage: AllItemImage
    }
    type AllItemEdition {
      name: String
    }
    type AllItemTerm     { name: String }
    type AllItemProperty {
      name:      String
      effectHtml: String
    }

    type AllItem implements Node {
      drupalId:               String!
      title:                  String!
      path:                   String
      source:                 String
      itemType:               String
      isMagic:                Boolean
      itemRarity:             String
      itemRequiresAttunement: Boolean
      damage:                 String
      itemBonus:              Int
      itemCost:               String
      itemWeight:             Float
      nonidentifiedName:      String
      armorCategory:          String
      armorAcBase:            Int
      armorStrRequirement:    Int
      descriptionHtml:        String
      edition:                AllItemEdition
      vestigeLevel:           AllItemTerm
      damageTypes:            [AllItemTerm]
      weaponProperties:       [AllItemTerm]
      weaponMastery:          [AllItemTerm]
      weaponSubtype:          [AllItemTerm]
      itemProperties:         [AllItemProperty]
      image:                  AllItemMediaImage
    }
  `);
};

export const sourceNodes: GatsbyNode['sourceNodes'] = async ({
  actions, createNodeId, createContentDigest,
}) => {
  const { createNode } = actions;

  const drupalUrl = (
    process.env.GATSBY_DRUPAL_BASE_URL ??
    process.env.DRUPAL_BASE_URL ??
    ''
  ).replace(/\/$/, '');

  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';

  if (!drupalUrl || !token) {
    console.warn('[sourceNodes] Drupal credentials not configured — skipping item pagination');
    return;
  }

  let cursor: string | null = null;
  let hasNextPage = true;
  let totalFetched = 0;

  while (hasNextPage) {
    let res: Response;
    try {
      res = await fetch(`${drupalUrl}/graphql`, {
        method:  'POST',
        headers: {
          'Content-Type':  'application/json',
          Accept:          'application/json',
          Authorization:   `Bearer ${token}`,
        },
        body: JSON.stringify({ query: ITEMS_PAGE_QUERY(cursor) }),
      });
    } catch (err) {
      console.error('[sourceNodes] Failed to reach Drupal for items:', err);
      break;
    }

    if (!res.ok) {
      console.error('[sourceNodes] Drupal returned', res.status, 'for items query');
      break;
    }

    const payload = (await res.json()) as {
      data?: { nodeItems: { nodes: RawItemNode[]; pageInfo: { hasNextPage: boolean; endCursor: string } } };
      errors?: unknown[];
    };

    if (payload.errors?.length) {
      console.error('[sourceNodes] GraphQL errors fetching items:', payload.errors);
      break;
    }

    const page       = payload.data?.nodeItems;
    const nodes      = page?.nodes ?? [];
    const pageInfo   = page?.pageInfo ?? { hasNextPage: false, endCursor: '' };

    for (const item of nodes) {
      /* Flatten nested HTML so Gatsby schema inference stays simple */
      const descriptionHtml = item.description
        ?.flatMap(d => d.text ?? [])
        .map(t => t.processed ?? '')
        .filter(Boolean)
        .join('') || null;

      const itemProperties = (item.itemProperties ?? []).map(p => ({
        name:       p.name,
        effectHtml: (p.effect ?? [])
          .flatMap(e => e.text ?? [])
          .map(t => t.processed ?? '')
          .filter(Boolean)
          .join('') || null,
      }));

      createNode({
        ...item,
        id:              createNodeId(`AllItem-${item.id}`),
        drupalId:        item.id,
        descriptionHtml,
        itemProperties,
        vestigeLevel:    item.vestigeLevel ?? null,
        damageTypes:     item.damageTypes ?? [],
        weaponProperties: item.weaponProperties ?? [],
        weaponMastery:   item.weaponMastery ?? [],
        weaponSubtype:   item.weaponSubtype ?? [],
        internal: {
          type:          'AllItem',
          contentDigest: createContentDigest(item),
        },
      });
    }

    totalFetched += nodes.length;
    hasNextPage  = pageInfo.hasNextPage;
    cursor       = pageInfo.endCursor ?? null;
  }

  console.info(`[sourceNodes] Fetched ${totalFetched} items from Drupal.`);
};

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

interface DrupalMonsterNode {
  id:   string;
  path: string | null;
}

interface CharactersQueryData {
  drupal: { nodeCharacters: { nodes: DrupalNode[] } };
}

interface StoriesQueryData {
  drupal: { nodeStories: { nodes: DrupalStoryNode[] } };
}

interface MonstersQueryData {
  drupal: { nodeMonsters: { nodes: DrupalMonsterNode[] } };
}

export const createPages: GatsbyNode['createPages'] = async ({ graphql, actions }) => {
  const drupalUrl = process.env.DRUPAL_BASE_URL;
  if (!drupalUrl) {
    throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
  }

  const { createPage } = actions;

  const characterTemplate = nodePath.resolve('./src/templates/character.tsx');
  const storyTemplate     = nodePath.resolve('./src/templates/story.tsx');
  const monsterTemplate   = nodePath.resolve('./src/templates/monster.tsx');
  const itemTemplate      = nodePath.resolve('./src/templates/item.tsx');

  const characterQuery = await graphql<CharactersQueryData>(`
    {
      drupal {
        nodeCharacters(first: 100) {
          nodes { id path characterType }
        }
      }
    }
  `);

  const monsterQuery = await graphql<MonstersQueryData>(`
    {
      drupal {
        nodeMonsters(first: 100) {
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

  /* Both PCs and NPCs use the same character sheet template — NPCs are
     character nodes with characterType === false, same data shape. */
  characterQuery.data?.drupal.nodeCharacters.nodes.forEach(node => {
    const isNpc   = node.characterType === false;
    const pagePath = node.path
      ? node.path
      : isNpc ? `/npcs/${node.id}` : `/characters/${node.id}`;
    createPage({ path: pagePath, component: characterTemplate, context: { id: node.id } });
  });

  monsterQuery.data?.drupal.nodeMonsters.nodes.forEach(node => {
    const pagePath = node.path ?? `/monsters/${node.id}`;
    createPage({ path: pagePath, component: monsterTemplate, context: { id: node.id } });
  });

  /* Items — query the AllItem source nodes created by sourceNodes */
  interface AllItemsQueryData {
    allAllItem: { nodes: Array<{ drupalId: string; path: string | null }> };
  }
  const itemQuery = await graphql<AllItemsQueryData>(`
    {
      allAllItem {
        nodes {
          drupalId
          path
        }
      }
    }
  `);

  itemQuery.data?.allAllItem.nodes.forEach(node => {
    const pagePath = node.path ?? `/items/${node.drupalId}`;
    createPage({ path: pagePath, component: itemTemplate, context: { drupalId: node.drupalId } });
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

  // Only proxy Drupal REST endpoints — Gatsby Functions also live at /api/*
  // and must not be forwarded to Drupal.
  app.use(
    createProxyMiddleware({
      target: drupalUrl,
      changeOrigin: true,
      agent: devAgent,
      pathFilter: (pathname: string) => pathname.startsWith('/api/content-search'),
      headers: { 'X-Forwarded-Proto': 'https' },
    }),
  );
};
