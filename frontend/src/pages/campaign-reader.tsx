import React, { useState, useEffect, useCallback, useRef } from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { cleanHtml } from '../utils/cleanHtml';
import * as styles from './campaign-reader.module.css';
import { useTopbar } from '../components/layout/TopbarContext';
import type { DrupalCampaign } from '../components/console/ConsoleContext';

// ── Roman numeral lookup (I–L) ────────────────────────────────────────────────

const ROMAN: readonly string[] = [
  'I',    'II',   'III',  'IV',   'V',
  'VI',   'VII',  'VIII', 'IX',   'X',
  'XI',   'XII',  'XIII', 'XIV',  'XV',
  'XVI',  'XVII', 'XVIII','XIX',  'XX',
  'XXI',  'XXII', 'XXIII','XXIV', 'XXV',
  'XXVI', 'XXVII','XXVIII','XXIX','XXX',
  'XXXI', 'XXXII','XXXIII','XXXIV','XXXV',
  'XXXVI','XXXVII','XXXVIII','XXXIX','XL',
  'XLI',  'XLII', 'XLIII','XLIV', 'XLV',
  'XLVI', 'XLVII','XLVIII','XLIX', 'L',
];

function toRoman(index: number): string {
  return ROMAN[index] ?? String(index + 1);
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface CharacterRef {
  title: string;
}

interface CampaignTerm {
  name:         string;
  currentParty: CharacterRef[] | null;
}

interface StoryNode {
  id:          string;
  title:       string;
  storyNumber: number | null;
  sessionDate: string | null;
  body:        { processed: string } | null;
  campaign:    CampaignTerm | null;
}

interface CampaignReaderData {
  drupal: {
    nodeStories: { nodes: StoryNode[] };
  };
}

// ── Date formatter ────────────────────────────────────────────────────────────

const MONTH_NAMES: readonly string[] = [
  'January', 'February', 'March',     'April',   'May',      'June',
  'July',    'August',   'September', 'October', 'November', 'December',
];

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const day  = d.getUTCDate();
  const mon  = MONTH_NAMES[d.getUTCMonth()] ?? '';
  const year = d.getUTCFullYear();
  return `${String(day)} ${mon} ${String(year)}`;
}

// ── Left page ─────────────────────────────────────────────────────────────────

interface StoryPageProps {
  story:    StoryNode;
  innerRef?: React.RefObject<HTMLDivElement | null>;
}

function LeftPage({ story, innerRef }: StoryPageProps): React.ReactElement {
  const characters = story.campaign?.currentParty ?? [];
  const dateStr    = story.sessionDate ? formatDate(story.sessionDate) : null;

  const metaParts: string[] = [];
  if (dateStr !== null) metaParts.push(dateStr);
  if (characters.length > 0) metaParts.push(characters.map(c => c.title).join(' · '));

  return (
    <div className={styles.pageInner} ref={innerRef}>
      <div className={styles.pageContent}>
        {story.storyNumber !== null && (
          <span className={styles.sessionChip}>
            Session {story.storyNumber}
          </span>
        )}

        <h2 className={styles.storyTitle}>{story.title}</h2>

        {metaParts.length > 0 && (
          <p className={styles.storyMeta}>{metaParts.join('  ·  ')}</p>
        )}

        <div className={styles.ornamentalDivider} aria-hidden="true" />

        {story.body !== null ? (
          <>
            <div
              className={styles.body}
              dangerouslySetInnerHTML={{ __html: cleanHtml(story.body.processed) }}
            />
            <p className={styles.endOrnament} aria-hidden="true">
              &#10087;&nbsp;&middot;&nbsp;&#10087;
            </p>
          </>
        ) : (
          <p className={styles.noBody}>No story content yet.</p>
        )}
      </div>
    </div>
  );
}

// ── Right page (next story or end-of-chronicle) ───────────────────────────────

interface RightPageProps {
  story:    StoryNode | null;
  innerRef?: React.RefObject<HTMLDivElement | null>;
}

function RightPage({ story, innerRef }: RightPageProps): React.ReactElement {
  if (story === null) {
    return (
      <div className={styles.endChronicle}>
        <span className={styles.endOrnamentLarge} aria-hidden="true">
          &#10087;
        </span>
        <p className={styles.endChronicleText}>End of Chronicle</p>
        <span className={styles.endOrnamentLarge} aria-hidden="true">
          &#10087;
        </span>
      </div>
    );
  }

  return <LeftPage story={story} innerRef={innerRef} />;
}

