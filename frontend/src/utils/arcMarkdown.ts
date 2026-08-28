/**
 * Parse a campaign-arc markdown document into story-arc fields and relations.
 *
 * Written against the shapes the DM's notes already use, so an existing
 * document imports without reformatting: `ACT I ... (Levels 6-8)` as a plain
 * line (premise before the first ACT, spine after), `### TIER n` setting the
 * tier for the `####` pairs below it, `#### A <-> The Epithet (Real Name)`
 * where the parenthetical is the character, the party-internal
 * `### A & B - description`, and pair tables written as `| A & B | note |`.
 *
 * Names are resolved against a supplied roster; anything unresolved is
 * reported so the console can show a preview before writing.
 */

import type { ArcFieldPayload, ArcRelationPayload, ArcRelationTier } from './arcPayload';

/** A character the importer can resolve names against. */
export interface RosterEntry {
  id: string;
  title: string;
}

/** One parsed relation, carrying the raw text behind each resolved end. */
export interface ParsedRelation extends ArcRelationPayload {
  /** The name as written in the document, for the preview. */
  sourceText: string;
  targetText: string;
}

export interface ArcImportResult {
  fields: ArcFieldPayload;
  /** Roster-table names that resolved, as character UUIDs. */
  partyIds: string[];
  partyRelations: ParsedRelation[];
  npcRelations: ParsedRelation[];
  /** Names the document mentions that no roster entry matched. */
  unmatched: string[];
}

const ARROWS = /↔|<->|↔/;
const ACT_LINE = /^ACT\s+[IVXLC]+\b/;
const TIER_HEADING = /^TIER\s+([123])\b/i;
const LEVEL_RANGE = /Levels?\s*(\d+)\s*[-–—]\s*(\d+)/g;

