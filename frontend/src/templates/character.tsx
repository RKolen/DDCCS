import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Divider } from '../components/atoms/Divider';
import { Badge } from '../components/atoms/Badge';
import { cleanHtml } from '../utils/cleanHtml';
import * as styles from './character.module.css';

interface CharacterNode {
  title:            string;
  firstName:        string | null;
  nickname:         string | null;
  level:            number | null;
  armorClass:       number | null;
  maximumHitpoints: number | null;
  movementSpeed:    number | null;
  proficiencyBonus: number | null;
  personality: { value: string } | null;
}

interface CharacterData {
  drupal: {
    node: Partial<CharacterNode> | null;
  };
}

const CharacterPage: React.FC<PageProps<CharacterData>> = ({ data, location }) => {
  const char = data.drupal?.node as CharacterNode | null;

  if (!char?.title) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Character not found.</p>
      </BaseTemplate>
    );
  }

  const hp = char.maximumHitpoints ?? 0;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.name}>{char.title}</h1>
          {char.nickname && <p className={styles.nickname}>{char.nickname}</p>}
          <div className={styles.badges}>
            {char.level !== null && <Badge label={`Level ${char.level}`} variant="class" />}
          </div>
        </header>

        <Divider icon="crossed-swords" />

        <div className={styles.stats}>
          <div className={styles.statBlock}>
            <span className={styles.statLabel}>HP</span>
            <span className={styles.statValue}>{hp}</span>
          </div>
          {char.armorClass !== null && (
            <div className={styles.statBlock}>
              <span className={styles.statLabel}>AC</span>
              <span className={styles.statValue}>{char.armorClass}</span>
            </div>
          )}
          {char.movementSpeed !== null && (
            <div className={styles.statBlock}>
              <span className={styles.statLabel}>Speed</span>
              <span className={styles.statValue}>{char.movementSpeed} ft</span>
            </div>
          )}
          {char.proficiencyBonus !== null && (
            <div className={styles.statBlock}>
              <span className={styles.statLabel}>Prof</span>
              <span className={styles.statValue}>+{char.proficiencyBonus}</span>
            </div>
          )}
        </div>

        {char.personality?.value && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Personality</h2>
            <div
              className={styles.prose}
              dangerouslySetInnerHTML={{ __html: cleanHtml(char.personality.value) }}
            />
          </section>
        )}

      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query CharacterPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeCharacter {
          title
          firstName
          nickname
          level
          armorClass
          maximumHitpoints
          movementSpeed
          proficiencyBonus
          personality { value }
        }
      }
    }
  }
`;

export const Head: HeadFC<CharacterData> = ({ data }) => {
  const char = data.drupal?.node as CharacterNode | null;
  return <title>{char?.title ?? 'Character'} | D&D Consultant</title>;
};

export default CharacterPage;
