/**
 * CharacterListScreen — `characters / list` and `npcs / n-list`.
 *
 * Data from ConsoleContext only — no mock fallbacks.
 * ctx.npcMode=true → filter characterType=false (NPCs).
 * Filtered to active campaign by default, with a campaign switcher.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters, npcCharacters } from '../ConsoleContext';
import type { DrupalCharacter, DrupalCampaign } from '../ConsoleContext';
import { drupalAdminUrl } from '../../../utils/drupalLinks';

function CharCard({ char }: { char: DrupalCharacter }): React.ReactElement {
  const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  const href = char.path ?? '#';

  const classLabel = char.characterType !== false
    ? [char.characterClass, char.level !== null ? `Lv ${char.level}` : null].filter(Boolean).join(' · ')
    : char.role ?? null;

  return (
    <Link to={href} className="char-card" style={{ textDecoration: 'none' }}>
      <div className="char-portrait">
        {char.imageUrl
          ? <img src={char.imageUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
          : <span className="portrait-placeholder">{initials}</span>
        }
      </div>
      <div className="char-card-body">
        <h4>{char.title}</h4>
        {char.nickname && <span className="char-card-meta" style={{ fontStyle: 'italic' }}>{char.nickname}</span>}
        {classLabel && <span className="char-card-meta">{classLabel}</span>}
        {char.pronouns && <span className="char-card-pron">{char.pronouns}</span>}
      </div>
      <div className="char-card-stats">
        {char.armorClass !== null && <span>AC {char.armorClass}</span>}
        {char.maximumHitpoints !== null && <span>HP {char.maximumHitpoints}</span>}
      </div>
    </Link>
  );
}

function partyIdsForCampaign(campaigns: DrupalCampaign[], name: string): Set<string> {
  const camp = campaigns.find(c => c.name === name);
  return new Set(camp?.currentPartyIds ?? []);
}

export function CharacterListScreen({ ctx }: ScreenProps): React.ReactElement {
  const data      = useConsoleData();
  const isNpcMode = Boolean(ctx.npcMode);
  const roster    = isNpcMode ? npcCharacters(data) : playerCharacters(data);

  const [search,   setSearch]   = React.useState('');
  const [campaign, setCampaign] = React.useState(ctx.activeCampaignName ?? '');

  /* Sync local campaign filter when the global active campaign changes */
  React.useEffect(() => {
    setCampaign(ctx.activeCampaignName ?? '');
  }, [ctx.activeCampaignName]);

  // PCs: filter by campaign's currentPartyIds (characters are linked via the campaign term).
  // NPCs: filter by their own campaign field if set, otherwise show all.
  const partyIds = (!isNpcMode && campaign) ? partyIdsForCampaign(data.campaigns, campaign) : null;

  const filtered = roster.filter(c => {
    const matchSearch = !search
      || c.title.toLowerCase().includes(search.toLowerCase())
      || (c.nickname ?? '').toLowerCase().includes(search.toLowerCase());
    const matchCampaign = isNpcMode
      ? (!campaign || c.campaign === campaign || c.campaign === null)
      : (!partyIds || partyIds.size === 0 || partyIds.has(c.id));
    return matchSearch && matchCampaign;
  });

  const eyebrow = isNpcMode ? 'NPCs' : 'Characters';
  const heading = isNpcMode ? 'Major NPCs' : 'All Characters';
  const drupalAddUrl = drupalAdminUrl('/node/add/character');

  if (roster.length === 0) {
    return (
      <div className="screen-characters-list">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">{eyebrow}</span>
            <h2>{heading}</h2>
          </div>
          <div className="screen-head-actions">
            <a href={drupalAddUrl} target="_blank" rel="noreferrer" className="primary-btn" style={{ textDecoration: 'none' }}>
              <Icon name="plus" size={11} /> Add in Drupal
            </a>
          </div>
        </header>
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', padding: '24px 0' }}>
          {isNpcMode
            ? 'No NPCs in Drupal yet. Create a Character node with Character Type set to off.'
            : 'No player characters in Drupal yet. Create a Character node with Character Type set to on.'}
        </p>
      </div>
    );
  }

  return (
    <div className="screen-characters-list">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">{eyebrow}</span>
          <h2>{heading}</h2>
          <p className="screen-blurb">
            {filtered.length} of {roster.length} {eyebrow.toLowerCase()}
            {campaign ? ` in ${campaign}` : ''}
          </p>
        </div>
        <div className="screen-head-actions">
          {!isNpcMode && (
            <Link to="/characters/" className="ghost-btn" style={{ textDecoration: 'none' }}>
              <Icon name="list" size={11} /> Full roster
            </Link>
          )}
          <a href={drupalAddUrl} target="_blank" rel="noreferrer" className="primary-btn" style={{ textDecoration: 'none' }}>
            <Icon name="plus" size={11} /> Add in Drupal
          </a>
        </div>
      </header>

      {/* Filter row */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="search-field" style={{ flex: 1, minWidth: 200, maxWidth: 320 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder={`Search ${eyebrow.toLowerCase()}...`}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        {data.campaigns.length > 1 && (
          <select value={campaign} onChange={e => setCampaign(e.target.value)}>
            <option value="">All campaigns</option>
            {data.campaigns.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
        )}
        <span className="muted mono" style={{ fontSize: 11 }}>
          {filtered.length} of {roster.length}
        </span>
      </div>

      {/* Card grid */}
      {filtered.length > 0 ? (
        <div className="char-grid">
          {filtered.map(char => (
            <CharCard key={char.id} char={char} />
          ))}
        </div>
      ) : (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          No results match your filters.
        </p>
      )}
    </div>
  );
}
