import React, { useState } from 'react';
import type { HeadFC } from 'gatsby';
import * as styles from './console.module.css';

// ── Console-local colour tokens ───────────────────────────────────────────────
// These extend the global tokens with desk-specific values.
// They are injected on the root shell element via inline style so CSS Modules
// can reference them without a separate :root override.

// ── Data ──────────────────────────────────────────────────────────────────────

const SECTIONS = [
  {
    id: 'read',
    label: 'Read Stories',
    blurb: 'Player view — read aloud, generate art',
    items: [
      { id: 'r-story',   label: 'Read Story File' },
      { id: 'r-char',    label: 'Read Character Profile' },
      { id: 'r-session', label: 'Read Session Results' },
      { id: 'r-dev',     label: 'Read Character Development' },
    ],
  },
  {
    id: 'characters',
    label: 'Characters',
    blurb: 'Profiles, arcs, and consultations',
    items: [
      { id: 'list',     label: 'List Characters' },
      { id: 'edit',     label: 'Edit Character Profile' },
      { id: 'view',     label: 'View Character Details' },
      { id: 'consult',  label: 'Get Character Consultation', ai: true as const },
      { id: 'ascii',    label: 'Customize Portrait', deprecated: true as const, note: 'Replaced by ComfyUI' },
      { id: 'verify',   label: 'Verify Character Profile' },
      { id: 'arc',      label: 'Character Arc Analysis', ai: true as const },
      { id: 'template', label: 'Create Character from Template' },
    ],
  },
  {
    id: 'stories',
    label: 'Stories',
    blurb: 'Sessions, series, timelines',
    items: [
      { id: 'new-series',  label: 'Create New Story Series', ai: true as const },
      { id: 'work-series', label: 'Work with Story Series' },
      { id: 'timeline',    label: 'Timeline Tracking' },
      { id: 'spells',      label: 'Spell Registry' },
    ],
  },
  {
    id: 'npcs',
    label: 'NPCs',
    blurb: 'Major antagonists, allies, factions',
    items: [
      { id: 'n-list',     label: 'List Major NPCs' },
      { id: 'n-view',     label: 'View Major NPC Details' },
      { id: 'n-validate', label: 'Validate NPC Files' },
    ],
  },
  {
    id: 'config',
    label: 'Settings',
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
    blurb: 'Switch active LLM profile',
    items: [
      { id: 'm-switch', label: 'Switch Model Profile' },
    ],
  },
  {
    id: 'tools',
    label: 'Tools & Batch',
    blurb: 'History, batch operations',
    items: [
      { id: 't-recent', label: 'View Recent History' },
      { id: 't-search', label: 'Search History' },
      { id: 't-stats',  label: 'History Statistics' },
      { id: 't-clear',  label: 'Clear History' },
      { id: 't-level',  label: 'Batch Level-Up Characters', slow: true as const },
      { id: 't-item',   label: 'Batch Add Item to Characters' },
    ],
  },
] as const;

// ── Types ─────────────────────────────────────────────────────────────────────

type SectionTuple = typeof SECTIONS;
type SectionDef = SectionTuple[number];
type ItemDef = SectionDef['items'][number];

type ActivityStatus = 'running' | 'done' | 'failed';

interface ActivityEntry {
  id: string;
  status: ActivityStatus;
  label: string;
  age: string;
}

// ── Tab glyphs ────────────────────────────────────────────────────────────────

const SECTION_GLYPHS: Record<string, string> = {
  read:       'C',
  characters: 'S',
  stories:    'R',
  npcs:       'N',
  config:     'Σ',
  model:      'M',
  tools:      'T',
};

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_CAMPAIGNS: ReadonlyArray<{ id: string; label: string; active: boolean }> = [
  { id: 'nb',        label: 'New Beginnings',  active: true  },
  { id: 'ironroot',  label: 'The Ironroot Pact', active: false },
  { id: 'mistveil',  label: 'Mistveil Quest',  active: false },
];

