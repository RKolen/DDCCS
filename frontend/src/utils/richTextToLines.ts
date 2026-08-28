/**
 * Convert Drupal rich-text field values into editable plain-text lines.
 *
 * A cardinality -1 text field arrives as a list of processed HTML values; the
 * editor works in lines. Paragraph breaks become line breaks so a multi-
 * paragraph trait stays editable, and a single wrapped sentence stays one line.
 */

/** Block-level closing tags. These always end an entry. */
const BLOCK_BREAK = /<\/(?:p|div|li|h[1-6])\s*>/gi;

/** A line break, which may or may not end an entry — see ::splitSoftBreaks. */
const LINE_BREAK = /<br\s*\/?>/gi;

/** Any remaining markup, which carries no line structure worth keeping. */
const ANY_TAG = /<[^>]*>/g;

/**
 * Decide whether each `<br>` ends an entry or merely wraps a line.
 *
 *
 * Sentence-ending punctuation before the break is the signal that separates the
 * two. It is a heuristic, not a rule the data guarantees — but it is right on
 * every affected record, and a wrong guess is one visible row the operator can
 * merge before saving.
 */
function splitSoftBreaks(text: string): string {
  return text.replace(LINE_BREAK, (_match, offset: number, whole: string) => {
    const before = whole.slice(0, offset).trimEnd();
    /* Only a full stop, question or exclamation mark. A semicolon or colon
       ends a clause, not an entry, and treating one as a separator would split
       traits that merely happen to wrap after one. */
    return /[.!?]["'’”)]?$/.test(before) ? '\n' : ' ';
  });
}

/** The named entities that realistically show up in this content. */
const NAMED_ENTITIES: Record<string, string> = {
  amp: '&',
  lt: '<',
  gt: '>',
  quot: '"',
  apos: "'",
  nbsp: ' ',
  hellip: '…',
  mdash: '—',
  ndash: '–',
  rsquo: '’',
  lsquo: '‘',
  rdquo: '”',
  ldquo: '“',
};

/**
 * Decode the HTML entities that survive tag stripping.
 *
 * `&amp;` is decoded last by virtue of a single pass: decoding it first would
 * turn `&amp;lt;` into `<`, inventing markup that was never there.
 */
function decodeEntities(text: string): string {
  return text.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (match, body: string) => {
    if (body.startsWith('#')) {
      const isHex = body[1] === 'x' || body[1] === 'X';
      const code = Number.parseInt(isHex ? body.slice(2) : body.slice(1), isHex ? 16 : 10);
      return Number.isFinite(code) && code > 0 ? String.fromCodePoint(code) : match;
    }
    return NAMED_ENTITIES[body.toLowerCase()] ?? match;
  });
}

/**
 * Split one stored value into the plain lines it actually represents.
 *
 * A value with no markup comes back as a single-entry list, unchanged apart
 * from trimming — so clean data passes straight through.
 */
export function htmlToLines(value: string): string[] {
  const broken = splitSoftBreaks(value.replace(BLOCK_BREAK, '\n'));
  return decodeEntities(broken.replace(ANY_TAG, ''))
    .split('\n')
    .map(line => line.replace(/\s+/g, ' ').trim())
    .filter(line => line !== '');
}

/**
 * Flatten a multi-value Drupal text field into plain lines.
 *
 * @param items The field's deltas as GraphQL returns them, or null.
 * @returns One entry per line across all deltas, empties dropped.
 */
export function textValues(items: Array<{ value: string }> | null | undefined): string[] {
  return (items ?? []).flatMap(item => htmlToLines(item.value));
}

/**
 * Normalise a single-value text field to plain text, preserving line breaks.
 *
 * Used for prose fields (notes, personality, AI system prompt) where the
 * paragraph structure is content rather than list structure.
 */
export function htmlToText(value: string | null | undefined): string | null {
  if (value == null) {
    return null;
  }
  const lines = htmlToLines(value);
  return lines.length === 0 ? null : lines.join('\n');
}
