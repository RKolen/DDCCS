/**
 * Wrap exact-case spell names in processed HTML with mention links.
 *
 * Walks text between tags only. Skips anything already inside `a`, `code`,
 * or `pre`. Longest name wins so "Cure Wounds" is not split into "Cure".
 * Matching is case-sensitive and whole-word (`identified` is not Identify).
 */

export interface SpellMentionRef {
  id: string;
  name: string;
  path: string;
}

const SKIP_TAGS = new Set(['a', 'code', 'pre', 'script', 'style']);
const VOID_TAGS = new Set(['br', 'hr', 'img', 'input', 'meta', 'link', 'wbr']);

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;');
}

function wrapMatch(spell: SpellMentionRef): string {
  return (
    `<a class="spell-mention" href="${escapeAttr(spell.path)}"` +
    ` data-spell="${escapeAttr(spell.id)}">${spell.name}</a>`
  );
}

function highlightText(
  text: string,
  pattern: RegExp,
  byName: Map<string, SpellMentionRef>,
): string {
  pattern.lastIndex = 0;
  return text.replace(pattern, matched => {
    const spell = byName.get(matched);
    return spell == null ? matched : wrapMatch(spell);
  });
}

function tagName(tag: string): string | null {
  const match = /^<\/?([a-zA-Z][a-zA-Z0-9]*)/.exec(tag);
  return match == null ? null : match[1].toLowerCase();
}

/**
 * Return HTML with spell names wrapped as `.spell-mention` links.
 */
export function highlightSpellMentions(
  html: string,
  spells: readonly SpellMentionRef[],
): string {
  const usable = spells
    .filter(spell => spell.name !== '' && spell.path !== '')
    .slice()
    .sort((a, b) => b.name.length - a.name.length);
  if (usable.length === 0 || html === '') {
    return html;
  }

  const byName = new Map<string, SpellMentionRef>();
  usable.forEach(spell => {
    if (!byName.has(spell.name)) {
      byName.set(spell.name, spell);
    }
  });

  const alternation = usable.map(spell => escapeRegExp(spell.name)).join('|');
  const pattern = new RegExp(`(?<![A-Za-z0-9])(?:${alternation})(?![A-Za-z0-9])`, 'g');

  let out = '';
  let index = 0;
  const skipStack: string[] = [];

  while (index < html.length) {
    if (html[index] !== '<') {
      const next = html.indexOf('<', index);
      const end = next === -1 ? html.length : next;
      const text = html.slice(index, end);
      out += skipStack.length > 0
        ? text
        : highlightText(text, pattern, byName);
      index = end;
      continue;
    }

    const close = html.indexOf('>', index);
    if (close === -1) {
      out += html.slice(index);
      break;
    }
    const tag = html.slice(index, close + 1);
    out += tag;
    const name = tagName(tag);
    if (name != null && SKIP_TAGS.has(name) && !VOID_TAGS.has(name)) {
      const isClose = tag.startsWith('</');
      const selfClosing = tag.endsWith('/>');
      if (!selfClosing) {
        if (isClose) {
          const stacked = skipStack.lastIndexOf(name);
          if (stacked !== -1) {
            skipStack.splice(stacked, 1);
          }
        } else {
          skipStack.push(name);
        }
      }
    }
    index = close + 1;
  }

  return out;
}