/** Strip markdown emphasis and trim, so "**Bree**" reads as a name. */
function clean(text: string): string {
  return text.replace(/\*\*|__|\*|`/g, '').trim();
}

/**
 * Pull the character names out of one side of a pair heading.
 *
 * The side may hold several targets joined by "&" or "+", each written as an
 * epithet with the real name in parentheses. When parentheses are present the
 * parenthetical wins, because that is the character; the epithet is a title
 * that matches nothing in the roster. A single parenthetical may itself hold
 * two names ("The Hobbits (Frodo Baggins & Samwise Gamgee)").
 */
function namesFromSide(side: string): string[] {
  const out: string[] = [];
  const push = (name: string): void => {
    const cleaned = clean(name);
    if (cleaned && !out.includes(cleaned)) {
      out.push(cleaned);
    }
  };

  /* Parentheses first: when a side names characters at all, it names them
     inside the parens, and one paren may hold two ("The Hobbits (Frodo
     Baggins & Samwise Gamgee)"). Splitting on "&" first would tear that
     pair apart. */
  const parens = Array.from(side.matchAll(/\(([^)]+)\)/g));
  if (parens.length > 0) {
    for (const match of parens) {
      for (const name of match[1].split(/\s*[&+,]\s*/)) {
        push(name);
      }
    }
    return out;
  }

  for (const name of side.split(/\s+[&+]\s+/)) {
    push(name);
  }
  return out;
}

/**
 * Resolve a written name to a roster entry.
 *
 * Progressively looser: exact, case-insensitive, then a whole-word match on
 * either side, which is what turns "Barliman" into "Barliman Butterbur" and
 * "Frodo" into "Frodo Baggins". A match that is ambiguous under the loose rule
 * is rejected rather than guessed at.
 */
export function resolveName(name: string, roster: RosterEntry[]): RosterEntry | null {
  const wanted = clean(name);
  if (!wanted) {
    return null;
  }
  const exact = roster.find(r => r.title === wanted);
  if (exact) {
    return exact;
  }
  const lower = wanted.toLowerCase();
  const ci = roster.filter(r => r.title.toLowerCase() === lower);
  if (ci.length === 1) {
    return ci[0];
  }
  const words = new Set(lower.split(/\s+/));
  const loose = roster.filter(r => {
    const parts = r.title.toLowerCase().split(/\s+/);
    return parts.some(p => words.has(p));
  });
  return loose.length === 1 ? loose[0] : null;
}

/** Build a relation for every source/target combination on a pair heading. */
function pairsFrom(
  sources: string[],
  targets: string[],
  tier: ArcRelationTier | undefined,
  type: string,
  note: string,
  roster: RosterEntry[],
  unmatched: Set<string>,
): ParsedRelation[] {
  const out: ParsedRelation[] = [];
  for (const sourceText of sources) {
    const source = resolveName(sourceText, roster);
    if (!source) {
      unmatched.add(sourceText);
      continue;
    }
    for (const targetText of targets) {
      const target = resolveName(targetText, roster);
      if (!target) {
        unmatched.add(targetText);
        continue;
      }
      if (source.id === target.id) {
        continue;
      }
      out.push({
        source: source.id,
        target: target.id,
        sourceText,
        targetText,
        type,
        tier,
        note,
      });
    }
  }
  return out;
}

/** Collect the widest level span the document mentions, as "min-max". */
function levelRange(text: string): string | undefined {
  let lo: number | null = null;
  let hi: number | null = null;
  for (const m of text.matchAll(LEVEL_RANGE)) {
    const a = Number(m[1]);
    const b = Number(m[2]);
    lo = lo === null ? a : Math.min(lo, a);
    hi = hi === null ? b : Math.max(hi, b);
  }
  return lo !== null && hi !== null ? `${lo}-${hi}` : undefined;
}

const TABLE_HEADER = /^(character|name|candidate|pair|party member|who|function|member)$/i;

/** A table row, read as either a roster name or an "A & B" pair. */
interface TableRows {
  /** First-column names from a roster table. */
  names: string[];
  /** Rows whose first cell is "A & B", with the rest of the row as the label. */
  pairs: Array<{ left: string; right: string; label: string }>;
}

/**
 * Read both table shapes the notes use.
 *
 * A roster table lists one character per row. A pair table writes the two ends
 * into the first cell ("| Aragorn & Frodo Baggins | Two keepers of a secret |"),
 * which is how most party-internal bonds are actually recorded - so reading
 * only the first column would import them as nonsense names.
 */
function tableRows(lines: string[]): TableRows {
  const names: string[] = [];
  const pairs: TableRows['pairs'] = [];
  for (const line of lines) {
    if (!line.trim().startsWith('|')) {
      continue;
    }
    const cells = line.split('|').map(c => c.trim()).filter(c => c !== '');
    if (cells.length < 2) {
      continue;
    }
    const first = clean(cells[0]);
    if (!first || /^-+$/.test(first) || TABLE_HEADER.test(first)) {
      continue;
    }
    const sides = first.split(/\s+&\s+/).map(clean).filter(Boolean);
    if (sides.length === 2) {
      pairs.push({ left: sides[0], right: sides[1], label: clean(cells[1] ?? '') });
      continue;
    }
    names.push(first);
  }
  return { names, pairs };
}

/**
 * Parse an arc markdown document.
 *
 * @param markdown
 *   The document text.
 * @param roster
 *   Characters names are resolved against, normally the campaign's PCs plus
 *   the NPCs available to the arc.
 *
 * @returns
 *   Arc fields, resolved party ids, both relation sides, and every name that
 *   failed to resolve.
 */
export function importArcMarkdown(markdown: string, roster: RosterEntry[]): ArcImportResult {
  const lines = markdown.split(/\r?\n/);
  const unmatched = new Set<string>();
  const partyRelations: ParsedRelation[] = [];
  const npcRelations: ParsedRelation[] = [];

  /* Body ends and the plot spine begins at the first ACT line. */
  const actIndex = lines.findIndex(l => ACT_LINE.test(l.trim()));
  const bodyLines = actIndex === -1 ? lines : lines.slice(0, actIndex);
  const plotLines = actIndex === -1 ? [] : lines.slice(actIndex);

  let tier: ArcRelationTier | undefined;
  let pending: { sources: string[]; targets: string[]; type: string; side: 'party' | 'npc' } | null = null;
  let noteLines: string[] = [];

  const flush = (): void => {
    if (!pending) {
      return;
    }
    const note = noteLines.join('\n').trim();
    const built = pairsFrom(
      pending.sources, pending.targets, tier, pending.type, note, roster, unmatched,
    );
    (pending.side === 'party' ? partyRelations : npcRelations).push(...built);
    pending = null;
    noteLines = [];
  };

  for (const raw of lines) {
    const heading = raw.match(/^(#{3,6})\s+(.*)$/);
    if (!heading) {
      if (pending) {
        noteLines.push(raw);
      }
      continue;
    }
    flush();
    const text = clean(heading[2]);

    const tierMatch = text.match(TIER_HEADING);
    if (tierMatch) {
      tier = Number(tierMatch[1]) as ArcRelationTier;
      continue;
    }

    if (ARROWS.test(text)) {
      const [left, right] = text.split(ARROWS);
      pending = {
        sources: namesFromSide(left ?? ''),
        targets: namesFromSide(right ?? ''),
        type: '',
        side: 'npc',
      };
      continue;
    }

    /* Party-internal shape: "A & B - what the bond is". */
    const dash = text.split(/\s+[-–—]\s+/);
    if (dash.length > 1 && /\s+&\s+/.test(dash[0])) {
      const names = dash[0].split(/\s+&\s+/).map(clean).filter(Boolean);
      if (names.length === 2) {
        pending = {
          sources: [names[0]],
          targets: [names[1]],
          type: dash.slice(1).join(' - ').trim(),
          side: 'party',
        };
      }
    }
  }
  flush();

  const { names, pairs } = tableRows(lines);

  const partyIds: string[] = [];
  for (const name of names) {
    const hit = resolveName(name, roster);
    if (hit) {
      if (!partyIds.includes(hit.id)) {
        partyIds.push(hit.id);
      }
    } else {
      unmatched.add(name);
    }
  }

  /* Pair tables carry no tier of their own; they read as thematic. */
  for (const pair of pairs) {
    partyRelations.push(
      ...pairsFrom([pair.left], [pair.right], 2, pair.label, '', roster, unmatched),
    );
  }

  const fields: ArcFieldPayload = {};
  const body = bodyLines
    .filter(l => {
      const s = l.trim();
      return !s.startsWith('|') && !s.startsWith('#') && !/^-{3,}$/.test(s);
    })
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  if (body) {
    fields.body = body;
  }
  const plot = plotLines.join('\n').trim();
  if (plot) {
    fields.overallPlot = plot;
  }
  const levels = levelRange(markdown);
  if (levels) {
    fields.levelRange = levels;
  }

  return {
    fields,
    partyIds,
    partyRelations,
    npcRelations,
    unmatched: Array.from(unmatched).sort(),
  };
}
