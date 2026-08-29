/**
 * The chronicle scroll: a story body that unfurls between two dowels.
 *
 * Lifted out of the story template so the console's reader shows the identical
 * thing rather than a copy that drifts. The furled default is deliberate - the
 * unfurl is the point, not friction to design away - so both surfaces keep it.
 *
 * Styles stay in `templates/story.module.css`, which owns the parchment and
 * dowel treatment; moving them would change the story page's look for no gain.
 *
 * `onUnfurl` fires on the opening edge only, which is where a scroll sound
 * belongs when there is one.
 */

import * as React from 'react';
import { cleanHtml } from '../../utils/cleanHtml';
import * as styles from '../../templates/story.module.css';

export interface StoryScrollProps {
  /** The story body as Drupal's processed HTML. */
  html: string;
  /** Called when the scroll is opened, never when it is rolled up. */
  onUnfurl?: () => void;
  /** Hint shown on the furled dowel. Defaults to the chronicle wording. */
  unfurlHint?: string;
  /** Accessible name when the scroll is furled. */
  unfurlLabel?: string;
  /** Accessible name when the scroll is open. */
  rollUpLabel?: string;
}

const DEFAULT_UNFURL_HINT = 'Tap to unfurl the chronicle';
const DEFAULT_UNFURL_LABEL = 'Unfurl chronicle';
const DEFAULT_ROLL_UP_LABEL = 'Roll up chronicle';

export function StoryScroll({
  html,
  onUnfurl,
  unfurlHint = DEFAULT_UNFURL_HINT,
  unfurlLabel = DEFAULT_UNFURL_LABEL,
  rollUpLabel = DEFAULT_ROLL_UP_LABEL,
}: StoryScrollProps): React.ReactElement | null {
  const [open, setOpen] = React.useState(false);

  if (!html.trim()) {
    return null;
  }

  const toggle = (): void => {
    setOpen(wasOpen => {
      if (!wasOpen) {
        onUnfurl?.();
      }
      return !wasOpen;
    });
  };

  return (
    <div className={styles.scroll}>
      <button
        type="button"
        className={styles.scrollDowelBtn}
        onClick={toggle}
        aria-expanded={open}
        aria-label={open ? rollUpLabel : unfurlLabel}
      >
        <div className={styles.scrollDowel} aria-hidden="true" />
        {!open && <span className={styles.scrollHint}>{unfurlHint}</span>}
      </button>

      <div className={`${styles.scrollBody} ${open ? styles.scrollBodyOpen : ''}`}>
        <div className={styles.scrollBodyInner}>
          <div className={styles.parchment}>
            <div
              className={styles.body}
              dangerouslySetInnerHTML={{ __html: cleanHtml(html) }}
            />
            <p className={styles.ornament}>{'-- . -- . --'}</p>
          </div>
        </div>
      </div>

      <div className={styles.scrollDowel} aria-hidden="true" />
    </div>
  );
}
