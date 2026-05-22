/**
 * CharacterRoster — shared roster component used by both /characters/ and /npcs/.
 *
 * Pass isNpc=false for player characters, isNpc=true for NPCs.
 * The only behavioural differences:
 *   - isNpc=false: shows party dot + "current party only" filter (uses story currentParty)
 *   - isNpc=true:  shows role line instead of campaign, no party filter
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'gatsby';
import { Divider } from '../atoms/Divider';
import { Portrait } from '../atoms/Portrait';
import * as styles from '../../pages/characters.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RosterCharacter {
  id:               string;
  title:            string;
  firstName:        string | null;
  nickname:         string | null;
  pronouns:         string | null;
  characterType:    boolean | null;
  sourceCharacter:  boolean | null;
  role:             string | null;
  level:            number | null;
  armorClass:       number | null;
  maximumHitpoints: number | null;
  path:             string | null;
  campaign:         { name: string } | null;
  image:            { mediaImage: { url: string; alt: string } | null } | null;
}

interface StoryNode {
  campaign: {
    id:           string;
    name:         string;
    currentParty: { id: string }[] | null;
  } | null;
}

export interface RosterData {
  drupal: {
    nodeCharacters: { nodes: RosterCharacter[] };
    nodeStories:    { nodes: StoryNode[] };
  } | null;
}

// ── Party IDs ─────────────────────────────────────────────────────────────────

function buildPartyIds(stories: StoryNode[]): Set<string> {
  const ids  = new Set<string>();
  const seen = new Set<string>();
  for (const s of stories) {
    if (!s.campaign) continue;
    if (seen.has(s.campaign.id)) continue;
    seen.add(s.campaign.id);
    for (const m of s.campaign.currentParty ?? []) ids.add(m.id);
  }
  return ids;
}

// ── Character card ─────────────────────────────────────────────────────────────

function CharacterCard({
  char,
  inParty,
  isNpc,
}: {
  char:    RosterCharacter;
  inParty: boolean;
  isNpc:   boolean;
}): React.ReactElement {
  const href = char.path ?? '#';

  return (
    <Link
      to={href}
      className={`${styles.card}${inParty ? ` ${styles.cardParty}` : ''}`}
      style={{ textDecoration: 'none' }}
    >
      <div className={styles.portraitWrap}>
        <Portrait
          name={char.title}
          size={56}
          imageUrl={char.image?.mediaImage?.url ?? null}
        />
        {inParty && <span className={styles.partyDot} title="In current party" />}
      </div>

      <div className={styles.cardBody}>
        <div className={styles.cardTop}>
          <span className={styles.cardName}>{char.title}</span>
          {char.sourceCharacter && (
            <span className={styles.canonBadge}>Canon</span>
          )}
        </div>

        {char.nickname && (
          <p className={styles.cardNickname}>&ldquo;{char.nickname}&rdquo;</p>
        )}

        {char.pronouns && (
          <p className={styles.cardPronouns}>{char.pronouns}</p>
        )}

        {/* NPCs show their role; PCs show their campaign */}
        {isNpc && char.role ? (
          <p className={styles.cardCampaign}>{char.role}</p>
        ) : !isNpc && char.campaign ? (
          <p className={styles.cardCampaign}>{char.campaign.name}</p>
        ) : null}

        <div className={styles.cardStats}>
          {char.level !== null && (
            <span className={styles.statChip}>Lv {char.level}</span>
          )}
          {char.maximumHitpoints !== null && (
            <span className={styles.statChip}>HP {char.maximumHitpoints}</span>
          )}
          {char.armorClass !== null && (
            <span className={styles.statChip}>AC {char.armorClass}</span>
          )}
        </div>
      </div>
    </Link>
  );
}

// ── Filter bar ─────────────────────────────────────────────────────────────────

