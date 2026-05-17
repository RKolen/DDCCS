/**
 * DDCCS Console — ScreenRouter
 * --------------------------------------------------------------
 * Typed port of `menu/screens-router.jsx` from the design system.
 *
 * Maps (section.id, item.id) -> the screen component that fills the
 * action-body panel of the StatelyLedger. This is intentionally a
 * dispatch table rather than per-route file structure — it mirrors
 * the CLI's section/item taxonomy and lets us share state via `ctx`.
 *
 * Canonical reference for full screen list:
 *   /menu/screens-router.jsx          <- the routing table
 *   /menu/screens-content.jsx         <- story/reader screens
 *   /menu/screens-admin.jsx           <- settings/tools/NPC screens
 *
 * NPC note: NPCs are character nodes with field_character_type=false.
 * The `npcs/*` routes query nodeCharacter filtered by that field.
 *
 * IMPORTANT: the three character pages we designed (see
 * /All Characters.html, /Character Sheet.html, /Current Party.html)
 * are NOT routed inside the console alone — they also have direct
 * Gatsby routes (/characters/, /characters/:slug/, /party/). When
 * navigated from within the console, render the same components
 * inline; when deep-linked, the page-level wrapper provides the
 * StatelyLedger chrome around them.
 */

import * as React from 'react';
import type { MenuSection, MenuItem } from './menuData';

/* ────────────────────────────────────────────────────────────
   Shared screen context
   ──────────────────────────────────────────────────────────── */

export interface ScreenContext {
  storyIdx?: number;
  charIdx?: number;
  /** Name of the currently active campaign (from Campaign taxonomy term) */
  activeCampaignName?: string | null;
  settingsTab?: 'view' | 'ai' | 'rag' | 'display' | 'paths' | 'validate';
  _jumpTo?: {
    sectionId?: string;
    itemId?: string;
    charIdx?: number;
    storyIdx?: number;
  };
  _itemId?: string;
  _sectionId?: string;
  [key: string]: unknown;
}

export interface ScreenProps {
  ctx: ScreenContext;
  setCtx: (next: ScreenContext) => void;
}

interface ScreenRouterProps {
  section: MenuSection;
  item: MenuItem;
  ctx: ScreenContext;
  setCtx: (next: ScreenContext) => void;
}

/* ────────────────────────────────────────────────────────────
   Screen imports
   ──────────────────────────────────────────────────────────── */

import { CharacterListScreen }    from './screens/CharacterListScreen';
import { CharacterDetailScreen }  from './screens/CharacterDetailScreen';
import { CurrentPartyScreen }     from './screens/CurrentPartyScreen';
import { ReadStoryFileScreen }    from './screens/ReadStoryFileScreen';
import { ConsultScreen }          from './screens/ConsultScreen';
import { PlaceholderScreen }      from './screens/PlaceholderScreen';

/* ────────────────────────────────────────────────────────────
   Dispatch table
   ──────────────────────────────────────────────────────────── */

export function ScreenRouter({ section, item, ctx, setCtx }: ScreenRouterProps): React.ReactElement | null {
  if (!section || !item) return null;

  const key = `${section.id}/${item.id}`;
  const ictx: ScreenContext = { ...ctx, _itemId: item.id, _sectionId: section.id };
  const set = (next: ScreenContext): void => {
    setCtx({ ...next, _itemId: next._itemId ?? item.id });
  };

  /* ───── Characters ───── */
  if (key === 'characters/list')    return <CharacterListScreen ctx={ictx} setCtx={set} />;
  if (key === 'characters/view')    return <CharacterDetailScreen ctx={ictx} setCtx={set} />;
  if (key === 'characters/consult') return <ConsultScreen ctx={ictx} setCtx={set} />;

  /* ───── Stories / Read ───── */
  if (key === 'read/r-story')       return <ReadStoryFileScreen ctx={ictx} setCtx={set} />;
  if (key === 'read/r-char')        return <CharacterDetailScreen ctx={ictx} setCtx={set} />;

  /* ───── NPCs (character nodes with field_character_type=false) ───── */
  if (key === 'npcs/n-list')        return <CharacterListScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-view')        return <CharacterDetailScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;

  /* Fallback — loud placeholder so missing screens can't be shipped silently */
  return <PlaceholderScreen section={section} item={item} />;
}
