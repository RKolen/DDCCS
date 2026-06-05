import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';

interface ItemNode {
  drupalId:               string;
  title:                  string;
  itemType:               string | null;
  isMagic:                boolean | null;
  itemRarity:             string | null;
  itemRequiresAttunement: boolean | null;
  edition:                { name: string } | null;
  path:                   string | null;
  image:                  { mediaImage: { url: string; alt: string } | null } | null;
}

interface ItemsData {
  allAllItem: { nodes: ItemNode[] };
}

import { rarityColor } from '../utils/rarityColor';

const ItemsPage: React.FC<PageProps<ItemsData>> = ({ data, location }) => {
  const items = data?.allAllItem?.nodes ?? [];

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div style={{ padding: '32px', maxWidth: 960, margin: '0 auto' }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 32,
          color: 'var(--color-gold-bright)', letterSpacing: '0.04em', marginBottom: 6,
        }}>
          Item Registry
        </h1>
        <p style={{
          fontFamily: 'var(--font-body)', fontStyle: 'italic',
          color: 'var(--color-text-secondary)', marginBottom: 32,
        }}>
          {items.length} {items.length === 1 ? 'item' : 'items'}
        </p>

        {items.length === 0 ? (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
            No items found.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {items.map(item => {
              const color = rarityColor(item.itemRarity);
              const initials = item.title.split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase();
              const isHomebrew = !item.edition || item.edition.name.toLowerCase() === 'homebrew';
              const href = item.path ?? '#';

              return (
                <Link
                  key={item.drupalId}
                  to={href}
                  style={{
                    display: 'grid', gridTemplateColumns: '44px 1fr auto',
                    gap: 16, alignItems: 'center', textDecoration: 'none',
                    background: 'var(--color-bg-surface)',
                    border: `1px solid var(--color-gold-border)`,
                    borderLeft: `3px solid ${item.isMagic ? color : 'var(--color-gold-muted)'}`,
                    borderRadius: 8, padding: '12px 16px',
                  }}
                >
                  {/* Sigil */}
                  <div style={{
                    width: 44, height: 44, borderRadius: 6, flexShrink: 0, overflow: 'hidden',
                    background: `radial-gradient(circle at 50% 30%, color-mix(in srgb, ${color} 18%, var(--color-bg-base)), var(--color-bg-base))`,
                    border: `1px solid ${item.isMagic ? `color-mix(in srgb, ${color} 50%, transparent)` : 'var(--color-gold-border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {item.image?.mediaImage
                      ? <img src={item.image.mediaImage.url} alt={item.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      : <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: item.isMagic ? color : 'var(--color-gold-mid)', fontWeight: 700 }}>{initials}</span>
                    }
                  </div>

                  <div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--color-gold-bright)', fontWeight: 600, marginBottom: 3 }}>
                      {item.title}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-text-secondary)' }}>
                      {item.itemType ?? '—'}
                      {item.itemRarity != null && (
                        <span style={{ color, textTransform: 'capitalize', marginLeft: 6 }}>· {item.itemRarity}</span>
                      )}
                      {item.itemRequiresAttunement && (
                        <span style={{ color: 'var(--color-warning)', marginLeft: 6 }}>· Attunement</span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 6, flexDirection: 'column', alignItems: 'flex-end' }}>
                    {item.isMagic && (
                      <span style={{
                        fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
                        letterSpacing: '0.12em', textTransform: 'uppercase', padding: '2px 7px',
                        borderRadius: 3, border: '1px solid var(--color-gold-border)',
                        color: 'var(--color-gold-bright)', background: 'var(--gold-a05)',
                      }}>Magic</span>
                    )}
                    <span style={{
                      fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
                      letterSpacing: '0.1em', textTransform: 'uppercase', padding: '2px 7px',
                      borderRadius: 3,
                      border: `1px solid ${isHomebrew ? '#c98ad133' : '#5b9bd533'}`,
                      color: isHomebrew ? '#c98ad1' : '#7fb0e8',
                    }}>
                      {isHomebrew ? 'Homebrew' : 'Official'}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query ItemsList {
    allAllItem {
      nodes {
        drupalId title itemType isMagic itemRarity itemRequiresAttunement path
        edition { name }
        image { mediaImage { url alt } }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Items | D&amp;D Consultant</title>;

export default ItemsPage;
