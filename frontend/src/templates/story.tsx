import React, { useState } from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Divider } from '../components/atoms/Divider';
import * as styles from './story.module.css';

interface StoryData {
  nodeStory: {
    title:            string;
    fieldStoryNumber: number | null;
    fieldSessionDate: string | null;
    fieldBody:        { value: string; processed: string } | null;
    fieldStoryHooks:  Array<{ value: string }> | null;
    fieldCharacters:  Array<{ title: string }> | null;
  } | null;
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

  const narrateLabel = narrating ? 'Listening…' : 'Narrate';
  const imgLabel =
    imgState === 'idle'    ? 'Generate image' :
    imgState === 'running' ? 'Conjuring…' :
    'View image';

  return (
    <div className={styles.medallions} role="group" aria-label={`Actions for ${title}`}>
      <button
        className={`${styles.medallion}${narrating ? ` ${styles.medallionActive}` : ''}`}
        onClick={toggleNarrate}
        title={narrateLabel}
        aria-pressed={narrating}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
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
      >
        {imgState === 'running' ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="8" strokeDasharray="14 8" className={styles.medallionSpinner}/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
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

const StoryPage: React.FC<PageProps<StoryData>> = ({ data, location }) => {
  const story = data.nodeStory;

  if (!story) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Story not found.</p>
      </BaseTemplate>
    );
  }

  const characters = story.fieldCharacters ?? [];
  const hooks = story.fieldStoryHooks ?? [];

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.meta}>
            {story.fieldStoryNumber !== null && (
              <span className={styles.session}>Session {story.fieldStoryNumber}</span>
            )}
            {story.fieldSessionDate && (
              <time className={styles.date} dateTime={story.fieldSessionDate}>
                {new Date(story.fieldSessionDate).toLocaleDateString('en-GB', {
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
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query StoryPage($id: String!) {
    nodeStory(id: { eq: $id }) {
      title
      fieldStoryNumber
      fieldSessionDate
      fieldBody { value processed }
      fieldStoryHooks { value }
      fieldCharacters {
        ... on node__character { title }
      }
    }
  }
`;

export const Head: HeadFC<StoryData> = ({ data }) => (
  <title>{data.nodeStory?.title ?? 'Story'} | D&D Consultant</title>
);

export default StoryPage;
