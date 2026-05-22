import React, { useState, useMemo } from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Divider } from '../components/atoms/Divider';
import { Portrait } from '../components/atoms/Portrait';
import * as styles from './characters.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CurrentPartyMember {
  id: string;
}

interface CampaignRef {
  id:           string;
  name:         string;
  currentParty: CurrentPartyMember[] | null;
}

interface StoryNode {
  campaign: CampaignRef | null;
}

interface CharacterNode {
  id:              string;
  title:           string;
  firstName:       string | null;
  nickname:        string | null;
  pronouns:        string | null;
  characterType:   boolean | null;
  sourceCharacter: boolean | null;
  level:           number | null;
  armorClass:      number | null;
  maximumHitpoints: number | null;
  path:            string | null;
  campaign:        { name: string } | null;
  image:           { mediaImage: { url: string; alt: string } | null } | null;
}

interface CharactersData {
  drupal: {
    nodeCharacters: { nodes: CharacterNode[] };
    nodeStories:    { nodes: StoryNode[] };
  } | null;
}

// ── Party ID set ──────────────────────────────────────────────────────────────

function buildPartyIds(stories: StoryNode[]): Set<string> {
  const ids = new Set<string>();
  const seen = new Set<string>();
  for (const s of stories) {
    if (!s.campaign) continue;
    if (seen.has(s.campaign.id)) continue;
    seen.add(s.campaign.id);
    for (const m of s.campaign.currentParty ?? []) {
      ids.add(m.id);
    }
  }
  return ids;
}

// ── Character card ────────────────────────────────────────────────────────────

interface CharacterCardProps {
  char:     CharacterNode;
  inParty:  boolean;
}

function CharacterCard({ char, inParty }: CharacterCardProps): React.ReactElement {
  const href    = char.path ?? '#';
  const initial = char.title.charAt(0).toUpperCase();

  return (
    <Link to={href} className={`${styles.card}${inParty ? ` ${styles.cardParty}` : ''}`}>
      {/* Portrait */}
      <div className={styles.portraitWrap}>
        <Portrait
          name={char.title}
          size={56}
          imageUrl={char.image?.mediaImage?.url ?? null}
          species={null}
        />
        {inParty && <span className={styles.partyDot} title="In current party" />}
      </div>

      {/* Body */}
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

        {char.campaign && (
          <p className={styles.cardCampaign}>{char.campaign.name}</p>
        )}

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

// ── Filter bar ────────────────────────────────────────────────────────────────

interface FilterBarProps {
  search:       string;
  onSearch:     (v: string) => void;
  partyOnly:    boolean;
  onPartyOnly:  (v: boolean) => void;
  canonOnly:    boolean;
  onCanonOnly:  (v: boolean) => void;
  count:        number;
  total:        number;
}

function FilterBar({
  search, onSearch,
  partyOnly, onPartyOnly,
  canonOnly, onCanonOnly,
  count, total,
}: FilterBarProps): React.ReactElement {
  return (
    <div className={styles.filterBar}>
      <input
        className={styles.filterSearch}
        type="search"
        placeholder="Search by name or nickname..."
        value={search}
        onChange={e => onSearch(e.target.value)}
        aria-label="Search characters"
      />

      <label className={styles.filterToggle}>
        <input
          type="checkbox"
          checked={partyOnly}
          onChange={e => onPartyOnly(e.target.checked)}
        />
        <span>Current party only</span>
      </label>

      <label className={styles.filterToggle}>
        <input
          type="checkbox"
          checked={canonOnly}
          onChange={e => onCanonOnly(e.target.checked)}
        />
        <span>Canon characters</span>
      </label>

      <span className={styles.filterCount}>
        {count === total ? `${total} characters` : `${count} of ${total}`}
      </span>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const CharactersPage: React.FC<PageProps<CharactersData>> = ({ data, location }) => {
  const [search,    setSearch]    = useState('');
  const [partyOnly, setPartyOnly] = useState(false);
  const [canonOnly, setCanonOnly] = useState(false);

  const allPcs = useMemo(
    () => (data.drupal?.nodeCharacters.nodes ?? []).filter(c => c.characterType !== false),
    [data],
  );

  const partyIds = useMemo(
    () => buildPartyIds(data.drupal?.nodeStories.nodes ?? []),
    [data],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allPcs.filter(c => {
      if (partyOnly && !partyIds.has(c.id)) return false;
      if (canonOnly && !c.sourceCharacter)  return false;
      if (q) {
        return (
          c.title.toLowerCase().includes(q) ||
          (c.nickname ?? '').toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [allPcs, partyIds, search, partyOnly, canonOnly]);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Characters</h1>
          <p className={styles.subtitle}>All adventurers across every campaign.</p>
        </header>

        <Divider icon="crossed-swords" />

        <div className={styles.dividerSpacer} />

        <FilterBar
          search={search}    onSearch={setSearch}
          partyOnly={partyOnly} onPartyOnly={setPartyOnly}
          canonOnly={canonOnly} onCanonOnly={setCanonOnly}
          count={filtered.length} total={allPcs.length}
        />

        {filtered.length > 0 ? (
          <div className={styles.grid}>
            {filtered.map(char => (
              <CharacterCard
                key={char.id}
                char={char}
                inParty={partyIds.has(char.id)}
              />
            ))}
          </div>
        ) : (
          <div className={styles.emptyPanel}>
            <p className={styles.emptyBody}>
              {allPcs.length === 0
                ? 'No characters in Drupal yet.'
                : 'No characters match the current filters.'}
            </p>
          </div>
        )}
      </div>
    </BaseTemplate>
  );
};

// ── GraphQL query ─────────────────────────────────────────────────────────────

export const query = graphql`
  query CharactersList {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id
          title
          firstName
          nickname
          pronouns
          characterType
          sourceCharacter
          level
          armorClass
          maximumHitpoints
          path
          campaign {
            ... on Drupal_TermCampaign { name }
          }
          image {
            ... on Drupal_MediaImage {
              mediaImage { url alt }
            }
          }
        }
      }
      nodeStories(first: 100) {
        nodes {
          campaign {
            ... on Drupal_TermCampaign {
              id
              name
              currentParty {
                ... on Drupal_NodeCharacter { id }
              }
            }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Characters | D&amp;D Consultant</title>;

export default CharactersPage;
