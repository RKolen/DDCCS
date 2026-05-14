import React, { useState } from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import * as styles from './campaign-reader.module.css';

// ── Roman numeral lookup (I–XII) ─────────────────────────────────────────────

const ROMAN_NUMERALS: readonly string[] = [
  'I', 'II', 'III', 'IV', 'V', 'VI',
  'VII', 'VIII', 'IX', 'X', 'XI', 'XII',
];

function toRoman(index: number): string {
  return ROMAN_NUMERALS[index] ?? String(index + 1);
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface StoryNode {
  id:               string;
  title:            string;
  fieldStoryNumber: number | null;
  fieldSessionDate: string | null;
  fieldBody:        { processed: string } | null;
  fieldCharacters:  Array<{ title: string }> | null;
  path:             { alias: string } | null;
}

interface CampaignReaderData {
  allNodeStory: { nodes: StoryNode[] };
}

type ImageState = 'idle' | 'running' | 'done';

// ── StoryMedallions ───────────────────────────────────────────────────────────

interface StoryMedallionsProps {
  title: string;
}

function StoryMedallions({ title }: StoryMedallionsProps): React.ReactElement {
  const [narrating, setNarrating] = useState(false);
  const [imgState, setImgState] = useState<ImageState>('idle');

  const toggleNarrate = (): void => setNarrating(n => !n);

  const generateImage = (): void => {
    if (imgState === 'running') return;
    setImgState('running');
    setTimeout(() => setImgState('done'), 1800);
  };

  const narrateLabel = narrating ? 'Listening...' : 'Narrate';
  const imgLabel =
    imgState === 'idle'    ? 'Generate image' :
    imgState === 'running' ? 'Conjuring...'   :
    'View image';

  return (
    <div className={styles.medallions} role="group" aria-label={`Actions for ${title}`}>
      <button
        className={`${styles.medallion}${narrating ? ` ${styles.medallionActive}` : ''}`}
        onClick={toggleNarrate}
        title={narrateLabel}
        aria-pressed={narrating}
        type="button"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M4 9h3l5-4v14l-5-4H4z" />
          <path d="M16 9c1.2 1.2 1.8 2 1.8 3s-.6 1.8-1.8 3" />
          {narrating && <path d="M19 6c2 2 3 4 3 6s-1 4-3 6" />}
        </svg>
        <span className={styles.medallionTooltip}>{narrateLabel}</span>
      </button>

      <button
        className={[
          styles.medallion,
          styles.medallionAi,
          imgState === 'done' ? styles.medallionDone : '',
        ].filter(Boolean).join(' ')}
        onClick={generateImage}
        title={imgLabel}
        disabled={imgState === 'running'}
        type="button"
      >
        {imgState === 'running' ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
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
          >
            <rect x="3" y="5" width="18" height="14" rx="1" />
            <circle cx="8.5" cy="10" r="1.4" />
            <path d="M3 17l5-5 4 4 3-3 6 5" />
            <path
              d="M18 3l.6 1.6L20 5l-1.4.4L18 7l-.6-1.6L16 5l1.4-.4z"
              fill="currentColor"
              stroke="none"
            />
          </svg>
        )}
        <span className={styles.medallionTooltip}>{imgLabel}</span>
      </button>
    </div>
  );
}

// ── StoryReader ───────────────────────────────────────────────────────────────

interface StoryReaderProps {
  story: StoryNode;
}

