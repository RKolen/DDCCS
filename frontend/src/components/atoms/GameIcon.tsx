/**
 * GameIcon — renders a game SVG icon inline.
 *
 * Fetches the SVG from /icons/game/<name>.svg, strips the black background
 * rect, replaces all fill values with `currentColor`, and inlines the markup.
 * Colour is set exclusively via CSS — the `color` prop maps to the CSS `color`
 * property on the wrapper, defaulting to `var(--color-gold-mid)`.
 *
 * `colorFilter` applies a CSS filter string on the wrapper instead of setting
 * `color` directly; used by existing organism callers for hue-rotate tinting.
 */

import * as React from 'react';
import type { GameIconName } from '../../types/icons';

export type { GameIconName };

interface GameIconProps {
  name: GameIconName;
  size?: number;
  color?: string;
  colorFilter?: string;
  label?: string;
  decorative?: boolean;
  className?: string;
}

const stripCache: Record<string, string> = {};

function loadAndStrip(name: string): Promise<string> {
  if (stripCache[name]) return Promise.resolve(stripCache[name]);
  return fetch(`/icons/game/${name}.svg`)
    .then(r => r.text())
    .then(raw => {
      const stripped = raw
        /* remove the solid black background rect */
        .replace(/<path d="M0 0h512v512H0z"><\/path>/g, '')
        .replace(/<path d="M0 0h512v512H0z"\/>/g, '')
        /* replace every hardcoded fill with currentColor */
        .replace(/fill="[^"]*"/g, 'fill="currentColor"');
      stripCache[name] = stripped;
      return stripped;
    });
}

export function GameIcon({
  name,
  size = 20,
  color = 'var(--color-gold-mid)',
  colorFilter,
  label,
  decorative = false,
  className,
}: GameIconProps): React.ReactElement {
  const [markup, setMarkup] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    loadAndStrip(name)
      .then(stripped => {
        if (cancelled) return;
        const sized = stripped
          .replace(/<svg([^>]*)width="\d+"/, `<svg$1width="${size}"`)
          .replace(/<svg([^>]*)height="\d+"/, `<svg$1height="${size}"`);
        setMarkup(sized);
      })
      .catch(() => { /* silently skip on fetch error */ });
    return () => { cancelled = true; };
  }, [name, size]);

  const wrapperStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    color: colorFilter ? undefined : color,
    ...(colorFilter ? { filter: colorFilter } : {}),
  };

  if (!markup) {
    return (
      <span
        style={{ ...wrapperStyle, width: size, height: size }}
        className={className}
      />
    );
  }

  return (
    <span
      role={decorative ? 'presentation' : 'img'}
      aria-label={decorative ? undefined : (label ?? name)}
      className={className}
      style={wrapperStyle}
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}
