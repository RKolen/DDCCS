import React from 'react';
import { GameIcon } from '../atoms/GameIcon';
import * as styles from './Navigation.module.css';

export interface NavLink {
  label: string;
  path: string;
  active?: boolean;
}

interface NavigationProps {
  campaignTitle?: string;
  links: NavLink[];
  renderLink?: RenderLinkFn;
}

type RenderLinkFn = (props: {
  href: string;
  className: string;
  children: React.ReactNode;
}) => React.ReactElement;

const defaultRenderLink: RenderLinkFn = ({ href, className, children }) => (
  <a href={href} className={className}>{children}</a>
);

export function Navigation({
  campaignTitle = 'New Beginnings',
  links,
  renderLink = defaultRenderLink,
}: NavigationProps): React.ReactElement {
  return (
    <nav className={styles.nav} aria-label="Site navigation">
      <a href="/" className={styles.brand} aria-label="Home">
        <GameIcon
          name="crossed-swords"
          size={20}
          colorFilter="var(--filter-gold-bright)"
          decorative
        />
        <span className={styles.brandName}>{campaignTitle}</span>
      </a>

      <div className={styles.links}>
        {links.map(link =>
          renderLink({
            href: link.path,
            className: `${styles.link}${link.active ? ` ${styles.linkActive}` : ''}`,
            children: link.label.toUpperCase(),
          })
        )}
      </div>
    </nav>
  );
}
