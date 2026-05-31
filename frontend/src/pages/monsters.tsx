import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';

interface MonsterNode {
  id:               string;
  title:            string;
  challengeRating:  number | null;
  type:             { name: string } | null;
  monsterSize:      string | null;
  monsterAlignment: string | null;
  path:             string | null;
  image:            { mediaImage: { url: string; alt: string } | null } | null;
}

interface MonstersData {
  drupal: {
    nodeMonsters: {
      nodes: MonsterNode[];
    };
  } | null;
}

function crTierColor(cr: number | null): string {
  if (cr == null) return 'var(--color-neutral)';
  if (cr >= 17)   return 'var(--color-danger)';
  if (cr >= 11)   return 'var(--color-warning)';
  if (cr >= 5)    return 'var(--color-info)';
  return 'var(--color-success)';
}

const MonstersPage: React.FC<PageProps<MonstersData>> = ({ data, location }) => {
  const monsters = data?.drupal?.nodeMonsters?.nodes ?? [];

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div style={{ padding: '32px', maxWidth: 960, margin: '0 auto' }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 32,
          color: 'var(--color-gold-bright)', letterSpacing: '0.04em', marginBottom: 8,
        }}>
          Bestiary
        </h1>
        <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', color: 'var(--color-text-secondary)', marginBottom: 32 }}>
          {monsters.length} {monsters.length === 1 ? 'creature' : 'creatures'}
        </p>

        {monsters.length === 0 ? (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
            No monsters found. Create node--monster content in Drupal to populate the bestiary.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {monsters.map(m => {
              const color = crTierColor(m.challengeRating);
              const initials = m.title.split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase();
              return (
                <a
                  key={m.id}
                  href={m.path ?? '#'}
                  style={{
                    display: 'grid', gridTemplateColumns: '48px 1fr 48px',
                    gap: 16, alignItems: 'center', textDecoration: 'none',
                    background: 'var(--color-bg-surface)',
                    border: `1px solid var(--color-gold-border)`,
                    borderLeft: `3px solid ${color}`,
                    borderRadius: 8, padding: '12px 16px',
                  }}
                >
                  <div style={{
                    width: 48, height: 48, borderRadius: 6, overflow: 'hidden',
                    background: 'var(--color-bg-overlay)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {m.image?.mediaImage
                      ? <img src={m.image.mediaImage.url} alt={m.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      : <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--color-gold-mid)', fontWeight: 700 }}>{initials}</span>
                    }
                  </div>

                  <div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 17, color: 'var(--color-gold-bright)', fontWeight: 600, marginBottom: 3 }}>
                      {m.title}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-text-secondary)' }}>
                      {[m.monsterSize, m.type?.name, m.monsterAlignment].filter(Boolean).join(' · ')}
                    </div>
                  </div>

                  <div style={{ textAlign: 'center', flexShrink: 0 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color, lineHeight: 1 }}>
                      {m.challengeRating ?? '?'}
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 8, color, letterSpacing: '0.12em', textTransform: 'uppercase' }}>CR</div>
                  </div>
                </a>
              );
            })}
          </div>
        )}
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query MonstersList {
    drupal {
      nodeMonsters(first: 100) {
        nodes {
          id title challengeRating monsterSize monsterAlignment path
          type        { ... on Drupal_TermCreatureType { name } }
          image       { ... on Drupal_MediaImage { mediaImage { url alt } } }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Bestiary | D&amp;D Consultant</title>;

export default MonstersPage;
