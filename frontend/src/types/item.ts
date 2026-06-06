/**
 * Item entity types — aligned with Drupal `node--item`.
 *
 * Live Drupal schema fields:
 *   - title                  string
 *   - path                   string | null
 *   - itemType               string  (lowercase: 'weapon', 'armor', 'ring', …)
 *   - itemRarity             string  ('common' | 'uncommon' | 'rare' | 'very_rake'
 *                                    | 'legendary' | 'artifact' | 'vestige')
 *   - isMagic                boolean
 *   - itemRequiresAttunement boolean
 *
 * Plus optional rich entity fields queried when available.
 */

/* ── Wire types — mirror Drupal exactly ──────────────────────────────── */

/** Raw rarity string as it lands from Drupal. Use `normalizeRarity` to map
 *  to the dash-form used by CSS classes. Our Drupal uses 'very_rake'
 *  (underscore) — this type accepts both the underscore and space variants. */
export type DrupalRarity =
  | 'common' | 'uncommon' | 'rare' | 'very_rake' | 'very rare'
  | 'legendary' | 'artifact' | 'vestige';

/** CSS-class friendly rarity. Drives the .rarityX modifiers and the
 *  --rarity-hue / --rarity-glow custom properties. */
export type ItemRarity =
  | 'common' | 'uncommon' | 'rare' | 'very-rare'
  | 'legendary' | 'artifact' | 'vestige';

/** Drupal stores itemType as a free string (lowercase). The labels and
 *  icons map off this. Unknown values fall back to 'gear'. */
export type ItemType =
  | 'weapon' | 'ranged_weapon' | 'armor' | 'shield'
  | 'ring' | 'staff' | 'wondrous' | 'scroll' | 'potion'
  | 'tool' | 'gear';

/** The shape the GraphQL fragments produce. Pass this to ItemCard
 *  and ItemSheet directly. */
export interface ItemNode {
  id?:                     string;
  title:                   string;
  path?:                   string | null;
  itemType:                string | null;
  itemRarity:              string | null;
  isMagic?:                boolean | null;
  itemRequiresAttunement?: boolean | null;
  body?:                   { value: string } | null;
  image?:                  { mediaImage?: { url: string; alt: string } | null } | null;

  /* ── Optional rich-entity fields ──────────────────────────────────── */
  epithet?:    string | null;
  subtype?:    string | null;
  weight?:     string | null;
  value?:      string | null;
  school?:     string | null;
  shortFlavour?: string | null;
  attunementRequirement?: string | null;
  mechanicsJson?: string | null;
  provenanceJson?: string | null;
  benefits?:    string[] | null;
  tags?:        string[] | null;
  /** Weapon subtype taxonomy terms (e.g. "Ranged", "Melee", "Shortbow"). Used
   *  to distinguish ranged weapons from melee when itemType is 'weapon'. */
  weaponSubtype?: Array<{ name: string }> | null;
  bearer?: {
    name:   string;
    status: string;
    charRef?: { id: string; path: string | null } | null;
  } | null;
  lastSeen?: string | null;
  related?:  Array<{ id: string; title: string; path: string | null }> | null;
  homebrew?: boolean | null;
}

/* ── Display/component shapes (derived) ──────────────────────────────── */

export interface ItemMechanic {
  label: string;
  value: string;
  unit?: string;
}

export interface ItemProvenanceEntry {
  era:  string;
  note: string;
}

export interface ItemBearer {
  name:   string;
  charId: string | null;
  charPath: string | null;
  status: string;
}

/** Fully-normalised shape the ItemSheet renders. Built by `toItemEntity`. */
export interface ItemEntity {
  id:         string;
  title:      string;
  path:       string | null;
  epithet:    string | null;
  type:       ItemType;
  typeLabel:  string;
  subtype:    string | null;
  rarity:     ItemRarity;
  rarityLabel: string;
  requiresAttunement: boolean;
  attunementRequirement: string | null;
  isMagic:    boolean;
  homebrew:   boolean;

  imageUrl:   string | null;
  imageAlt:   string | null;
  bodyHtml:   string | null;
  shortFlavour: string | null;

  weight:     string | null;
  value:      string | null;
  school:     string | null;

  mechanics:  ItemMechanic[];
  benefits:   string[];
  tags:       string[];
  provenance: ItemProvenanceEntry[];
  bearer:     ItemBearer | null;
  lastSeen:   string | null;
  related:    Array<{ id: string; title: string; path: string | null }>;
}

/* ── Normalisers ─────────────────────────────────────────────────────── */