function StoryReader({ story }: StoryReaderProps): React.ReactElement {
  const characters = story.fieldCharacters ?? [];

  const formattedDate = story.fieldSessionDate
    ? new Date(story.fieldSessionDate).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric',
      })
    : null;

  return (
    <div key={story.id} className={styles.storyContent}>
      <header className={styles.storyHeader}>
        <h2 className={styles.storyTitle}>{story.title}</h2>
        <div className={styles.storyMeta}>
          {story.fieldStoryNumber !== null && (
            <span className={styles.storySession}>
              Session {story.fieldStoryNumber}
            </span>
          )}
          {formattedDate && (
            <time className={styles.storyDate} dateTime={story.fieldSessionDate ?? ''}>
              {formattedDate}
            </time>
          )}
        </div>
        {characters.length > 0 && (
          <p className={styles.storyCharacters}>
            {characters.map(c => c.title).join(' · ')}
          </p>
        )}
      </header>

      {story.fieldBody && (
        <div className={styles.scroll}>
          <div className={styles.scrollDowel} aria-hidden="true" />
          <div className={styles.parchment}>
            <div
              className={styles.body}
              dangerouslySetInnerHTML={{ __html: story.fieldBody.processed }}
            />
            <p className={styles.ornament}>{'❧ · ❧ · ❧'}</p>
            <StoryMedallions title={story.title} />
          </div>
          <div className={styles.scrollDowel} aria-hidden="true" />
        </div>
      )}
    </div>
  );
}

// ── CampaignReaderPage ────────────────────────────────────────────────────────

const CampaignReaderPage: React.FC<PageProps<CampaignReaderData>> = ({
  data,
  location,
}) => {
  const stories = data.allNodeStory.nodes;
  const [activeIndex, setActiveIndex] = useState(0);

  if (stories.length === 0) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p className={styles.empty}>No stories found for this campaign.</p>
      </BaseTemplate>
    );
  }

  const activeStory = stories[activeIndex];
  const hasPrev = activeIndex > 0;
  const hasNext = activeIndex < stories.length - 1;

  const goToPrev = (): void => {
    if (hasPrev) setActiveIndex(i => i - 1);
  };

  const goToNext = (): void => {
    if (hasNext) setActiveIndex(i => i + 1);
  };

  const tocEntries = stories.slice(0, ROMAN_NUMERALS.length);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.shell}>

        {/* TOC Sidebar */}
        <nav aria-label="Table of contents">
          <div className={styles.toc}>
            <h2 className={styles.tocHeading}>Table of Contents</h2>
            <div className={styles.tocDivider} aria-hidden="true" />
            <ol className={styles.tocList}>
              {tocEntries.map((story, index) => (
                <li key={story.id} className={styles.tocItem}>
                  <button
                    type="button"
                    className={
                      index === activeIndex
                        ? `${styles.tocButton} ${styles.tocButtonActive}`
                        : styles.tocButton
                    }
                    onClick={() => setActiveIndex(index)}
                    aria-current={index === activeIndex ? 'true' : undefined}
                  >
                    <span className={styles.tocNumeral}>{toRoman(index)}</span>
                    <span className={styles.tocLabel}>{story.title}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
        </nav>

        {/* Reader column */}
        <div className={styles.reader}>

          {/* Campaign eyebrow */}
          <div className={styles.eyebrow} aria-hidden="true">
            <span className={styles.eyebrowText}>Campaign · New Beginnings</span>
          </div>

          {/* Campaign title */}
          <h1 className={styles.campaignTitle}>The New Beginnings</h1>

          {/* Active story — key forces remount + CSS fade-in on change */}
          <StoryReader key={activeStory.id} story={activeStory} />

          {/* Prev / Next navigation */}
          <div className={styles.nav}>
            <button
              type="button"
              className={styles.navButton}
              onClick={goToPrev}
              disabled={!hasPrev}
              aria-label="Previous story"
            >
              &larr; Previous
            </button>
            <button
              type="button"
              className={styles.navButton}
              onClick={goToNext}
              disabled={!hasNext}
              aria-label="Next story"
            >
              Next &rarr;
            </button>
          </div>
        </div>
      </div>
    </BaseTemplate>
  );
};

// ── GraphQL page query ────────────────────────────────────────────────────────

export const query = graphql`
  query CampaignReader {
    allNodeStory(sort: { fieldStoryNumber: ASC }) {
      nodes {
        id
        title
        fieldStoryNumber
        fieldSessionDate
        fieldBody {
          processed
        }
        fieldCharacters {
          ... on node__character {
            title
          }
        }
        path {
          alias
        }
      }
    }
  }
`;

export const Head: HeadFC<CampaignReaderData> = () => (
  <title>Campaign Reader | D&D Consultant</title>
);

export default CampaignReaderPage;
