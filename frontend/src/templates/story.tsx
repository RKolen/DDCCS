import React, { useState } from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Divider } from '../components/atoms/Divider';
import { cleanHtml } from '../utils/cleanHtml';
import * as styles from './story.module.css';

interface CharacterImage {
  mediaImage: { url: string; alt: string } | null;
}

interface CharacterRef {
  title: string;
  image: CharacterImage | null;
}

interface StoryNode {
  title:       string;
  storyNumber: number | null;
  sessionDate: string | null;
  body:        { value: string; processed: string } | null;
  storyHooks:  Array<{ value: string }> | null;
  campaign:    { currentParty: Array<CharacterRef> | null } | null;
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

function ActionSidebar({ title }: { title: string }): React.ReactElement {
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
    <div className={styles.actionSidebar} role="group" aria-label={`Actions for ${title}`}>
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

function PartyPanel({ characters }: { characters: CharacterRef[] }): React.ReactElement {
  if (characters.length === 0) return <></>;

  return (
    <aside className={styles.partySidebar}>
      <h3 className={styles.partyTitle}>The Party</h3>
      <ul className={styles.partyList}>
        {characters.map(c => (
          <li key={c.title} className={styles.partyCard}>
            <div className={styles.partyAvatar}>
              {c.image?.mediaImage?.url ? (
                <img
                  src={c.image.mediaImage.url}
                  alt={c.image.mediaImage.alt || c.title}
                  className={styles.partyAvatarImg}
                />
              ) : (
                <span className={styles.partyAvatarInitial}>
                  {c.title.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            <span className={styles.partyName}>{c.title}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}

const StoryPage: React.FC<PageProps<StoryData, StoryPageContext>> = ({ data, location, pageContext }) => {
  const story = data.drupal?.node as StoryNode | null;
  const { prevPath, prevTitle, nextPath, nextTitle } = pageContext;
  const [scrollOpen, setScrollOpen] = useState(false);

  if (!story || !story.title) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Story not found.</p>
      </BaseTemplate>
    );
  }

  const characters = story.campaign?.currentParty ?? [];
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

        <div className={styles.storyLayout}>

          {/* Left: action buttons */}
          {story.body ? <ActionSidebar title={story.title} /> : <div />}

          {/* Center: main content */}
          <div className={styles.storyMain}>
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
            </header>

            <Divider icon="scroll-unfurled" />

            {story.body && (
              <div className={styles.scroll}>
                <button
                  type="button"
                  className={styles.scrollDowelBtn}
                  onClick={() => setScrollOpen(o => !o)}
                  aria-expanded={scrollOpen}
                  aria-label={scrollOpen ? 'Roll up chronicle' : 'Unfurl chronicle'}
                >
                  <div className={styles.scrollDowel} aria-hidden="true" />
                  {!scrollOpen && (
                    <span className={styles.scrollHint}>Tap to unfurl the chronicle</span>
                  )}
                </button>

                <div className={`${styles.scrollBody} ${scrollOpen ? styles.scrollBodyOpen : ''}`}>
                  <div className={styles.scrollBodyInner}>
                    <div className={styles.parchment}>
                      <div
                        className={styles.body}
                        dangerouslySetInnerHTML={{ __html: cleanHtml(story.body.processed) }}
                      />
                      <p className={styles.ornament}>{'-- . -- . --'}</p>
                    </div>
                  </div>
                </div>

                <div className={styles.scrollDowel} aria-hidden="true" />
              </div>
            )}

            {hooks.length > 0 && (
              <aside className={styles.hooks}>
                <h3 className={styles.hooksTitle}>Story Hooks</h3>
                <ul className={styles.hooksList}>
                  {hooks.map((hook, i) => (
                    <li key={`hook-${String(i)}`} className={styles.hookItem}>{hook.value}</li>
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

          {/* Right: party panel */}
          <PartyPanel characters={characters} />

        </div>
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
          campaign {
            ... on Drupal_TermCampaign {
              currentParty {
                ... on Drupal_NodeCharacter {
                  title
                  image {
                    ... on Drupal_MediaImage {
                      mediaImage { url alt }
                    }
                  }
                }
              }
            }
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