function FilterBar({
  search,    onSearch,
  partyOnly, onPartyOnly,
  canonOnly, onCanonOnly,
  count,     total,
  isNpc,
}: {
  search:      string;
  onSearch:    (v: string) => void;
  partyOnly:   boolean;
  onPartyOnly: (v: boolean) => void;
  canonOnly:   boolean;
  onCanonOnly: (v: boolean) => void;
  count:       number;
  total:       number;
  isNpc:       boolean;
}): React.ReactElement {
  const noun = isNpc ? 'NPCs' : 'characters';
  return (
    <div className={styles.filterBar}>
      <input
        className={styles.filterSearch}
        type="search"
        placeholder={`Search by name or nickname...`}
        value={search}
        onChange={e => onSearch(e.target.value)}
        aria-label={`Search ${noun}`}
      />

      {/* Party filter only applies to PCs */}
      {!isNpc && (
        <label className={styles.filterToggle}>
          <input
            type="checkbox"
            checked={partyOnly}
            onChange={e => onPartyOnly(e.target.checked)}
          />
          <span>Current party only</span>
        </label>
      )}

      <label className={styles.filterToggle}>
        <input
          type="checkbox"
          checked={canonOnly}
          onChange={e => onCanonOnly(e.target.checked)}
        />
        <span>Canon characters</span>
      </label>

      <span className={styles.filterCount}>
        {count === total
          ? `${total} ${noun}`
          : `${count} of ${total}`}
      </span>
    </div>
  );
}

// ── Roster ────────────────────────────────────────────────────────────────────

interface CharacterRosterProps {
  data:    RosterData | null | undefined;
  isNpc:   boolean;
  pathname?: string;
}

export function CharacterRoster({ data, isNpc }: CharacterRosterProps): React.ReactElement {
  const [search,    setSearch]    = useState('');
  const [partyOnly, setPartyOnly] = useState(false);
  const [canonOnly, setCanonOnly] = useState(false);

  const allChars = useMemo(
    () => (data?.drupal?.nodeCharacters.nodes ?? []).filter(c =>
      isNpc ? c.characterType === false : c.characterType !== false,
    ),
    [data, isNpc],
  );

  const partyIds = useMemo(
    () => buildPartyIds(data?.drupal?.nodeStories.nodes ?? []),
    [data],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allChars.filter(c => {
      if (!isNpc && partyOnly && !partyIds.has(c.id)) return false;
      if (canonOnly && !c.sourceCharacter) return false;
      if (q) {
        return (
          c.title.toLowerCase().includes(q) ||
          (c.nickname ?? '').toLowerCase().includes(q) ||
          (c.role    ?? '').toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [allChars, partyIds, search, partyOnly, canonOnly, isNpc]);

  const heading  = isNpc ? 'NPCs' : 'Characters';
  const subtitle = isNpc
    ? 'Recurring non-player characters across every campaign.'
    : 'All adventurers across every campaign.';
  const icon = isNpc ? 'scroll-unfurled' : 'crossed-swords';

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <h1 className={styles.heading}>{heading}</h1>
        <p className={styles.subtitle}>{subtitle}</p>
      </header>

      <Divider icon={icon as 'crossed-swords' | 'scroll-unfurled'} />

      <div className={styles.dividerSpacer} />

      <FilterBar
        search={search}       onSearch={setSearch}
        partyOnly={partyOnly} onPartyOnly={setPartyOnly}
        canonOnly={canonOnly} onCanonOnly={setCanonOnly}
        count={filtered.length} total={allChars.length}
        isNpc={isNpc}
      />

      {filtered.length > 0 ? (
        <div className={styles.grid}>
          {filtered.map(char => (
            <CharacterCard
              key={char.id}
              char={char}
              inParty={!isNpc && partyIds.has(char.id)}
              isNpc={isNpc}
            />
          ))}
        </div>
      ) : (
        <div className={styles.emptyPanel}>
          <p className={styles.emptyBody}>
            {allChars.length === 0
              ? isNpc
                ? 'No NPCs in Drupal yet. Create a Character node with Character Type set to off.'
                : 'No player characters in Drupal yet.'
              : 'No results match the current filters.'}
          </p>
        </div>
      )}
    </div>
  );
}
