import * as React from 'react';
import { Link } from 'gatsby';
import type { HeadFC } from 'gatsby';

export default function NotFoundPage(): React.ReactElement {
  return (
    <div style={{
      display:        'flex',
      flexDirection:  'column',
      alignItems:     'center',
      justifyContent: 'center',
      minHeight:      '60vh',
      gap:            '16px',
      textAlign:      'center',
      padding:        '40px 20px',
    }}>
      <p style={{
        fontFamily: 'var(--font-display)',
        fontSize:   '1rem',
        color:      'var(--ink-muted)',
        letterSpacing: '.06em',
        textTransform: 'uppercase',
        margin:     0,
      }}>
        This story has not been written yet.
      </p>
      <Link
        to="/"
        style={{
          fontFamily:  'var(--font-mono)',
          fontSize:    '.8rem',
          color:       'var(--brass)',
          textDecoration: 'none',
          letterSpacing: '.04em',
        }}
      >
        Return to the console
      </Link>
    </div>
  );
}

export const Head: HeadFC = () => <title>Page not found</title>;
