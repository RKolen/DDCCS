/**
 * DDCCS Console — menu data
 * --------------------------------------------------------------
 * Typed port of `menu/menu-data.jsx` from the design system project.
 * The CLI sections, items, campaigns, model profiles, and the
 * activity-log mock all flow through this single source of truth.
 *
 * Canonical reference (DO NOT diverge without updating both):
 *   /menu/menu-data.jsx  (in the design system repo)
 *
 * IMPORTANT — NPC/Character architecture (2026-05-16):
 *   NPCs are no longer a separate content type. They are character
 *   nodes (nodeCharacter) with the `field_character_type` field set
 *   to false/off. When querying Drupal, filter by:
 *     - Player characters: field_character_type = true
 *     - NPCs:             field_character_type = false
 *   The legacy `nodeNpc` GraphQL type should be considered deprecated.
 *   The `npcs` section in the console lists and views these filtered
 *   character nodes.
 *
 * When this is wired to Drupal:
 *   - `sections` stays static (it's the app's information architecture)
 *   - `campaigns` comes from the Campaign taxonomy term reference
 *   - `characters` comes from `node--character` (field_character_type=true,
 *                  filtered to active campaign)
 *   - `recentStories` comes from `node--story` ordered by `field_session_date`
 *   - `activityLog` comes from a websocket/SSE channel for AI job status
 */

/* ────────────────────────────────────────────────────────────
   Types
   ──────────────────────────────────────────────────────────── */

export type IconName =
  | 'char' | 'story' | 'read' | 'npc'
  | 'gear' | 'model' | 'tools'
  | 'sparkle' | 'chevron' | 'chevronDown' | 'chevronLeft'
  | 'search' | 'plus' | 'close'
  | 'play' | 'pause' | 'speaker' | 'image'
  | 'book' | 'flag' | 'scroll' | 'timeline'
  | 'spell' | 'grid' | 'list' | 'drawer';

export interface MenuItem {
  id: string;
  label: string;
  ai?: boolean;
  slow?: boolean;
  deprecated?: boolean;
  note?: string;
  hasSubmenu?: boolean;
  submenu?: MenuItem[];
}

export interface MenuSection {
  id: 'characters' | 'stories' | 'read' | 'npcs' | 'config' | 'model' | 'tools';
  label: string;
  glyph: string;
  icon: IconName;
  blurb: string;
  count?: number;
  items: MenuItem[];
}

export interface Campaign {
  id: string;
  name: string;
  stories: number;
  party: number;
  active: boolean;
}

export interface ModelProfile {
  id: string;
  name: string;
  task: string;
  active: boolean;
}

export interface UtilityCommand {
  cmd: string;
  label: string;
  ai?: boolean;
  slow?: boolean;
}

export type ActivityStatus = 'running' | 'done' | 'failed';
export type ActivityKind   = 'ai' | 'index' | 'batch';

export interface ActivityItem {
  kind: ActivityKind;
  status: ActivityStatus;
  label: string;
  detail: string;
  progress?: number;
  elapsed?: string;
}

export interface CharacterSummary {
  name: string;
  class: string;
  level: number;
  pronouns?: string;
}

export interface StorySummary {
  title: string;
  series: string;
  date: string;
}

export interface MenuData {
  campaigns: Campaign[];
  modelProfiles: ModelProfile[];
  sections: MenuSection[];
  utilityCommands: UtilityCommand[];
  characters: CharacterSummary[];
  recentStories: StorySummary[];
  activityLog: ActivityItem[];
}

/* ────────────────────────────────────────────────────────────
   Data (1:1 with menu-data.jsx — keep in sync)
   ──────────────────────────────────────────────────────────── */

