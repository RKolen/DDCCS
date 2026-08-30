import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import {
  type SpellTermNode,
  spellTermToRecord,
} from '../types/spell';
import '../graphql/spellTerm';

export interface SpellCatalogEntry {
  id: string;
  name: string;
  path: string;
  level: number;
  school: string | null;
  castingTime: string | null;
  spellRange: string | null;
  excerpt: string;
}

interface CatalogQuery {
  drupal: { termSpells: { nodes: SpellTermNode[] } };
}

function excerptFromHtml(html: string | null): string {
  if (html == null || html === '') {
    return '';
  }
  const text = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  if (text.length <= 140) {
    return text;
  }
  return `${text.slice(0, 137)}...`;
}

/**
 * Every spells-vocabulary term, for mention highlighting in story HTML.
 */
export function useSpellCatalog(): SpellCatalogEntry[] {
  const data = useStaticQuery<CatalogQuery>(graphql`
    query SpellMentionCatalog {
      drupal {
        termSpells(first: 500) {
          nodes {
            ...SpellTermFields
          }
        }
      }
    }
  `);

  return React.useMemo(() => {
    const nodes = data?.drupal?.termSpells?.nodes ?? [];
    const entries: SpellCatalogEntry[] = [];
    nodes.forEach(node => {
      const record = spellTermToRecord(node);
      if (record.path == null) {
        return;
      }
      entries.push({
        id: record.id,
        name: record.title,
        path: record.path,
        level: record.spellLevel,
        school: record.school,
        castingTime: record.castingTime,
        spellRange: record.spellRange,
        excerpt: excerptFromHtml(record.descriptionHtml),
      });
    });
    return entries;
  }, [data]);
}
