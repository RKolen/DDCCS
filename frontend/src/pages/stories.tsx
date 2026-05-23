import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { GameIcon } from '../components/atoms/GameIcon';
import { useTopbar } from '../components/layout/TopbarContext';
import type { DrupalCampaign } from '../components/console/ConsoleContext';
import * as styles from './stories.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignTerm {
  name: string;
}

interface StoryNode {
  id:          string;
  title:       string;
  storyNumber: number | null;
  campaign:    CampaignTerm | null;
}

interface StoriesData {
  drupal: {
    nodeStories: { nodes: StoryNode[] };
  };
}

// ── Campaign grouping helpers ──────────────────────────────────────────────────

interface CampaignGroup {
  name:    string;
  stories: StoryNode[];
}

function groupByCampaign(nodes: StoryNode[]): CampaignGroup[] {
  const map = new Map<string, StoryNode[]>();

  for (const node of nodes) {
    const key = node.campaign?.name ?? 'Unknown Campaign';
    const existing = map.get(key);
    if (existing) {
      existing.push(node);
    } else {
      map.set(key, [node]);
    }
  }

  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, stories]) => ({
      name,
      stories: stories
        .slice()
        .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0)),
    }));
}

function sessionRange(stories: StoryNode[]): string | null {
  if (stories.length === 0) return null;
  const first = stories[0];
  const last  = stories[stories.length - 1];
  if (first === last) return first.title;
  return `Session 1 – Session ${String(stories.length)}`;
}

// ── Campaign card ─────────────────────────────────────────────────────────────

interface CampaignCardProps {
  group: CampaignGroup;
}

function CampaignCard({ group }: CampaignCardProps): React.ReactElement {
  const count = group.stories.length;
  const range = sessionRange(group.stories);
  const href  = `/campaign-reader/?campaign=${encodeURIComponent(group.name)}`;

  return (
    <Link to={href} className={styles.card}>
      <div className={styles.cardIcon}>
        <GameIcon
          name="scroll-unfurled"
          size={28}
          colorFilter="var(--filter-gold-dim)"
          decorative
        />
      </div>

      <h2 className={styles.cardName}>{group.name}</h2>

      <p className={styles.cardCount}>
        {count} {count === 1 ? 'session' : 'sessions'} recorded
      </p>

      {range !== null && (
        <p className={styles.cardRange}>{range}</p>
      )}

      <span className={styles.cardCta}>Read Chronicle &rarr;</span>
    </Link>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState(): React.ReactElement {
  return (
    <p className={styles.empty}>No stories recorded yet.</p>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const StoriesPage: React.FC<PageProps<StoriesData>> = ({ data, location }) => {
  const storyNodes = data.drupal.nodeStories.nodes;
  const allGroups  = groupByCampaign(storyNodes);
  const { activeCampaignName, register } = useTopbar();

  React.useEffect(() => {
    const names = Array.from(
      new Set(storyNodes.map(n => n.campaign?.name).filter((n): n is string => n !== undefined && n !== null)),
    );
    const drupalCampaigns: DrupalCampaign[] = names.map(n => ({
      id: n,
      name: n,
      campaignStatus: null,
    }));
    register(drupalCampaigns, names[0] ?? null);
  }, [storyNodes, register]);

  const activeGroup = activeCampaignName !== null
    ? (allGroups.find(g => g.name === activeCampaignName) ?? null)
    : null;

  const showAll = activeCampaignName === null;
  const groups  = showAll ? allGroups : (activeGroup !== null ? [activeGroup] : []);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Chronicle</h1>
          <p className={styles.subtitle}>
            {activeCampaignName !== null
              ? activeCampaignName
              : 'Select a campaign to begin reading.'}
          </p>
        </header>

        {groups.length > 0 ? (
          <div className={styles.grid}>
            {groups.map(group => (
              <CampaignCard key={group.name} group={group} />
            ))}
          </div>
        ) : activeCampaignName !== null ? (
          <div className={styles.grid}>
            <div className={styles.card} style={{ cursor: 'default', opacity: 0.7 }}>
              <div className={styles.cardIcon}>
                <GameIcon name="scroll-unfurled" size={28} colorFilter="var(--filter-gold-dim)" decorative />
              </div>
              <h2 className={styles.cardName}>{activeCampaignName}</h2>
              <p className={styles.cardCount}>0 sessions recorded</p>
              <p className={styles.cardRange}>
                No stories yet — sync from the Python CLI or add one from the console.
              </p>
            </div>
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </BaseTemplate>
  );
};

// ── GraphQL query ─────────────────────────────────────────────────────────────

export const query = graphql`
  query StoriesCampaignIndex {
    drupal {
      nodeStories(first: 100) {
        nodes {
          id
          title
          storyNumber
          campaign {
            ... on Drupal_TermCampaign { name }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Chronicle | D&D Consultant</title>;

export default StoriesPage;