const MOCK_STORIES: ReadonlyArray<{ id: string; num: string; title: string; body: string }> = [
  {
    id: 's-001',
    num: '001',
    title: 'The Bell at Bree',
    body: 'The Prancing Pony smelled of old ale and older secrets as the party slipped through its crooked door. A hooded stranger watched from the far corner, fingers curled around an untouched mug. Before the last candle guttered out, three purses had been cut and one name had been whispered that none of them expected to hear again.',
  },
  {
    id: 's-002',
    num: '002',
    title: 'Shadows at Weathertop',
    body: 'Rain had turned the Greenway to a river of mud when the silhouette of Amon Sûl rose against the bruised sky. The ruins held something older than the stones — a cold that did not belong to the season, and a presence that pressed against the edge of thought like a blade not yet drawn. The fire they lit that night was less a comfort than a promise of things to come.',
  },
  {
    id: 's-003',
    num: '003',
    title: 'The Ford of Bruinen',
    body: 'The ford ran shallow but the crossing felt impossible, as though the water itself had been instructed to delay them. Hoofbeats thundered on stone behind — nine riders whose breath did not make mist in the cold air. Then the river rose, white and furious, and for one perfect moment the pursuit ended in a roar that swallowed all other sound.',
  },
];

const MOCK_CHARACTERS: ReadonlyArray<{
  id: string;
  name: string;
  cls: string;
  level: number;
  stat: string;
  mod: string;
}> = [
  { id: 'aragorn', name: 'Aragorn',  cls: 'Ranger', level: 10, stat: 'Dex', mod: '+3' },
  { id: 'frodo',   name: 'Frodo',    cls: 'Rogue',  level:  6, stat: 'Dex', mod: '+4' },
  { id: 'gandalf', name: 'Gandalf',  cls: 'Wizard', level: 20, stat: 'Int', mod: '+5' },
];

const CONFIG_TABS = ['View', 'AI', 'RAG', 'Display', 'Paths', 'Validate'] as const;
type ConfigTab = typeof CONFIG_TABS[number];

const CONFIG_ROWS: Record<ConfigTab, ReadonlyArray<{ key: string; value: string }>> = {
  View: [
    { key: 'profile',     value: 'narrative' },
    { key: 'theme',       value: 'dark-parchment' },
    { key: 'log_level',   value: 'info' },
    { key: 'last_saved',  value: '2026-05-14T09:41:00Z' },
    { key: 'config_path', value: '~/.config/ddccs/config.json' },
  ],
  AI: [
    { key: 'model',       value: 'claude-sonnet-4-5' },
    { key: 'profile',     value: 'narrative' },
    { key: 'temperature', value: '0.7' },
    { key: 'max_tokens',  value: '8192' },
    { key: 'base_url',    value: 'https://api.anthropic.com' },
  ],
  RAG: [
    { key: 'backend',      value: 'milvus' },
    { key: 'milvus_host',  value: 'localhost' },
    { key: 'milvus_port',  value: '19530' },
    { key: 'collection',   value: 'lore_index_v3' },
    { key: 'top_k',        value: '8' },
  ],
  Display: [
    { key: 'rich_enabled', value: 'true' },
    { key: 'pager',        value: 'less' },
    { key: 'color_depth',  value: '256' },
    { key: 'line_width',   value: '100' },
    { key: 'tts_enabled',  value: 'true' },
  ],
  Paths: [
    { key: 'game_data',   value: '/home/raymond-kolen/Projects/New Beginnings/game_data' },
    { key: 'campaigns',   value: '{game_data}/campaigns' },
    { key: 'characters',  value: '{game_data}/characters' },
    { key: 'npcs',        value: '{game_data}/npcs' },
    { key: 'items',       value: '{game_data}/items' },
  ],
  Validate: [
    { key: 'last_run',     value: '2026-05-14T08:15:00Z' },
    { key: 'characters',   value: '3 valid, 0 errors' },
    { key: 'npcs',         value: '12 valid, 0 errors' },
    { key: 'items',        value: '47 valid, 0 errors' },
    { key: 'config_schema', value: 'OK' },
  ],
};

const INITIAL_ACTIVITY: ReadonlyArray<ActivityEntry> = [
  { id: 'a1', status: 'running', label: 'Generating story analysis…',       age: 'now'  },
  { id: 'a2', status: 'done',    label: 'Character arc report — Aragorn',   age: '3m ago' },
  { id: 'a3', status: 'failed',  label: 'Milvus connection timed out',            age: '7m ago' },
  { id: 'a4', status: 'done',    label: 'Session results generated',              age: '12m ago' },
];

