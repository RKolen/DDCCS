/**
 * DDCCS Console — ScreenRouter.
 *
 * Maps (section.id, item.id) -> the screen filling the ledger's action panel.
 * A dispatch table rather than per-route files, so screens share state via
 * `ctx`.
 *
 * NPCs are character nodes with field_character_type=false; `npcs/*` routes
 * query nodeCharacter filtered by that field.
 */

import * as React from 'react';
import type { MenuSection, MenuItem } from './menuData';

/* ────────────────────────────────────────────────────────────
   Shared screen context
   ──────────────────────────────────────────────────────────── */

export interface ScreenContext {
  storyIdx?: number;
  /** UUID of the story an activity row asked the reader to open. */
  storyId?: string;
  charIdx?: number;
  itemIdx?: number;
  /** Character screens show NPCs (characterType === false) when true. */
  npcMode?: boolean;
  /**
   * UUID of a character to select regardless of the screen's own roster order.
   * Set by deep links (`/?item=edit&char=…`) and by the completeness audit,
   * both of which know a character but not its index in a campaign-scoped list.
   */
  editCharId?: string;
  activeCampaignName?: string | null;
  /** UUID of the story arc a stories screen is focused on. */
  arcId?: string;
  settingsTab?: 'view' | 'ai' | 'rag' | 'display' | 'paths' | 'validate' | 'save';
  modelId?: string;
  /**
   * A queued job whose result the screen should pick back up and offer for
   * review. Set when the operator clicks through from an activity row.
   */
  reviewJobId?: string;
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
import { CreateCharacterScreen }        from './screens/CreateCharacterScreen';
import { CharacterEditScreen }          from './screens/CharacterEditScreen';
import { CharacterArcScreen }           from './screens/CharacterArcScreen';
import { CharacterDevelopmentScreen }   from './screens/CharacterDevelopmentScreen';
import { ItemListScreen }               from './screens/ItemListScreen';
import { ItemDetailScreen }             from './screens/ItemDetailScreen';
import { ItemRegistryScreen }           from './screens/ItemRegistryScreen';
import { BestiaryScreen }               from './screens/BestiaryScreen';
import { MonsterStatBlockScreen }       from './screens/MonsterStatBlockScreen';
import { EncounterSpotlightScreen }     from './screens/EncounterSpotlightScreen';
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
import { StoryArcScreen }               from './screens/StoryArcScreen';
import { SettingsScreen }               from './screens/SettingsScreen';
import { ModelProfileScreen }           from './screens/ModelProfileScreen';
import { ToolsScreen }                  from './screens/ToolsScreen';
import { NpcValidatorScreen }           from './screens/NpcValidatorScreen';
import { PortraitStudioScreen }         from './screens/PortraitStudioScreen';
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

  /* The route decides which roster a character screen shows, never the inherited
     context. npcMode survives in ctx across section switches (it is seeded from
     the landing section and set by activity rows), so a screen that merely
     forwards ctx would render the wrong roster — the Characters tab listing NPCs
     is the mirror of the NPC tab listing a player character. */
  const pcctx: ScreenContext = { ...ictx, npcMode: false };

  /* ───── Characters ───── */
  if (key === 'characters/list')         return <CharacterListScreen  ctx={pcctx} setCtx={set} />;
  if (key === 'characters/template')     return <CreateCharacterScreen ctx={pcctx} setCtx={set} />;
  if (key === 'characters/edit')         return <CharacterEditScreen  ctx={pcctx} setCtx={set} />;
  if (key === 'characters/view')         return <CharacterDetailScreen ctx={pcctx} setCtx={set} />;
  if (key === 'characters/consult')      return <ConsultScreen ctx={pcctx} setCtx={set} />;
  if (key === 'characters/completeness') return <NpcValidatorScreen ctx={{ ...pcctx, pcMode: true }} setCtx={set} />;
  if (key === 'characters/ascii')        return <PortraitStudioScreen ctx={pcctx} setCtx={set} />;
  if (key === 'characters/development')  return <CharacterDevelopmentScreen ctx={pcctx} setCtx={set} />;

  /* Arc hub + all four sub-actions — CharacterArcScreen dispatches internally
     via ctx.arcSubAction, set by its own buttons. The sidebar only surfaces the
     top-level 'arc' item, so we must NOT override arcSubAction from item.id
     (that would pin the screen to the hub and swallow in-screen navigation). */
  if (section.id === 'characters' && (item.id === 'arc' || item.id.startsWith('arc-'))) {
    return <CharacterArcScreen ctx={pcctx} setCtx={set} />;
  }

  /* ───── Stories ───── */
  if (key === 'stories/work-series') {
    const actionId = ictx.workSeriesAction as string | undefined;
    if (actionId === 's-view')  return <StoryDetailsScreen  ctx={ictx} setCtx={set} />;
    if (actionId === 's-notes') return <SessionNotesScreen  ctx={ictx} setCtx={set} />;
    if (actionId !== undefined) return <AiActionScreen      ctx={ictx} setCtx={set} />;
    return <StorySeriesWorkspaceScreen ctx={ictx} setCtx={set} />;
  }
  if (key === 'stories/read')        return <ReadStoryFileScreen ctx={ictx} setCtx={set} />;
  if (key === 'stories/timeline')    return <TimelineScreen ctx={ictx} setCtx={set} />;
  if (key === 'stories/new-series')  return <NewSeriesScreen ctx={ictx} setCtx={set} />;
  if (key === 'stories/arcs')        return <StoryArcScreen ctx={ictx} setCtx={set} />;

  /* ───── NPCs (character nodes with field_character_type=false) ─────
     Same screens as the characters/* twins, with npcMode set — an NPC is a
     character profile, so the tooling is identical. */
  if (key === 'npcs/n-list')     return <CharacterListScreen   ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-edit')     return <CharacterEditScreen   ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-view')     return <CharacterDetailScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-consult')  return <ConsultScreen         ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-ascii')    return <PortraitStudioScreen  ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  if (key === 'npcs/n-validate') return <NpcValidatorScreen    ctx={ictx} setCtx={set} />;

  /* Arc hub + sub-actions, same dispatch rule as characters/arc. */
  if (section.id === 'npcs' && (item.id === 'n-arc' || item.id.startsWith('arc-'))) {
    return <CharacterArcScreen ctx={{ ...ictx, npcMode: true }} setCtx={set} />;
  }

  /* ───── Spells ───── */
  if (key === 'spells/sp-list') return <SpellRegistryScreen ctx={ictx} setCtx={set} />;

  /* ───── Items ───── */
  if (key === 'items/i-list')     return <ItemListScreen     ctx={ictx} setCtx={set} />;
  if (key === 'items/i-view')     return <ItemDetailScreen   ctx={ictx} setCtx={set} />;
  if (key === 'items/i-validate') return <ItemRegistryScreen ctx={ictx} setCtx={set} />;

  /* ───── Monsters ───── */
  if (key === 'monsters/m-list')      return <BestiaryScreen           ctx={ictx} setCtx={set} />;
  if (key === 'monsters/m-view')      return <MonsterStatBlockScreen   ctx={ictx} setCtx={set} />;
  if (key === 'monsters/m-encounter') return <EncounterSpotlightScreen ctx={ictx} setCtx={set} />;

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
  if (key === 'characters/party') return <CurrentPartyScreen ctx={pcctx} setCtx={set} />;

  /* Fallback — loud placeholder so missing screens can't be shipped silently */
  return <PlaceholderScreen section={section} item={item} />;
}