export const MENU_DATA: MenuData = {
  campaigns: [
    { id: 'whispers', name: 'Whispers of the Sundered Crown', stories: 12, party: 4, active: true  },
    { id: 'ironroot', name: 'The Ironroot Pact',              stories:  7, party: 5, active: false },
    { id: 'mistveil', name: 'Mistveil Quest',                 stories:  3, party: 3, active: false },
  ],

  modelProfiles: [
    { id: 'claude-sonnet', name: 'Claude Sonnet 4.6',       task: 'story_generation', active: true  },
    { id: 'claude-haiku',  name: 'Claude Haiku 4.5',        task: 'analysis',         active: false },
    { id: 'local-llama',   name: 'Llama 3.1 70B (local)',   task: 'fallback',         active: false },
  ],

  sections: [
    {
      id: 'characters',
      label: 'Characters',
      glyph: 'C',
      icon: 'char',
      blurb: 'Profiles, arcs, and consultations',
      count: 6,
      items: [
        { id: 'list',     label: 'List Characters' },
        { id: 'edit',     label: 'Edit Character Profile' },
        { id: 'view',     label: 'View Character Details' },
        { id: 'consult',  label: 'Get Character Consultation', ai: true },
        { id: 'ascii',    label: 'Customize Portrait', deprecated: true, note: 'Replaced by ComfyUI' },
        { id: 'verify',   label: 'Verify Character Profile' },
        {
          id: 'arc', label: 'Character Arc Analysis', ai: true, hasSubmenu: true,
          submenu: [
            { id: 'arc-summary',  label: 'View character arc summary' },
            { id: 'arc-analyze',  label: 'Analyze story for character arc', ai: true },
            { id: 'arc-overview', label: 'View campaign arc overview' },
            { id: 'arc-export',   label: 'Export arc report to file' },
          ],
        },
        { id: 'template', label: 'Create Character from Template' },
      ],
    },
    {
      id: 'stories',
      label: 'Stories',
      glyph: 'S',
      icon: 'story',
      blurb: 'Sessions, series, timelines',
      count: 22,
      items: [
        { id: 'new-series',  label: 'Create New Story Series', ai: true },
        {
          id: 'work-series', label: 'Work with Story Series', hasSubmenu: true,
          submenu: [
            { id: 's-add',         label: 'Add New Story to Series',        ai: true },
            { id: 's-view',        label: 'View Story Details' },
            { id: 's-session',     label: 'Generate Session Results',       ai: true },
            { id: 's-chardev',     label: 'Generate Character Development', ai: true },
            { id: 's-analyze',     label: 'Analyze Story File',             ai: true },
            { id: 's-combat',      label: 'Convert Combat to Narrative',    ai: true },
            { id: 's-dc',          label: 'Get DC Suggestions',             ai: true },
            { id: 's-dm',          label: 'Get DM Narrative Suggestions',   ai: true },
            { id: 's-story-anal',  label: 'Story Analysis',                 ai: true, slow: true },
            { id: 's-char-anal',   label: 'Character Analysis',             ai: true, slow: true },
            { id: 's-amend',       label: 'Amend Story Character Actions' },
            { id: 's-notes',       label: 'Manage Session Notes' },
            { id: 's-suggest',     label: 'AI Story Suggestions',           ai: true },
          ],
        },
        { id: 'timeline', label: 'Timeline Tracking' },
        { id: 'spells',   label: 'Spell Registry' },
      ],
    },
    {
      id: 'read',
      label: 'Read Stories',
      glyph: 'R',
      icon: 'read',
      blurb: 'Player view — read aloud, generate art',
      count: 22,
      items: [
        { id: 'r-story',   label: 'Read Story File' },
        { id: 'r-char',    label: 'Read Character Profile' },
        { id: 'r-session', label: 'Read Session Results' },
        { id: 'r-dev',     label: 'Read Character Development' },
      ],
    },
    {
      /*
       * NPCs are character nodes (field_character_type = false).
       * Queries use nodeCharacter filtered by that field, not a
       * separate nodeNpc type. See module-level comment for details.
       */
      id: 'npcs',
      label: 'NPCs',
      glyph: 'N',
      icon: 'npc',
      blurb: 'Major antagonists, allies, factions',
      count: 14,
      items: [
        { id: 'n-list',     label: 'List Major NPCs' },
        { id: 'n-view',     label: 'View Major NPC Details' },
        { id: 'n-validate', label: 'Validate NPC Files' },
      ],
    },
    {
      id: 'config',
      label: 'Settings',
      glyph: 'Σ',
      icon: 'gear',
      blurb: 'AI, RAG, display, paths',
      items: [
        { id: 'c-view',     label: 'View Current Configuration' },
        { id: 'c-ai',       label: 'Configure AI Settings' },
        { id: 'c-rag',      label: 'Configure RAG Settings' },
        { id: 'c-display',  label: 'Configure Display Settings' },
        { id: 'c-paths',    label: 'Configure Path Settings' },
        { id: 'c-save',     label: 'Save Configuration' },
        { id: 'c-validate', label: 'Validate Configuration' },
      ],
    },
    {
      id: 'model',
      label: 'Model Profile',
      glyph: 'M',
      icon: 'model',
      blurb: 'Switch active LLM profile',
      items: [
        { id: 'm-switch', label: 'Switch Model Profile' },
      ],
    },
    {
      id: 'tools',
      label: 'Tools & Batch',
      glyph: 'T',
      icon: 'tools',
      blurb: 'History, batch operations',
      items: [
        { id: 't-recent', label: 'View Recent History' },
        { id: 't-search', label: 'Search History' },
        { id: 't-stats',  label: 'History Statistics' },
        { id: 't-clear',  label: 'Clear History' },
        { id: 't-level',  label: 'Batch Level-Up Characters', slow: true },
        { id: 't-item',   label: 'Batch Add Item to Characters' },
      ],
    },
  ],

  utilityCommands: [
    { cmd: '--reindex',       label: 'Reindex vector DB', slow: true },
    { cmd: '--milvus-status', label: 'Milvus health' },
    { cmd: '--sync-drupal',   label: 'Sync to Drupal' },
  ],

  characters: [
    { name: 'Vesper Ashwhile',        class: 'Warlock', level: 8, pronouns: 'she/her'   },
    { name: 'Brynn Coldhammer',       class: 'Cleric',  level: 8, pronouns: 'they/them' },
    { name: 'Kael of the Blackmarsh', class: 'Ranger',  level: 7 },
    { name: 'Mira Quickfingers',      class: 'Rogue',   level: 8, pronouns: 'she/her'   },
  ],

  recentStories: [
    { title: 'The Bell of Vellishar',    series: 'Whispers of the Sundered Crown', date: '3 days ago'  },
    { title: 'Smoke at the Northgate',   series: 'Whispers of the Sundered Crown', date: '1 week ago'  },
    { title: 'A Ledger of Names',        series: 'Whispers of the Sundered Crown', date: '2 weeks ago' },
  ],

  activityLog: [
    { kind: 'ai',    status: 'running', label: 'Generating session results',      detail: 'Whispers · The Bell of Vellishar', progress: 0.62, elapsed: '00:42' },
    { kind: 'ai',    status: 'done',    label: 'Story continuation',               detail: 'Mistveil · 1,840 tokens · 12s' },
    { kind: 'index', status: 'done',    label: 'Reindex vector DB',                detail: '24 files · 18s' },
    { kind: 'batch', status: 'done',    label: 'Batch level-up: 4 characters +1',  detail: '4/4 succeeded' },
    { kind: 'ai',    status: 'failed',  label: 'Arc analysis: Vesper Ashwhile',    detail: 'AI client unavailable — check config' },
  ],
};
