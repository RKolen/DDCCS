/**
 * DDCCS Console — menu data
 * --------------------------------------------------------------
 * The console's information architecture: which sections exist, which actions
 * each one offers, and the utility command list. Originally a typed port of
 * `menu/menu-data.jsx` from the design system project.
 *
 * This file holds **structure only**. It once also carried the design mock's
 * sample campaigns, characters, recent stories, model profiles, and activity
 * log; those are gone. Content comes from Drupal:
 *
 *   campaigns / characters / stories -> ConsoleContext (index.tsx page query)
 *   activity log                     -> utils/aiJobs, polled from the queue
 *
 * Do not reintroduce sample content here. A screen that renders invented
 * characters is indistinguishable from one that lost its data connection.
 *
 * IMPORTANT — the `read` section is gone (2026-08-16):
 *   It carried four items backed by one unique screen. `r-story` and
 *   `r-session` routed to the same component with the same context, and
 *   `r-char` was byte-identical to `characters/view`. Its two real
 *   destinations now live where they belong:
 *     r-story -> `stories/read`            (ReadStoryFileScreen)
 *     r-dev   -> `characters/development`  (CharacterDevelopmentScreen)
 *   Do not reintroduce it. The public reader at `/stories/` and
 *   `templates/story.tsx` is a separate surface and is unaffected.
 *
 * IMPORTANT — NPC/Character architecture (2026-05-16):
 *   NPCs are no longer a separate content type. They are character
 *   nodes (nodeCharacter) with the `field_character_type` field set
 *   to false/off. When querying Drupal, filter by:
 *     - Player characters: field_character_type = true
 *     - NPCs:             field_character_type = false
 *   The legacy `nodeNpc` GraphQL type should be considered deprecated.
 *   The `npcs` section offers the same actions as `characters`, run against
 *   the filtered roster; `field_recurring` marks the NPCs that earn a full
 *   character profile.
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
  id: 'characters' | 'stories' | 'npcs' | 'items' | 'spells' | 'monsters' | 'config' | 'model' | 'tools';
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

export interface UtilityCommand {
  cmd: string;
  label: string;
  ai?: boolean;
  slow?: boolean;
}

/**
 * `queued` and `running` are deliberately separate: a job waiting for the host
 * processor and a job the host is actually working on look identical otherwise,
 * and a pulsing "busy" row for work nothing has started yet is a lie.
 */
export type ActivityStatus = 'queued' | 'running' | 'done' | 'failed';
export type ActivityKind = 'ai' | 'index' | 'batch';

/**
 * The console screen an activity row leads to.
 *
 * An activity row is not just a status line: a finished job's output is waiting
 * on a decision, and this is the address of the screen where that decision gets
 * made. Fed to StatelyLedger's `_jumpTo` when the row is opened.
 */
export interface ActivityTarget {
  sectionId: MenuSection['id'];
  itemId: string;
  /** Index into that screen's roster, for the per-character screens. */
  charIdx?: number;
  /** True when the target roster is the NPC one rather than the party. */
  npcMode?: boolean;
}

export interface ActivityItem {
  kind: ActivityKind;
  status: ActivityStatus;
  label: string;
  detail: string;
  progress?: number;
  elapsed?: string;
  /** The queue job behind this row, when there is one. */
  jobId?: string;
  /** Where this row's work can be inspected or reviewed. */
  target?: ActivityTarget;
  /**
   * UUID of the character this row is about. The console resolves it to a
   * roster index; pages outside the console have no roster, so they deep-link
   * to `/?char=…` with it instead.
   */
  subjectId?: string;
  /** True when the job finished and its result has not been accepted yet. */
  needsReview?: boolean;
  /**
   * True when the job was claimed but its worker stopped responding. It is not
   * running and will not finish on its own, so the row offers a requeue.
   */
  stalled?: boolean;
}

/**
 * The console's static menu taxonomy.
 *
 * Structure only — sections, items, and the utility command list. Every piece
 * of campaign content (characters, stories, campaigns, activity) comes from
 * Drupal via ConsoleContext. This file previously also carried sample
 * characters, stories, campaigns, and an activity log copied from the design
 * mock; nothing read them, and they were removed so nobody wires them back up
 * by accident.
 */
export interface MenuData {
  sections: MenuSection[];
  utilityCommands: UtilityCommand[];
}

/* ────────────────────────────────────────────────────────────
   Data — the information architecture, and nothing else
   ──────────────────────────────────────────────────────────── */

