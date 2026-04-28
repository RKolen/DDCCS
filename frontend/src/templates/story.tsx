import React from 'react';
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
          <div
            className={styles.body}
            dangerouslySetInnerHTML={{ __html: story.fieldBody.processed }}
          />
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
