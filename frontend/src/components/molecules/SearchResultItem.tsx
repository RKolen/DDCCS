import React from 'react';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import type { SearchResult } from '../../types/search';
import * as styles from './SearchResultItem.module.css';

interface SearchResultItemProps {
  result: SearchResult;
}

const TYPE_ICONS: Record<string, GameIconName> = {
  character: 'cowled',
  npc: 'hood',
  spell: 'magic-swirl',
  item: 'swap-bag',
  feat: 'stars-stack',
  monster: 'skull',
};

const DEFAULT_ICON: GameIconName = 'scroll-unfurled';

export function SearchResultItem({ result }: SearchResultItemProps): React.ReactElement {
  const iconName = TYPE_ICONS[result.type] ?? DEFAULT_ICON;

  return (
    <li className={styles.item}>
      <GameIcon name={iconName} size={20} decorative />
      <span className={styles.title}>{result.title}</span>
      <Badge label={result.type} />
      <span className={styles.relevance}>
        {(result.relevance * 100).toFixed(1)}% match
      </span>
    </li>
  );
}