const RARITY_LABEL_MAP: Record<string, ItemRarity> = {
  common:      'common',
  uncommon:    'uncommon',
  rare:        'rare',
  'very rare': 'very-rare',
  'very-rare': 'very-rare',
  very_rake:   'very-rare',
  legendary:   'legendary',
  artifact:    'artifact',
  vestige:     'vestige',
};

export function normalizeRarity(raw: string | null | undefined): ItemRarity {
  if (!raw) return 'common';
  const key = raw.toLowerCase().trim();
  return RARITY_LABEL_MAP[key] ?? 'common';
}

export function rarityDisplayLabel(r: ItemRarity): string {
  if (r === 'very-rare') return 'Very Rare';
  return r.charAt(0).toUpperCase() + r.slice(1);
}

/** Maps Drupal's lowercased itemType to one of the curated `ItemType`
 *  values. Unknowns fall back to 'gear' so an icon and label always show.
 *
 *  When `itemType` is generic 'weapon', pass the weaponSubtype terms to
 *  distinguish ranged weapons (any subtype whose name contains "Ranged"). */
export function normalizeType(
  raw: string | null | undefined,
  weaponSubtype?: Array<{ name: string }> | null,
): ItemType {
  const k = (raw ?? '').toLowerCase().replace(/\s+/g, '_').trim();
  switch (k) {
    case 'weapon':
    case 'melee_weapon':
      if (weaponSubtype?.some(s => /ranged/i.test(s.name))) {
        return 'ranged_weapon';
      }
      return 'weapon';
    case 'ranged_weapon':
    case 'bow':
    case 'crossbow':       return 'ranged_weapon';
    case 'armor':          return 'armor';
    case 'shield':         return 'shield';
    case 'ring':           return 'ring';
    case 'staff':
    case 'rod':
    case 'wand':           return 'staff';
    case 'wondrous':
    case 'wondrous_item':
    case 'magic_item':     return 'wondrous';
    case 'scroll':         return 'scroll';
    case 'potion':         return 'potion';
    case 'tool':
    case 'kit':            return 'tool';
    default:               return 'gear';
  }
}

const TYPE_LABEL: Record<ItemType, string> = {
  weapon:        'Melee Weapon',
  ranged_weapon: 'Ranged Weapon',
  armor:         'Armor',
  shield:        'Shield',
  ring:          'Ring',
  staff:         'Staff',
  wondrous:      'Wondrous',
  scroll:        'Scroll',
  potion:        'Potion',
  tool:          'Tool',
  gear:          'Gear',
};

export function typeDisplayLabel(t: ItemType): string { return TYPE_LABEL[t]; }

function safeParseJson<T>(raw: string | null | undefined, fallback: T): T {
  if (!raw) return fallback;
  try { return JSON.parse(raw) as T; } catch { return fallback; }
}

/** Build the rich `ItemEntity` shape from the Drupal `ItemNode`. Optional
 *  fields default to safe empties — the ItemSheet renders sparsely when
 *  the back end has only the legacy 6-field shape. */
export function toItemEntity(node: ItemNode): ItemEntity {
  const rarity = normalizeRarity(node.itemRarity);
  const type   = normalizeType(node.itemType, node.weaponSubtype);
  return {
    id:        node.id ?? node.title,
    title:     node.title,
    path:      node.path ?? null,
    epithet:   node.epithet ?? null,
    type,
    typeLabel: node.subtype ?? typeDisplayLabel(type),
    subtype:   node.subtype ?? null,
    rarity,
    rarityLabel: rarityDisplayLabel(rarity),
    requiresAttunement: !!node.itemRequiresAttunement,
    attunementRequirement: node.attunementRequirement ?? null,
    isMagic:   !!node.isMagic,
    homebrew:  !!node.homebrew,
    imageUrl:  node.image?.mediaImage?.url ?? null,
    imageAlt:  node.image?.mediaImage?.alt ?? null,
    bodyHtml:  node.body?.value ?? null,
    shortFlavour: node.shortFlavour ?? null,
    weight:    node.weight ?? null,
    value:     node.value  ?? null,
    school:    node.school ?? null,
    mechanics:  safeParseJson<ItemMechanic[]>(node.mechanicsJson, []),
    benefits:   node.benefits ?? [],
    tags:       node.tags     ?? [],
    provenance: safeParseJson<ItemProvenanceEntry[]>(node.provenanceJson, []),
    bearer:     node.bearer ? {
      name:     node.bearer.name,
      status:   node.bearer.status,
      charId:   node.bearer.charRef?.id   ?? null,
      charPath: node.bearer.charRef?.path ?? null,
    } : null,
    lastSeen:   node.lastSeen ?? null,
    related:    (node.related ?? []).map(r => ({ id: r.id, title: r.title, path: r.path })),
  };
}