export const MENU_DATA: MenuData = {
  sections: [
    {
      id: 'characters',
      label: 'Characters',
      glyph: 'C',
      icon: 'char',
      blurb: 'Profiles, arcs, and consultations',
      count: 6,
      items: [
        { id: 'list', label: 'List Characters' },
        { id: 'edit', label: 'Edit Character Profile' },
        { id: 'view', label: 'View Character Details' },
        { id: 'consult', label: 'Get Character Consultation', ai: true },
        { id: 'ascii', label: 'Customize Portrait', ai: true, note: 'ComfyUI portrait studio' },
        { id: 'completeness', label: 'Profile Completeness' },
        {
          id: 'arc', label: 'Character Arc Analysis', ai: true, hasSubmenu: true,
          submenu: [
            { id: 'arc-summary', label: 'View character arc summary' },
            { id: 'arc-analyze', label: 'Analyze story for character arc', ai: true },
            { id: 'arc-overview', label: 'View campaign arc overview' },
            { id: 'arc-export', label: 'Export arc report to file' },
          ],
        },
        { id: 'development', label: 'Character Development' },
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
        { id: 'new-series', label: 'Create New Story Series', ai: true },
        {
          id: 'work-series', label: 'Work with Story Series', hasSubmenu: true,
          submenu: [
            { id: 's-add', label: 'Add New Story to Series', ai: true },
            { id: 's-view', label: 'View Story Details' },
            { id: 's-session', label: 'Generate Session Results', ai: true },
            { id: 's-chardev', label: 'Generate Character Development', ai: true },
            { id: 's-analyze', label: 'Analyze Story File', ai: true },
            { id: 's-combat', label: 'Convert Combat to Narrative', ai: true },
            { id: 's-dc', label: 'Get DC Suggestions', ai: true },
            { id: 's-dm', label: 'Get DM Narrative Suggestions', ai: true },
            { id: 's-story-anal', label: 'Story Analysis', ai: true, slow: true },
            { id: 's-char-anal', label: 'Character Analysis', ai: true, slow: true },
            { id: 's-amend', label: 'Amend Story Character Actions' },
            { id: 's-notes', label: 'Manage Session Notes' },
            { id: 's-suggest', label: 'AI Story Suggestions', ai: true },
          ],
        },
        { id: 'read', label: 'Read Story File' },
        { id: 'timeline', label: 'Timeline Tracking' },
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
      /*
       * The same action set as Characters. An NPC is a character profile that
       * happens to carry field_character_type = false, and field_recurring is
       * what marks the ones that earn a full fill - so every tool that works on
       * a PC works here too, on the same screens with npcMode set.
       */
      items: [
        { id: 'n-list', label: 'List Major NPCs' },
        { id: 'n-edit', label: 'Edit NPC Profile' },
        { id: 'n-view', label: 'View Major NPC Details' },
        { id: 'n-consult', label: 'Get NPC Consultation', ai: true },
        { id: 'n-ascii', label: 'Customize Portrait', ai: true, note: 'ComfyUI portrait studio' },
        { id: 'n-validate', label: 'Profile Completeness' },
        {
          id: 'n-arc', label: 'Character Arc Analysis', ai: true, hasSubmenu: true,
          submenu: [
            { id: 'arc-summary', label: 'View character arc summary' },
            { id: 'arc-analyze', label: 'Analyze story for character arc', ai: true },
            { id: 'arc-overview', label: 'View campaign arc overview' },
            { id: 'arc-export', label: 'Export arc report to file' },
          ],
        },
      ],
    },
    {
      id: 'items',
      label: 'Items',
      glyph: 'I',
      icon: 'grid',
      blurb: 'Registry, validation, loot tracking',
      items: [
        { id: 'i-list',     label: 'Loot Vault' },
        { id: 'i-view',     label: 'Item Sheet' },
        { id: 'i-validate', label: 'Validate Registry' },
      ],
    },
    {
      /*
       * Spells are `node--spell` content, a compendium in their own right —
       * not a property of a story. This section was `stories/spells` until it
       * was promoted alongside a `/spells/` topbar link (2026-08-23).
       *
       * The item list is deliberately minimal. Flesh it out as the screens
       * are designed; anything added here without a ScreenRouter case falls
       * through to PlaceholderScreen, which says so loudly.
       */
      id: 'spells',
      label: 'Spells',
      glyph: 'A',
      icon: 'spell',
      blurb: 'Compendium, schools, slot tracking',
      items: [
        { id: 'sp-list', label: 'Spell Compendium' },
      ],
    },
    {
      id: 'monsters',
      label: 'Monsters',
      glyph: 'M',
      icon: 'npc',
      blurb: 'Bestiary, stat blocks, encounter tools',
      items: [
        { id: 'm-list',      label: 'Bestiary' },
        { id: 'm-view',      label: 'Monster Stat Block' },
        { id: 'm-encounter', label: 'Encounter Spotlight' },
      ],
    },
    {
      id: 'config',
      label: 'Settings',
      glyph: 'Σ',
      icon: 'gear',
      blurb: 'AI, RAG, display, paths',
      items: [
        { id: 'c-view', label: 'View Current Configuration' },
        { id: 'c-ai', label: 'Configure AI Settings' },
        { id: 'c-rag', label: 'Configure RAG Settings' },
        { id: 'c-display', label: 'Configure Display Settings' },
        { id: 'c-paths', label: 'Configure Path Settings' },
        { id: 'c-save', label: 'Save Configuration' },
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
        { id: 't-stats', label: 'History Statistics' },
        { id: 't-clear', label: 'Clear History' },
        { id: 't-level', label: 'Batch Level-Up Characters', slow: true },
        { id: 't-item', label: 'Batch Add Item to Characters' },
      ],
    },
  ],

  utilityCommands: [
    { cmd: '--reindex', label: 'Reindex vector DB', slow: true },
    { cmd: '--milvus-status', label: 'Milvus health' },
  ],
};
