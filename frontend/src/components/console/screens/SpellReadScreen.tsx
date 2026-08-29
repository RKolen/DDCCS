/**
 * SpellReadScreen — `spells/sp-read`.
 *
 * Split-pane: picker rail plus the same SpellSheet the public page uses.
 * ctx.spellIdx indexes the nodeSpells list; the compendium sets it before
 * jumping here.
 */

import * as React from 'react';
import { graphql, Link, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { SpellSheet } from '../../molecules/SpellSheet';
import {
  type SpellRecord,
  flattenDescription,
  levelLabel,
  schoolName,
} from '../../../types/spell';

interface ReadNode {
  id: string;
  title: string;
  path: string | null;
  spellLevel: number;
  castingTime: string | null;
  spellRange: string | null;
  spellComponents: string | null;
  spellDuration: string | null;
  concentration: boolean | null;
  ritual: boolean | null;
  spellSchool: { name: string | null } | null;
  description: Array<{ text: Array<{ processed: string }> | null }> | null;
}

interface ReadQuery {
  drupal: { nodeSpells: { nodes: ReadNode[] } };
}

function toRecord(node: ReadNode): SpellRecord {
  return {
    id: node.id,
    title: node.title,
    path: node.path,
    spellLevel: node.spellLevel,
    school: schoolName(node.spellSchool),
    castingTime: node.castingTime,
    spellRange: node.spellRange,
    spellComponents: node.spellComponents,
    spellDuration: node.spellDuration,
    concentration: node.concentration,
    ritual: node.ritual,
    descriptionHtml: flattenDescription(node.description),
  };
}

export function SpellReadScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useStaticQuery<ReadQuery>(graphql`
    query ConsoleSpellRead {
      drupal {
        nodeSpells(first: 100) {
          nodes {
            id title path spellLevel castingTime spellRange
            spellComponents spellDuration concentration ritual
            spellSchool { ... on Drupal_TermSpellSchool { name } }
            description { ... on Drupal_ParagraphWysiwyg { text { processed } } }
          }
        }
      }
    }
  `);

  const all = data?.drupal?.nodeSpells?.nodes ?? [];
  const idx = ctx.spellIdx ?? 0;
  const raw = all[idx] ?? null;
  const spell = raw != null ? toRecord(raw) : null;

  return (
    <div className="screen-itemdetails">
      {all.length > 0 && (
        <aside className="char-picker">
          <ul className="char-picker-list">
            {all.map((node, index) => {
              const initials = node.title.split(' ').map(word => word[0]).slice(0, 2).join('').toUpperCase();
              return (
                <li key={node.id}>
                  <button
                    type="button"
                    className={`char-picker-item${index === idx ? ' active' : ''}`}
                    onClick={() => setCtx({ ...ctx, spellIdx: index })}
                  >
                    <span className="char-pip">{initials}</span>
                    <span className="char-pip-meta">
                      <strong>{node.title}</strong>
                      <span>{levelLabel(node.spellLevel)}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>
      )}

      <div className="char-sheet">
        {spell == null ? (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
            {all.length === 0
              ? 'No spells in Drupal. Search the wiki or create a custom spell.'
              : 'Select a spell from the list.'}
          </p>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <span className="reader-eyebrow">Spell</span>
              {spell.path != null && spell.path !== '' && (
                <Link to={spell.path} className="ghost-btn" style={{ textDecoration: 'none' }}>
                  <Icon name="scroll" size={11} /> Full sheet
                </Link>
              )}
            </div>
            <SpellSheet spell={spell} />
          </>
        )}
      </div>
    </div>
  );
}
