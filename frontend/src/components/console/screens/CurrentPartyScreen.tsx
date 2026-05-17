/**
 * CurrentPartyScreen — `/party/` and console embedded view.
 *
 * Party = characters listed in field_current_party on the Campaign taxonomy
 * term (accessed via the story's campaign reference). Falls back to filtering
 * all player characters by campaign name if currentPartyIds is unavailable.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters, storiesForCampaign } from '../ConsoleContext';
import { Icon } from '../atoms';

export function CurrentPartyScreen({ ctx }: ScreenProps): React.ReactElement {
  const data         = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined) ?? data.campaigns[0]?.name ?? null;
  const campaign     = data.campaigns.find(c => c.name === campaignName) ?? data.campaigns[0] ?? null;

  const allPcs = playerCharacters(data);

  /* Use field_current_party IDs from the campaign term if present */
  const party = (() => {
    if (campaign?.currentPartyIds && campaign.currentPartyIds.length > 0) {
      const idSet = new Set(campaign.currentPartyIds);
      const fromParty = allPcs.filter(c => idSet.has(c.id));
      if (fromParty.length > 0) return fromParty;
    }
    /* Fall back: filter by campaign name */
    return campaignName ? allPcs.filter(c => c.campaign === campaignName) : allPcs;
  })();

  const campaignStories = campaign ? storiesForCampaign(data, campaign.name) : data.stories;

  return (
    <div className="screen-current-party">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Current party</span>
          <h2>{campaign?.name ?? 'No campaign selected'}</h2>
          <p className="screen-blurb">
            {party.length} {party.length === 1 ? 'member' : 'members'}
            {campaign?.campaignStatus ? ` · ${campaign.campaignStatus}` : ''}
            {campaignStories.length > 0 ? ` · ${campaignStories.length} sessions` : ''}
          </p>
        </div>
        <div className="screen-head-actions">
          <Link to="/stories/" className="ghost-btn" style={{ textDecoration: 'none' }}>
            <Icon name="book" size={11} /> Story log
          </Link>
          <a
            href="https://drupal-cms.ddev.site/node/add/story"
            target="_blank"
            rel="noreferrer"
            className="primary-btn"
            style={{ textDecoration: 'none' }}
          >
            <Icon name="plus" size={11} /> New session
          </a>
        </div>
      </header>

      {party.length === 0 ? (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', padding: '24px 0' }}>
          {allPcs.length === 0
            ? 'No player characters in Drupal.'
            : `No characters in field_current_party for "${campaign?.name ?? 'this campaign'}". Set the party in Drupal.`}
        </p>
      ) : (
        <div className="char-grid">
          {party.map(char => {
            const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
            return (
              <div key={char.id} className="char-card">
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
                </div>
                <div className="char-card-stats">
                  {char.maximumHitpoints !== null && <span>HP {char.maximumHitpoints}</span>}
                  {char.armorClass !== null        && <span>AC {char.armorClass}</span>}
                </div>
                {char.path && (
                  <div style={{ padding: '6px 12px 10px', borderTop: '1px solid var(--rule)' }}>
                    <Link to={char.path} style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: 'var(--brass)', letterSpacing: '.08em', textDecoration: 'none' }}>
                      Full sheet
                    </Link>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
