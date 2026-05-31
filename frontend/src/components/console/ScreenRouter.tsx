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
 * Canonical reference:
 *   /menu/screens-router.jsx          <- the routing table
 *   /menu/screens-content.jsx         <- story/reader screens
 *   /menu/screens-admin.jsx           <- settings/tools/NPC screens
 *
 * NPC note: NPCs are character nodes with field_character_type=false.
 * The `npcs/*` routes query nodeCharacter filtered by that field.
 */

import * as React from 'react';
import type { MenuSection, MenuItem } from './menuData';

/* ────────────────────────────────────────────────────────────
   Shared screen context
   ──────────────────────────────────────────────────────────── */

export interface ScreenContext {
  storyIdx?: number;
  charIdx?: number;
  activeCampaignName?: string | null;
  settingsTab?: 'view' | 'ai' | 'rag' | 'display' | 'paths' | 'validate' | 'save';
  modelId?: string;
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

import { CharacterListScreen }          from './screens/CharacterListScreen';
import { CharacterDetailScreen }        from './screens/CharacterDetailScreen';
import { CurrentPartyScreen }           from './screens/CurrentPartyScreen';
import { ReadStoryFileScreen }          from './screens/ReadStoryFileScreen';
import { ConsultScreen }                from './screens/ConsultScreen';
import { StorySeriesWorkspaceScreen }   from './screens/StorySeriesWorkspaceScreen';
import { AiActionScreen }               from './screens/AiActionScreen';
import { StoryDetailsScreen }           from './screens/StoryDetailsScreen';
import { SessionNotesScreen }           from './screens/SessionNotesScreen';
import { TimelineScreen }               from './screens/TimelineScreen';
import { SpellRegistryScreen }          from './screens/SpellRegistryScreen';
import { NewSeriesScreen }              from './screens/NewSeriesScreen';
import { SettingsScreen }               from './screens/SettingsScreen';
import { ModelProfileScreen }           from './screens/ModelProfileScreen';
import { ToolsScreen }                  from './screens/ToolsScreen';
import { NpcValidatorScreen }           from './screens/NpcValidatorScreen';
import { DeprecatedScreen }             from './screens/DeprecatedScreen';
import { PlaceholderScreen }            from './screens/PlaceholderScreen';

/* ────────────────────────────────────────────────────────────
   Dispatch table
   ──────────────────────────────────────────────────────────── */

export function ScreenRouter({ section, item, ctx, setCtx }: ScreenRouterProps): React.ReactElement | null {
  if (!section || !item) return null;

  const key  = `${section.id}/${item.id}`;
  const ictx: ScreenContext = { ...ctx, _itemId: item.id, _sectionId: section.id };
  const set  = (next: ScreenContext): void => {
    setCtx({ ...next, _itemId: next._itemId ?? item.id });
  };

  /* ───── Characters ───── */
  if (key === 'characters/list')         return <CharacterListScreen ctx={ictx} setCtx={set} />;
  if (key === 'characters/view')         return <CharacterDetailScreen ctx={ictx} setCtx={set} />;
  if (key === 'characters/consult')      return <ConsultScreen ctx={ictx} setCtx={set} />;
  if (key === 'characters/completeness') return <NpcValidatorScreen ctx={{ ...ictx, pcMode: true }} setCtx={set} />;
  if (key === 'characters/ascii')        return <DeprecatedScreen item={item} />;

  /* ───── Stories ───── */
  if (key === 'stories/work-series') {
    const actionId = ictx.workSeriesAction as string | undefined;
    if (actionId === 's-view')  return <StoryDetailsScreen  ctx={ictx} setCtx={set} />;
    if (actionId === 's-notes') return <SessionNotesScreen  ctx={ictx} setCtx={set} />;
    if (actionId !== undefined) return <AiActionScreen      ctx={ictx} setCtx={set} />;
    return <StorySeriesWorkspaceScreen ctx={ictx} setCtx={set} />;
  }
  if (key === 'stories/timeline')    return <TimelineScreen ctx={ictx} setCtx={set} />;
  if (key === 'stories/spells')      return <SpellRegistryScreen ctx={ictx} setCtx={set} />;
  if (key === 'stories/new-series')  return <NewSeriesScreen ctx={ictx} setCtx={set} />;

  /* ───── Read Stories ───── */
  if (key === 'read/r-story')   return <ReadStoryFileScreen ctx={ictx} setCtx={set} />;
  if (key === 'read/r-char')    return <CharacterDetailScreen ctx={ictx} setCtx={set} />;
  if (key === 'read/r-session') return <ReadStoryFileScreen ctx={ictx} setCtx={set} />;
  if (key === 'read/r-dev')     return <PlaceholderScreen section={section} item={item} />;

  /* ───── NPCs (character nodes with field_character_type=false) ───── */
  if (key === 'npcs/n-list')     return <CharacterListScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-view')     return <CharacterDetailScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-validate') return <NpcValidatorScreen ctx={ictx} setCtx={set} />;

  /* ───── Settings (all config items → same screen, different tab) ───── */
  if (section.id === 'config') {
    const tabMap: Record<string, ScreenContext['settingsTab']> = {
      'c-view':     'view',
      'c-ai':       'ai',
      'c-rag':      'rag',
      'c-display':  'display',
      'c-paths':    'paths',
      'c-validate': 'validate',
      'c-save':     'save',
    };
    const settingsTab = tabMap[item.id] ?? 'view';
    return <SettingsScreen ctx={{ ...ictx, settingsTab }} setCtx={set} />;
  }

  /* ───── Model Profile ───── */
  if (section.id === 'model') return <ModelProfileScreen ctx={ictx} setCtx={set} />;

  /* ───── Tools & Batch ───── */
  if (section.id === 'tools') return <ToolsScreen ctx={ictx} setCtx={set} />;

  /* ───── Characters — party ───── */
  if (key === 'characters/party') return <CurrentPartyScreen ctx={ictx} setCtx={set} />;

  /* Fallback — loud placeholder so missing screens can't be shipped silently */
  return <PlaceholderScreen section={section} item={item} />;
}
