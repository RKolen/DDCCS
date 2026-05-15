import React, { useState } from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Divider } from '../components/atoms/Divider';
import { cleanHtml } from '../utils/cleanHtml';
import * as styles from './story.module.css';

interface StoryNode {
  title:       string;
  storyNumber: number | null;
  sessionDate: string | null;
  body:        { value: string; processed: string } | null;
  storyHooks:  Array<{ value: string }> | null;
  characters:  Array<{ title: string }> | null;
}

interface StoryData {
  drupal: {
    node: Partial<StoryNode> | null;
  };
}

interface StoryPageContext {
  id:        string;
  prevPath:  string | null;
  prevTitle: string | null;
  nextPath:  string | null;
  nextTitle: string | null;
}

type ImageState = 'idle' | 'running' | 'done';

function StoryMedallions({ title }: { title: string }): React.ReactElement {
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
    imgState === 'running' ? 'Conjuring...' :
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
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M4 9h3l5-4v14l-5-4H4z"/>
          <path d="M16 9c1.2 1.2 1.8 2 1.8 3s-.6 1.8-1.8 3"/>
          {narrating && <path d="M19 6c2 2 3 4 3 6s-1 4-3 6"/>}
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
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="8" strokeDasharray="14 8" className={styles.medallionSpinner}/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="3" y="5" width="18" height="14" rx="1"/>
            <circle cx="8.5" cy="10" r="1.4"/>
            <path d="M3 17l5-5 4 4 3-3 6 5"/>
            <path d="M18 3l.6 1.6L20 5l-1.4.4L18 7l-.6-1.6L16 5l1.4-.4z" fill="currentColor" stroke="none"/>
          </svg>
        )}
        <span className={styles.medallionTooltip}>{imgLabel}</span>
      </button>
    </div>
  );
}

const StoryPage: React.FC<PageProps<StoryData, StoryPageContext>> = ({ data, location, pageContext }) => {
  const story = data.drupal?.node as StoryNode | null;
  const { prevPath, prevTitle, nextPath, nextTitle } = pageContext;

  if (!story || !story.title) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Story not found.</p>
      </BaseTemplate>
    );
  }

  const characters = story.characters ?? [];
  const hooks = story.storyHooks ?? [];

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>

        <Link to="/stories/" className={styles.backLink}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          All Stories
        </Link>

        <header className={styles.header}>
          <div className={styles.meta}>
            {story.storyNumber !== null && story.storyNumber !== undefined && (
              <span className={styles.session}>Session {story.storyNumber}</span>
            )}
            {story.sessionDate && (
              <time className={styles.date} dateTime={story.sessionDate}>
                {new Date(story.sessionDate).toLocaleDateString('en-GB', {
                  day: 'numeric', month: 'long', year: 'numeric',
                })}
              </time>
            )}
          </div>
          <h1 className={styles.title}>{story.title}</h1>
          {characters.length > 0 && (
            <p className={styles.party}>
              {characters.map(c => c.title).join(' · ')}
            </p>
          )}
        </header>

        <Divider icon="scroll-unfurled" />

        {story.body && (
          <div className={styles.scroll}>
            <div className={styles.scrollDowel} aria-hidden="true" />
            <div className={styles.parchment}>
              <div
                className={styles.body}
                dangerouslySetInnerHTML={{ __html: cleanHtml(story.body.processed) }}
              />
              <p className={styles.ornament}>{'-- . -- . --'}</p>
              <StoryMedallions title={story.title} />
            </div>
            <div className={styles.scrollDowel} aria-hidden="true" />
          </div>
        )}

        {hooks.length > 0 && (
          <aside className={styles.hooks}>
            <h3 className={styles.hooksTitle}>Story Hooks</h3>
            <ul className={styles.hooksList}>
              {hooks.map((hook, i) => (
                <li key={i} className={styles.hookItem}>{hook.value}</li>
              ))}
            </ul>
          </aside>
        )}

        <nav className={styles.storyNav} aria-label="Story navigation">
          {prevPath ? (
            <Link to={prevPath} className={styles.navBtn}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
              <span className={styles.navBtnLabel}>
                <span className={styles.navBtnEyebrow}>Previous</span>
                <span className={styles.navBtnTitle}>{prevTitle}</span>
              </span>
            </Link>
          ) : <span />}

          {nextPath && (
            <Link to={nextPath} className={`${styles.navBtn} ${styles.navBtnNext}`}>
              <span className={styles.navBtnLabel}>
                <span className={styles.navBtnEyebrow}>Next</span>
                <span className={styles.navBtnTitle}>{nextTitle}</span>
              </span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </Link>
          )}
        </nav>

      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query StoryPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeStory {
          title
          storyNumber
          sessionDate
          body { value processed }
          storyHooks { value }
          characters {
            ... on Drupal_NodeCharacter { title }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC<StoryData> = ({ data }) => {
  const story = data.drupal?.node as StoryNode | null;
  return <title>{story?.title ?? 'Story'} | D&D Consultant</title>;
};

export default StoryPage;