// ── Dot indicator ─────────────────────────────────────────────────────────────

interface DotIndicatorProps {
  total:   number;
  current: number;
}

function DotIndicator({ total, current }: DotIndicatorProps): React.ReactElement {
  const MAX_DOTS = 20;
  const visible  = Math.min(total, MAX_DOTS);

  return (
    <div className={styles.dots} aria-label={`Session ${String(current + 1)} of ${String(total)}`}>
      {Array.from({ length: visible }, (_, i) => (
        <span
          key={i}
          className={i === current ? `${styles.dot} ${styles.dotActive}` : styles.dot}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}

// ── CampaignReaderPage ────────────────────────────────────────────────────────

const ANIM_DURATION = 600;

const CampaignReaderPage: React.FC<PageProps<CampaignReaderData>> = ({
  data,
  location,
}) => {
  const allStories = data.drupal.nodeStories.nodes;
  const { activeCampaignName: contextCampaign, register } = useTopbar();

  // Register campaigns so the topbar chip works on this page.
  // Uses allStories (stable Gatsby prop) as the dep, not a derived array.
  useEffect(() => {
    const names = Array.from(
      new Set(allStories.map(s => s.campaign?.name).filter((n): n is string => n !== undefined && n !== null)),
    ).sort();
    const drupalCampaigns: DrupalCampaign[] = names.map(n => ({
      id:             n,
      name:           n,
      campaignStatus: null,
    }));
    register(drupalCampaigns, names[0] ?? null);
  }, [allStories, register]);

  // Priority: ?campaign= URL param > active campaign from console > first alphabetically.
  const [campaignName, setCampaignName] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const raw    = params.get('campaign');
    if (raw !== null && raw !== '') {
      setCampaignName(raw);
    } else if (contextCampaign !== null) {
      setCampaignName(contextCampaign);
    } else {
      const names = Array.from(
        new Set(
          allStories
            .map(s => s.campaign?.name ?? null)
            .filter((n): n is string => n !== null),
        ),
      ).sort();
      setCampaignName(names[0] ?? null);
    }
  }, [location.search, contextCampaign, allStories]);

  const stories = allStories
    .filter(s => s.campaign?.name === campaignName)
    .slice()
    .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0));

  // Spread model: each turn shows two consecutive stories (left + right page).
  // spread 0 → stories[0] + stories[1], spread 1 → stories[2] + stories[3], etc.
  const leftPageRef  = useRef<HTMLDivElement>(null);
  const rightPageRef = useRef<HTMLDivElement>(null);

  const spreadCount  = Math.ceil(stories.length / 2);

  // activeSpread  = spread currently fully displayed
  // sourceSpread  = spread we are leaving (kept during flip animation for the front face)
  const [activeSpread, setActiveSpread] = useState(0);
  const [sourceSpread, setSourceSpread] = useState<number | null>(null);
  const [animDir,      setAnimDir]      = useState<'forward' | 'back'>('forward');
  const [animating,    setAnimating]    = useState(false);

  // Reset to spread 0 when the active campaign changes.
  useEffect(() => {
    setActiveSpread(0);
  }, [campaignName]);

  // Scroll both pages to top whenever the spread changes.
  useEffect(() => {
    leftPageRef.current?.scrollTo({ top: 0 });
    rightPageRef.current?.scrollTo({ top: 0 });
  }, [activeSpread]);

  const navigate = useCallback((nextSpread: number, dir: 'forward' | 'back'): void => {
    if (animating) return;
    setAnimDir(dir);
    setSourceSpread(activeSpread);   // remember what we're leaving
    setActiveSpread(nextSpread);     // new content appears underneath immediately
    setAnimating(true);
    setTimeout(() => {
      setAnimating(false);
      setSourceSpread(null);
    }, ANIM_DURATION);
  }, [animating, activeSpread]);

  const goToPrev = (): void => {
    if (activeSpread > 0) navigate(activeSpread - 1, 'back');
  };

  const goToNext = (): void => {
    if (activeSpread < spreadCount - 1) navigate(activeSpread + 1, 'forward');
  };

  const hasPrev = activeSpread > 0;
  const hasNext = activeSpread < spreadCount - 1;

  // What the underlying spread shows (the destination).
  const leftStory  = stories[activeSpread * 2] ?? null;
  const rightStory = stories[activeSpread * 2 + 1] ?? null;

  // The page faces shown on the turning page during animation.
  // Forward flip: front = old right page, back = new left page.
  // Backward flip: front = old left page, back = new right page.
  const srcLeft  = sourceSpread !== null ? (stories[sourceSpread * 2] ?? null) : null;
  const srcRight = sourceSpread !== null ? (stories[sourceSpread * 2 + 1] ?? null) : null;
  const flipFrontStory = animDir === 'forward' ? srcRight : srcLeft;
  const flipBackStory  = animDir === 'forward' ? leftStory : rightStory;

  const prevLeftTitle = stories[(activeSpread - 1) * 2]?.title ?? '';
  const nextLeftTitle = stories[(activeSpread + 1) * 2]?.title ?? '';
  const currentStory  = leftStory;

  if (stories.length === 0 && campaignName !== null) {
    return (
      <div className={styles.shell}>
        <div className={styles.topBar}>
          <Link to="/stories/" className={styles.backLink}>&larr; Back to Chronicles</Link>
          <span className={styles.topCenter}>{campaignName ?? ''}</span>
          <span className={styles.topRight} />
        </div>
        <div className={styles.emptyBook}>
          <p className={styles.emptyText}>No stories recorded for this campaign.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.shell}>

      {/* Top bar */}
      <div className={styles.topBar}>
        <Link to="/stories/" className={styles.backLink}>
          &larr; Back to Chronicles
        </Link>
        <span className={styles.topCenter}>
          <span className={styles.topCampaign}>{campaignName ?? ''}</span>
          {currentStory !== null && (
            <>
              <span className={styles.topSep}>&thinsp;&mdash;&thinsp;</span>
              <span className={styles.topStoryTitle}>{currentStory.title}</span>
            </>
          )}
        </span>
        <span className={styles.topRight}>
          Spread {String(activeSpread + 1)} of {String(spreadCount)}
        </span>
      </div>

      {/* Book area */}
      <div className={styles.bookArea}>
        <div className={styles.bookContainer}>
          <div className={styles.book}>

            {/* Destination spread — always visible underneath */}
            <div className={`${styles.page} ${styles.pageLeft}`}>
              {leftStory !== null && <LeftPage story={leftStory} innerRef={leftPageRef} />}
            </div>
            <div className={styles.spine} aria-hidden="true" />
            <div className={`${styles.page} ${styles.pageRight}`}>
              <RightPage story={rightStory} innerRef={rightPageRef} />
            </div>

            {/* 3D page-turn overlay — only during animation */}
            {animating && (
              <div
                className={`${styles.pageFlipper} ${
                  animDir === 'forward'
                    ? styles.pageFlipperForward
                    : styles.pageFlipperBack
                }`}
                aria-hidden="true"
              >
                {/* Front face: the page we are leaving */}
                <div className={`${styles.flipFace} ${styles.flipFaceFront}`}>
                  {flipFrontStory !== null && (
                    <LeftPage story={flipFrontStory} />
                  )}
                </div>
                {/* Back face: the page that appears as the flip completes */}
                <div className={`${styles.flipFace} ${styles.flipFaceBack}`}>
                  {flipBackStory !== null && (
                    <LeftPage story={flipBackStory} />
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* Bottom navigation */}
      <div className={styles.navBar}>
        <button
          type="button"
          className={styles.navButton}
          onClick={goToPrev}
          disabled={!hasPrev}
          aria-label="Previous spread"
        >
          &larr; Previous{hasPrev ? ` — ${prevLeftTitle}` : ''}
        </button>

        <DotIndicator total={spreadCount} current={activeSpread} />

        <button
          type="button"
          className={`${styles.navButton} ${styles.navButtonRight}`}
          onClick={goToNext}
          disabled={!hasNext}
          aria-label="Next spread"
        >
          {hasNext ? `${nextLeftTitle} · ` : ''}Next &rarr;
        </button>
      </div>

    </div>
  );
};

// ── GraphQL query ─────────────────────────────────────────────────────────────

export const query = graphql`
  query CampaignReader {
    drupal {
      nodeStories(first: 100) {
        nodes {
          id
          title
          storyNumber
          sessionDate
          body { processed }
          campaign {
            ... on Drupal_TermCampaign {
              name
              currentParty {
                ... on Drupal_NodeCharacter { title }
              }
            }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC<CampaignReaderData> = () => (
  <title>Campaign Reader | D&D Consultant</title>
);

export default CampaignReaderPage;
