/**
 * CharacterListScreen — `characters / list` and `npcs / n-list`.
 *
 * Data from ConsoleContext only — no mock fallbacks.
 * ctx.npcMode=true → filter characterType=false (NPCs).
 * Always filtered to the active campaign — no campaign switcher.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters, npcCharacters } from '../ConsoleContext';
import type { DrupalCharacter, DrupalCampaign } from '../ConsoleContext';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import { AddCharacterModal } from './AddCharacterModal';

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
  const campaign  = ctx.activeCampaignName ?? '';

  const [search,    setSearch]    = React.useState('');
  const [showModal, setShowModal] = React.useState(false);

  const activeCampaign = data.campaigns.find(c => c.name === campaign) ?? null;
  const partyIds       = (!isNpcMode && campaign) ? partyIdsForCampaign(data.campaigns, campaign) : null;

  /* Only source characters are counted and offered in the picker. Clones exist
     per-campaign and should not appear as selectable roster entries. */
  const sourceRoster = isNpcMode ? roster : roster.filter(c => c.sourceCharacter !== false);

  const filtered = roster.filter(c => {
    const matchSearch = !search
      || c.title.toLowerCase().includes(search.toLowerCase())
      || (c.nickname ?? '').toLowerCase().includes(search.toLowerCase());
    const matchCampaign = isNpcMode
      ? (!campaign || c.campaign === campaign || c.campaign === null)
      : (!partyIds || partyIds.has(c.id));
    return matchSearch && matchCampaign;
  });

  /* Source characters not yet in this campaign — shown in the picker modal. */
  const available = isNpcMode ? [] : sourceRoster.filter(c => !partyIds || !partyIds.has(c.id));

  const eyebrow      = isNpcMode ? 'NPCs' : 'Characters';
  const heading      = isNpcMode ? 'Major NPCs' : 'All Characters';
  const drupalAddUrl = drupalAdminUrl('/node/add/character');

  const addButton = !isNpcMode && activeCampaign ? (
    <button type="button" className="primary-btn" onClick={() => setShowModal(true)}>
      <Icon name="plus" size={11} /> Add character
    </button>
  ) : (
    <a href={drupalAddUrl} target="_blank" rel="noreferrer" className="primary-btn" style={{ textDecoration: 'none' }}>
      <Icon name="plus" size={11} /> Add character
    </a>
  );

  const modal = showModal && activeCampaign && (
    <AddCharacterModal
      campaignId={activeCampaign.id}
      campaignName={activeCampaign.name}
      available={available}
      onAdded={() => { setShowModal(false); window.location.reload(); }}
      onClose={() => setShowModal(false)}
    />
  );

  if (filtered.length === 0 && !search) {
    return (
      <div className="screen-characters-list">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">{eyebrow}</span>
            <h2>{heading}</h2>
            {campaign && <p className="screen-blurb">No characters in {campaign} yet.</p>}
          </div>
          <div className="screen-head-actions">{addButton}</div>
        </header>
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', padding: '24px 0' }}>
          No characters found for this campaign. Use Add character to populate the party.
        </p>
        {modal}
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
            {filtered.length} of {sourceRoster.length} {eyebrow.toLowerCase()}
            {campaign ? ` in ${campaign}` : ''}
          </p>
        </div>
        <div className="screen-head-actions">{addButton}</div>
      </header>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center' }}>
        <div className="search-field" style={{ flex: 1, minWidth: 200, maxWidth: 320 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder={`Search ${eyebrow.toLowerCase()}...`}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <span className="muted mono" style={{ fontSize: 11 }}>
          {filtered.length} of {sourceRoster.length}
        </span>
      </div>

      {filtered.length > 0 ? (
        <div className="char-grid">
          {filtered.map(char => <CharCard key={char.id} char={char} />)}
        </div>
      ) : (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          No characters match your search.
        </p>
      )}
      {modal}
    </div>
  );
}