// ── TopBar ────────────────────────────────────────────────────────────────────

interface TopBarProps {
  onModelClick: () => void;
}

function TopBar({ onModelClick }: TopBarProps): React.ReactElement {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const toggleDropdown = (): void => setDropdownOpen(o => !o);
  const closeDropdown  = (): void => setDropdownOpen(false);

  return (
    <header className={styles.topbar}>
      {/* Brand */}
      <div className={styles.brand}>
        <span className={styles.brandMark}>DD</span>
        <span className={styles.brandName}>DDCCS</span>
        <span className={styles.brandSub}>Campaign Console</span>
      </div>

      {/* Campaign chip */}
      <div className={styles.campaignChipWrap}>
        <button
          type="button"
          className={styles.campaignChip}
          onClick={toggleDropdown}
          aria-haspopup="listbox"
          aria-expanded={dropdownOpen}
        >
          <span className={styles.campaignStatus} aria-hidden="true" />
          <span className={styles.campaignChipMeta}>
            <span className={styles.campaignChipEyebrow}>Active</span>
            <span className={styles.campaignChipName}>New Beginnings</span>
          </span>
          <span className={styles.campaignChipStats}>12 stories &middot; 3 party</span>
          <span className={styles.campaignChipArrow} aria-hidden="true">&#8964;</span>
        </button>

        {dropdownOpen && (
          <ul
            role="listbox"
            aria-label="Switch campaign"
            className={styles.campaignDropdown}
          >
            {MOCK_CAMPAIGNS.map(c => (
              <li key={c.id} role="option" aria-selected={c.active}>
                <button
                  type="button"
                  className={`${styles.campaignOption}${c.active ? ` ${styles.campaignOptionActive}` : ''}`}
                  onClick={closeDropdown}
                >
                  {c.active && (
                    <span className={styles.campaignCheck} aria-hidden="true">&#10003;</span>
                  )}
                  {!c.active && <span className={styles.campaignCheckPlaceholder} />}
                  {c.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Model button */}
      <button
        type="button"
        className={styles.modelBtn}
        onClick={onModelClick}
        title="Switch model profile"
      >
        Claude Sonnet &#xB7; Narrative
      </button>
    </header>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

interface SidebarProps {
  activeSectionId: string;
  onSelectSection: (id: string) => void;
}

const UTILITY_CMDS = ['--reindex', '--milvus-status', '--sync-drupal'] as const;

function Sidebar({ activeSectionId, onSelectSection }: SidebarProps): React.ReactElement {
  return (
    <nav className={styles.sidebar} aria-label="Console sections">
      <ul className={styles.sidebarList} role="tablist">
        {SECTIONS.map(section => {
          const isActive = section.id === activeSectionId;
          const glyph    = SECTION_GLYPHS[section.id] ?? '?';
          return (
            <li key={section.id} role="presentation">
              <button
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`${styles.sidebarTab}${isActive ? ` ${styles.sidebarTabActive}` : ''}`}
                onClick={() => onSelectSection(section.id)}
              >
                <span className={styles.sidebarGlyph} aria-hidden="true">{glyph}</span>
                <span className={styles.sidebarLabel}>{section.label}</span>
              </button>
            </li>
          );
        })}
      </ul>

      <div className={styles.utilitySection}>
        <span className={styles.utilityHeading}>Utility</span>
        {UTILITY_CMDS.map(cmd => (
          <button key={cmd} type="button" className={styles.utilityBtn}>
            {cmd}
          </button>
        ))}
      </div>
    </nav>
  );
}

// ── Type guards (shared by ActionPane and screens) ────────────────────────────

type GenericItem = {
  id: string;
  label: string;
  ai?: true;
  slow?: true;
  deprecated?: true;
  note?: string;
};

function isAiItem(item: ItemDef): item is ItemDef & { ai: true } {
  return 'ai' in item && item.ai === true;
}

function isSlowItem(item: ItemDef): item is ItemDef & { slow: true } {
  return 'slow' in item && (item as GenericItem).slow === true;
}

function isDeprecatedItem(item: ItemDef): item is ItemDef & { deprecated: true } {
  return 'deprecated' in item && (item as GenericItem).deprecated === true;
}

// ── Screens ───────────────────────────────────────────────────────────────────

// -- GenericActionScreen

interface GenericActionScreenProps {
  section: SectionDef;
  item: ItemDef;
}

function GenericActionScreen({ section, item }: GenericActionScreenProps): React.ReactElement {
  const hasAi = isAiItem(item);
  return (
    <div className={styles.genericScreen}>
      <span className={styles.screenEyebrow}>{section.label}</span>
      <h2 className={styles.screenHeading}>{item.label}</h2>
      {hasAi && (
        <p className={styles.screenAiNote}>
          Uses the active model profile. Result streams to activity drawer.
        </p>
      )}
      <button type="button" className={styles.runBtn}>
        Run
      </button>
    </div>
  );
}

// -- ReadStoryFileScreen

function ReadStoryFileScreen(): React.ReactElement {
  const [activeStoryId, setActiveStoryId] = useState<string>(MOCK_STORIES[0].id);
  const [narrating, setNarrating]   = useState(false);
  const [artState, setArtState]     = useState<'idle' | 'running' | 'done'>('idle');

  const story = MOCK_STORIES.find(s => s.id === activeStoryId) ?? MOCK_STORIES[0];

  const toggleNarrate = (): void => setNarrating(n => !n);
  const generateArt   = (): void => {
    if (artState === 'running') return;
    setArtState('running');
    setTimeout(() => setArtState('done'), 1800);
  };

  const narrateLabel = narrating ? 'Listening…' : 'Narrate';
  const artLabel     =
    artState === 'idle'    ? 'Generate Art' :
    artState === 'running' ? 'Conjuring…' :
    'View Art';

  return (
    <div className={styles.readScreen}>
      {/* Story picker */}
      <aside className={styles.storyPicker}>
        <span className={styles.pickerEyebrow}>Story Files</span>
        <ul className={styles.pickerList}>
          {MOCK_STORIES.map((s, idx) => (
            <li key={s.id}>
              <button
                type="button"
                className={`${styles.pickerItem}${s.id === activeStoryId ? ` ${styles.pickerItemActive}` : ''}`}
                onClick={() => setActiveStoryId(s.id)}
              >
                <span className={styles.pickerNum}>{String(idx + 1).padStart(3, '0')}</span>
                <span className={styles.pickerLabel}>{s.title}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      {/* Reader area */}
      <div className={styles.storyReader}>
        <span className={styles.storyReaderChip}>Story {story.num}</span>
        <h2 className={styles.storyReaderTitle}>{story.title}</h2>
        <div className={styles.storyReaderMeta}>
          <span>New Beginnings Campaign</span>
          <span className={styles.readerMetaDot}>&middot;</span>
          <span>3 days ago</span>
          <span className={styles.readerMetaDot}>&middot;</span>
          <span>&#126;5 min read</span>
        </div>
        <p className={styles.storyReaderBody}>{story.body}</p>

        <div className={styles.storyMedallions} role="group" aria-label={`Actions for ${story.title}`}>
          {/* Narrate */}
          <button
            type="button"
            className={`${styles.storyMedallion}${narrating ? ` ${styles.storyMedallionActive}` : ''}`}
            onClick={toggleNarrate}
            title={narrateLabel}
            aria-pressed={narrating}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              className={styles.medallionSvg}
            >
              <path d="M4 9h3l5-4v14l-5-4H4z" />
              <path d="M16 9c1.2 1.2 1.8 2 1.8 3s-.6 1.8-1.8 3" />
              {narrating && <path d="M19 6c2 2 3 4 3 6s-1 4-3 6" />}
            </svg>
            <span className={styles.medallionLabel}>{narrateLabel}</span>
          </button>

          {/* Generate Art */}
          <button
            type="button"
            className={`${styles.storyMedallion} ${styles.storyMedallionAi}${artState === 'done' ? ` ${styles.storyMedallionDone}` : ''}`}
            onClick={generateArt}
            disabled={artState === 'running'}
            title={artLabel}
          >
            {artState === 'running' ? (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
                className={styles.medallionSvg}
              >
                <circle
                  cx="12"
                  cy="12"
                  r="8"
                  strokeDasharray="14 8"
                  className={styles.medallionSpinner}
                />
              </svg>
            ) : (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
                className={styles.medallionSvg}
              >
                <path d="M12 2l1.5 4.5H18l-3.75 2.75L15.75 14 12 11.25 8.25 14l1.5-4.75L6 6.5h4.5z" />
              </svg>
            )}
            <span className={styles.medallionLabel}>{artLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// -- ListCharactersScreen

interface ListCharactersScreenProps {
  onViewCharacter: () => void;
}

function ListCharactersScreen({ onViewCharacter }: ListCharactersScreenProps): React.ReactElement {
  return (
    <div className={styles.charScreen}>
      <span className={styles.screenEyebrow}>Characters</span>
      <h2 className={styles.screenHeading}>List Characters</h2>
      <div className={styles.charGrid}>
        {MOCK_CHARACTERS.map(c => (
          <div key={c.id} className={styles.charCard}>
            <span className={styles.charCardName}>{c.name}</span>
            <span className={styles.charCardClass}>
              {c.cls} {c.level} &middot; {c.stat} {c.mod}
            </span>
            <button
              type="button"
              className={styles.charCardBtn}
              onClick={onViewCharacter}
            >
              View Details
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// -- SettingsScreen

function SettingsScreen(): React.ReactElement {
  const [activeTab, setActiveTab] = useState<ConfigTab>('View');
  const rows = CONFIG_ROWS[activeTab];

  return (
    <div className={styles.settingsScreen}>
      <span className={styles.screenEyebrow}>Settings</span>
      <h2 className={styles.screenHeading}>Configuration</h2>

      <div className={styles.settingsTabs} role="tablist">
        {CONFIG_TABS.map(tab => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={tab === activeTab}
            className={`${styles.settingsTab}${tab === activeTab ? ` ${styles.settingsTabActive}` : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className={styles.settingsRows}>
        {rows.map(row => (
          <div key={row.key} className={styles.settingsRow}>
            <span className={styles.settingsKey}>{row.key}</span>
            <span className={styles.settingsValue}>{row.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── ActionPane (replaces separate DetailColumn + ActionColumn) ────────────────

interface ActionPaneProps {
  section: SectionDef;
  activeItemId: string;
  item: ItemDef;
  onSelectItem: (id: string) => void;
  onViewCharacter: () => void;
}

function ActionPane({
  section,
  activeItemId,
  item,
  onSelectItem,
  onViewCharacter,
}: ActionPaneProps): React.ReactElement {
  const aiCount = section.items.filter(it => isAiItem(it)).length;

  const screenContent = (): React.ReactElement => {
    if (section.id === 'read' && item.id === 'r-story') {
      return <ReadStoryFileScreen />;
    }
    if (section.id === 'characters' && item.id === 'list') {
      return <ListCharactersScreen onViewCharacter={onViewCharacter} />;
    }
    if (section.id === 'config') {
      return <SettingsScreen />;
    }
    return <GenericActionScreen section={section} item={item} />;
  };

  return (
    <main className={styles.actionPane} aria-label={`${section.label} — ${item.label}`}>
      <div className={styles.actionHeader}>
        <div className={styles.actionHeaderTop}>
          <div className={styles.actionHeaderText}>
            <span className={styles.actionEyebrow}>{section.label}</span>
            <h2 className={styles.actionTitle}>{item.label}</h2>
          </div>
          <span className={styles.actionHeaderMeta}>
            {section.items.length} actions
            {aiCount > 0 && (
              <><span className={styles.dotSep}>&middot;</span>{aiCount} AI-powered</>
            )}
          </span>
        </div>

        <nav className={styles.actionTabs} aria-label={`${section.label} actions`}>
          {section.items.map((it, idx) => {
            const isActive     = it.id === activeItemId;
            const hasAi        = isAiItem(it);
            const hasSlow      = isSlowItem(it);
            const hasDeprecated = isDeprecatedItem(it);
            const num          = String(idx + 1).padStart(2, '0');

            return (
              <button
                key={it.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`${styles.actionTab}${isActive ? ` ${styles.actionTabActive}` : ''}${hasDeprecated ? ` ${styles.actionTabDeprecated}` : ''}`}
                onClick={() => onSelectItem(it.id)}
              >
                <span className={styles.actionTabNum}>{num}</span>
                <span>{it.label}</span>
                <span className={styles.actionTabTags}>
                  {hasAi && <span className={styles.aiTag} title="AI-powered">{'✦'} AI</span>}
                  {hasSlow && <span className={styles.slowTag}>slow</span>}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className={styles.actionBody}>
        {screenContent()}
      </div>
    </main>
  );
}

// ── ActivityDrawer ────────────────────────────────────────────────────────────

function ActivityDrawer(): React.ReactElement {
  const [expanded, setExpanded] = useState(true);
  const entries: ReadonlyArray<ActivityEntry> = INITIAL_ACTIVITY;

  return (
    <div className={`${styles.drawer}${expanded ? ` ${styles.drawerExpanded}` : ''}`}>
      <button
        type="button"
        className={styles.drawerToggle}
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse activity drawer' : 'Expand activity drawer'}
      >
        {expanded
          ? <span aria-hidden="true">&#8250;</span>
          : <span aria-hidden="true">&#8249;</span>
        }
      </button>

      {expanded ? (
        <div className={styles.drawerContent}>
          <span className={styles.drawerHeading}>Activity</span>
          <ul className={styles.drawerList}>
            {entries.map(entry => (
              <li key={entry.id} className={styles.drawerEntry}>
                <span
                  className={`${styles.drawerIcon} ${
                    entry.status === 'running' ? styles.drawerIconRunning :
                    entry.status === 'done'    ? styles.drawerIconDone    :
                    styles.drawerIconFailed
                  }`}
                  aria-label={entry.status}
                >
                  {entry.status === 'running' && <span className={styles.drawerSpinner} aria-hidden="true" />}
                  {entry.status === 'done'    && <span aria-hidden="true">&#10003;</span>}
                  {entry.status === 'failed'  && <span aria-hidden="true">&#10007;</span>}
                </span>
                <span className={styles.drawerEntryBody}>
                  <span className={styles.drawerEntryLabel}>{entry.label}</span>
                  <span className={styles.drawerEntryAge}>{entry.age}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <span className={styles.drawerCollapsedLabel} aria-hidden="true">Activity</span>
      )}
    </div>
  );
}

// ── ConsolePage ───────────────────────────────────────────────────────────────

const ConsolePage = (): React.ReactElement => {
  const [activeSectionId, setActiveSectionId] = useState<string>('read');
  const [activeItemId, setActiveItemId]       = useState<string>('r-story');

  const activeSection = SECTIONS.find(s => s.id === activeSectionId) ?? SECTIONS[0];
  const activeItem    = activeSection.items.find(it => it.id === activeItemId) ?? activeSection.items[0];

  const selectSection = (id: string): void => {
    setActiveSectionId(id);
    const sec = SECTIONS.find(s => s.id === id);
    if (sec && sec.items.length > 0) {
      setActiveItemId(sec.items[0].id);
    }
  };

  const selectItem = (id: string): void => {
    setActiveItemId(id);
  };

  const jumpToModel = (): void => {
    setActiveSectionId('model');
    setActiveItemId('m-switch');
  };

  const jumpToView = (): void => {
    setActiveSectionId('characters');
    setActiveItemId('view');
  };

  return (
    <div className={styles.shell}>
      <TopBar onModelClick={jumpToModel} />

      <div className={styles.body}>
        <Sidebar
          activeSectionId={activeSectionId}
          onSelectSection={selectSection}
        />

        <ActionPane
          section={activeSection}
          activeItemId={activeItem.id}
          item={activeItem}
          onSelectItem={selectItem}
          onViewCharacter={jumpToView}
        />

        <ActivityDrawer />
      </div>
    </div>
  );
};

export const Head: HeadFC = () => (
  <title>Stately Ledger | DDCCS Campaign Console</title>
);

export default ConsolePage;
