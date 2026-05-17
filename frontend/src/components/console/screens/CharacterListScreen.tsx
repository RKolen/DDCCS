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
import type { DrupalCharacter } from '../ConsoleContext';

function CharCard({
  char, onClick,
}: { char: DrupalCharacter; onClick: () => void }): React.ReactElement {
  const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  return (
    <button className="char-card" onClick={onClick}>
      <div className="char-portrait">
        {char.imageUrl
          ? <img src={char.imageUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : <span className="portrait-placeholder">{initials}</span>
        }
      </div>
      <div className="char-card-body">
        <h4>{char.title}</h4>
        {char.nickname && <span className="char-card-meta" style={{ fontStyle: 'italic' }}>{char.nickname}</span>}
        {char.characterClass && <span className="char-card-meta">{char.characterClass}</span>}
        {char.pronouns && <span className="char-card-pron">{char.pronouns}</span>}
        {char.campaign && <span className="char-card-pron">{char.campaign}</span>}
      </div>
      <div className="char-card-stats">
        {char.level !== null      && <span>Lv {char.level}</span>}
        {char.armorClass !== null && <span>AC {char.armorClass}</span>}
        {char.maximumHitpoints !== null && <span>HP {char.maximumHitpoints}</span>}
      </div>
    </button>
  );
}

export function CharacterListScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data      = useConsoleData();
  const isNpcMode = Boolean(ctx.npcMode);
  const roster    = isNpcMode ? npcCharacters(data) : playerCharacters(data);

  const [search,   setSearch]   = React.useState('');
  const [campaign, setCampaign] = React.useState(ctx.activeCampaignName ?? '');

  const campaigns = Array.from(new Set(roster.map(c => c.campaign).filter(Boolean))) as string[];

  const filtered = roster.filter(c => {
    const matchSearch   = !search   || c.title.toLowerCase().includes(search.toLowerCase()) || (c.nickname ?? '').toLowerCase().includes(search.toLowerCase());
    const matchCampaign = !campaign || c.campaign === campaign;
    return matchSearch && matchCampaign;
  });

  const eyebrow = isNpcMode ? 'NPCs' : 'Characters';
  const heading = isNpcMode ? 'Major NPCs' : 'All Characters';
  const drupalAddUrl = isNpcMode
    ? 'https://drupal-cms.ddev.site/node/add/character'
    : 'https://drupal-cms.ddev.site/node/add/character';

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
        {campaigns.length > 1 && (
          <select value={campaign} onChange={e => setCampaign(e.target.value)}>
            <option value="">All campaigns</option>
            {campaigns.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
        <span className="muted mono" style={{ fontSize: 11 }}>
          {filtered.length} of {roster.length}
        </span>
      </div>

      {/* Card grid */}
      {filtered.length > 0 ? (
        <div className="char-grid">
          {filtered.map(char => {
            const idx = roster.indexOf(char);
            return (
              <CharCard
                key={char.id}
                char={char}
                onClick={() => setCtx({
                  ...ctx,
                  charIdx: idx,
                  _jumpTo: {
                    sectionId: isNpcMode ? 'npcs' : 'characters',
                    itemId: isNpcMode ? 'n-view' : 'view',
                    charIdx: idx,
                  },
                })}
              />
            );
          })}
        </div>
      ) : (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          No results match your filters.
        </p>
      )}
    </div>
  );
}
