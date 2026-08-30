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
 *
 * After cleanHtml(), exact-case spell names become `.spell-mention` links
 * with a hover tooltip. SpellSheet turns that off so rules text does not
 * link to itself.
 */

import * as React from 'react';
import { createPortal } from 'react-dom';
import { navigate } from 'gatsby';
import { cleanHtml } from '../../utils/cleanHtml';
import { highlightSpellMentions } from '../../utils/highlightSpellMentions';
import {
  type SpellCatalogEntry,
  useSpellCatalog,
} from '../../hooks/useSpellCatalog';
import { levelLabel } from '../../types/spell';
import * as styles from '../../templates/story.module.css';
import * as tipStyles from './SpellMentionTooltip.module.css';

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
  /** Wrap vault spell names as links. Off on the spell sheet itself. */
  highlightSpells?: boolean;
}

const DEFAULT_UNFURL_HINT = 'Tap to unfurl the chronicle';
const DEFAULT_UNFURL_LABEL = 'Unfurl chronicle';
const DEFAULT_ROLL_UP_LABEL = 'Roll up chronicle';

interface TipState {
  spell: SpellCatalogEntry;
  x: number;
  y: number;
}

function mentionFromEvent(target: EventTarget | null): HTMLAnchorElement | null {
  if (!(target instanceof Element)) {
    return null;
  }
  return target.closest('a.spell-mention');
}

export function StoryScroll({
  html,
  onUnfurl,
  unfurlHint = DEFAULT_UNFURL_HINT,
  unfurlLabel = DEFAULT_UNFURL_LABEL,
  rollUpLabel = DEFAULT_ROLL_UP_LABEL,
  highlightSpells = true,
}: StoryScrollProps): React.ReactElement | null {
  const [open, setOpen] = React.useState(false);
  const [tip, setTip] = React.useState<TipState | null>(null);
  const catalog = useSpellCatalog();

  if (!html.trim()) {
    return null;
  }

  const cleaned = cleanHtml(html);
  const refs = catalog.map(entry => ({
    id: entry.id,
    name: entry.name,
    path: entry.path,
  }));
  const body = highlightSpells
    ? highlightSpellMentions(cleaned, refs)
    : cleaned;

  const toggle = (): void => {
    setOpen(wasOpen => {
      if (!wasOpen) {
        onUnfurl?.();
      }
      return !wasOpen;
    });
  };

  const onClick = (event: React.MouseEvent<HTMLDivElement>): void => {
    const link = mentionFromEvent(event.target);
    if (link == null) {
      return;
    }
    const href = link.getAttribute('href');
    if (href == null || href === '') {
      return;
    }
    event.preventDefault();
    setTip(null);
    void navigate(href);
  };

  const onMouseOver = (event: React.MouseEvent<HTMLDivElement>): void => {
    const link = mentionFromEvent(event.target);
    if (link == null) {
      return;
    }
    const id = link.getAttribute('data-spell');
    const spell = catalog.find(entry => entry.id === id);
    if (spell == null) {
      return;
    }
    const rect = link.getBoundingClientRect();
    setTip({
      spell,
      x: rect.left,
      y: rect.bottom + 8,
    });
  };

  const onMouseOut = (event: React.MouseEvent<HTMLDivElement>): void => {
    const link = mentionFromEvent(event.target);
    if (link == null) {
      return;
    }
    const related = event.relatedTarget;
    if (related instanceof Node && link.contains(related)) {
      return;
    }
    setTip(null);
  };

  const meta = tip == null
    ? ''
    : [
      levelLabel(tip.spell.level),
      tip.spell.school,
      tip.spell.castingTime,
      tip.spell.spellRange,
    ].filter((part): part is string => part != null && part !== '').join(' · ');

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
              dangerouslySetInnerHTML={{ __html: body }}
              onClick={onClick}
              onMouseOver={onMouseOver}
              onMouseOut={onMouseOut}
            />
            <p className={styles.ornament}>{'-- . -- . --'}</p>
          </div>
        </div>
      </div>

      <div className={styles.scrollDowel} aria-hidden="true" />

      {tip != null && typeof document !== 'undefined' && createPortal(
        <div
          className={tipStyles.tip}
          style={{ left: tip.x, top: tip.y }}
          role="tooltip"
        >
          <p className={tipStyles.name}>{tip.spell.name}</p>
          {meta !== '' && <p className={tipStyles.meta}>{meta}</p>}
          {tip.spell.excerpt !== '' && (
            <p className={tipStyles.excerpt}>{tip.spell.excerpt}</p>
          )}
        </div>,
        document.body,
      )}
    </div>
  );
}
