/**
 * /items/ — the Loot Vault index page.
 *
 * Queries every item from the `allAllItem` Gatsby nodes (which paginate past
 * graphql_compose's default 100-item limit) and hands the result to ItemRoster
 * for filter, search, summary band, and grid rendering.
 */

import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { ItemRoster, type ItemRosterData } from '../components/organisms/ItemRoster';

const ItemsPage: React.FC<PageProps<ItemRosterData>> = ({ data, location }) => (
  <BaseTemplate currentPath={location.pathname}>
    <ItemRoster data={data} />
  </BaseTemplate>
);

export const query = graphql`
  query ItemsList {
    allAllItem {
      nodes {
        id
        title
        path
        itemType
        isMagic
        itemRarity
        itemRequiresAttunement
        weaponSubtype { name }
        image { mediaImage { url alt } }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Items | D&amp;D Consultant</title>;

export default ItemsPage;
