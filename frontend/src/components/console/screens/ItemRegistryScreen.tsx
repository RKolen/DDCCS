/**
 * ItemRegistryScreen — `items / i-list` and `items / i-validate`
 *
 * The Item Registry shows all items the party carries or has registered.
 * - Homebrew items (source = "homebrew" | "custom" | null) → stored in
 *   the custom registry; never looked up on the wiki.
 * - Official items (source = "official" | "srd") → resolved from the SRD
 *   wiki on demand; not in the registry.
 *
 * For homebrew items the screen runs a lightweight schema validation and
 * flags missing/malformed fields.
 *
 * Design reference: /project/Item Registry.html
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData } from '../ConsoleContext';
import type { DrupalItem } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Type → icon map
   ──────────────────────────────────────────────────────────── */

const ITEM_TYPE_ICON: Record<string, string> = {
  weapon: 'scroll',
  armor: 'npc',
  gear: 'tools',
  tool: 'tools',
  consumable: 'spell',
  magic_item: 'spell',
  treasure: 'star',
};

const ITEM_TYPE_ORDER = ['weapon', 'armor', 'magic_item', 'gear', 'tool', 'consumable', 'treasure'];

const ITEM_TYPE_LABEL: Record<string, string> = {
  weapon: 'Weapon',
  armor: 'Armor',
  gear: 'Gear',
  tool: 'Tool',
  consumable: 'Consumable',
  magic_item: 'Magic Item',
  treasure: 'Treasure',
};

/* ────────────────────────────────────────────────────────────
   Rarity colours
   ──────────────────────────────────────────────────────────── */

import { rarityColor } from '../../../utils/rarityColor';

/* ────────────────────────────────────────────────────────────
   Source classification helpers
   ──────────────────────────────────────────────────────────── */

/** Edition null or "Homebrew" = in the custom registry. Any named edition = official SRD. */
function isHomebrew(item: DrupalItem): boolean {
  const s = (item.source ?? '').toLowerCase();
  if (!s || s === 'homebrew') return true;
  /* Named editions like "D&D 5.5e (2024)", "D&D 5e (2014)" etc. are official */
  return false;
}

/* ────────────────────────────────────────────────────────────
   Validation engine (homebrew items only)
   ──────────────────────────────────────────────────────────── */

type Level = 'pass' | 'warn' | 'error';
interface Finding { level: Level; msg: string }
interface ValidationResult { status: Level; findings: Finding[] }

const DISALLOWED = new Set(['"', "'", '`', '$', '%', '&', '|', '<', '>', '/', '\\']);
const VALID_TYPES = new Set(['weapon', 'armor', 'gear', 'tool', 'consumable', 'magic_item', 'treasure']);

function validateItem(item: DrupalItem): ValidationResult {
  const findings: Finding[] = [];

  if (!item.title || item.title.trim() === '') {
    findings.push({ level: 'error', msg: 'Missing required field: name' });
  } else if ([...item.title].some(c => DISALLOWED.has(c))) {
    findings.push({ level: 'error', msg: `Name contains disallowed character(s)` });
  }

  if (!item.itemType) {
    findings.push({ level: 'error', msg: 'Missing required field: item_type' });
  } else if (!VALID_TYPES.has(item.itemType.toLowerCase())) {
    findings.push({ level: 'error', msg: `item_type "${item.itemType}" is not a valid type` });
  }

  if (item.isMagic == null) {
    findings.push({ level: 'warn', msg: 'is_magic not set — assumed false' });
  }

  if (!item.descriptionHtml || item.descriptionHtml.trim() === '') {
    findings.push({ level: 'warn', msg: 'description is empty — registry entries read thin without it' });
  }

  const counts: Record<Level, number> = { error: 0, warn: 0, pass: 0 };
  findings.forEach(f => { counts[f.level]++; });
  const status: Level = counts.error ? 'error' : counts.warn ? 'warn' : 'pass';
  return { status, findings };
}

/* ────────────────────────────────────────────────────────────
   StatusPip
   ──────────────────────────────────────────────────────────── */

const STATUS_GLYPH: Record<Level, string> = { pass: '✓', warn: '!', error: '✗' };
const STATUS_COLOR: Record<Level, string> = {
  pass: 'var(--color-success)',
  warn: 'var(--color-warning)',
  error: 'var(--color-danger)',
};

function StatusPip({ level, size = 20 }: { level: Level; size?: number }): React.ReactElement {
  const color = STATUS_COLOR[level];
  return (
    <span title={level} style={{
      width: size, height: size, borderRadius: 9999, flexShrink: 0,
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      background: `color-mix(in srgb, ${color} 16%, transparent)`,
      border: `1px solid ${color}`, color,
      fontFamily: 'var(--font-mono)', fontWeight: 700,
      fontSize: size * 0.52, lineHeight: 1,
    }}>
      {STATUS_GLYPH[level]}
    </span>
  );
}

/* ────────────────────────────────────────────────────────────
   ItemSigil — icon tile with rarity tint
   ──────────────────────────────────────────────────────────── */

function ItemSigil({ item, size = 46 }: { item: DrupalItem; size?: number }): React.ReactElement {
  const tint = rarityColor(item.itemRarity);
  const iconName = ITEM_TYPE_ICON[item.itemType?.toLowerCase() ?? ''] ?? 'tools';

  return (
    <div style={{
      width: size, height: size, borderRadius: 8, flexShrink: 0, overflow: 'hidden',
      background: `radial-gradient(circle at 50% 30%, color-mix(in srgb, ${tint} 18%, var(--color-bg-base)), var(--color-bg-base))`,
      border: `1px solid ${item.isMagic ? `color-mix(in srgb, ${tint} 60%, transparent)` : 'var(--color-gold-border)'}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      boxShadow: item.isMagic ? `0 0 10px color-mix(in srgb, ${tint} 28%, transparent)` : 'none',
    }}>
      {item.imageUrl
        ? <img src={item.imageUrl} alt={item.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        : <Icon name={iconName as 'spell'} size={size * 0.5} style={{ color: item.isMagic ? tint : 'var(--color-gold-mid)' }} />
      }
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Registry row (expandable)
   ──────────────────────────────────────────────────────────── */

function RegistryRow({
  item, val, expanded, onToggle, showValidation, compact,
}: {
  item: DrupalItem;
  val: ValidationResult;
  expanded: boolean;
  onToggle: () => void;
  showValidation: boolean;
  compact: boolean;
}): React.ReactElement {
  const homebrew = isHomebrew(item);
  const tint = rarityColor(item.itemRarity);
  const showVal = showValidation && homebrew;
  const typeLabel = ITEM_TYPE_LABEL[item.itemType?.toLowerCase() ?? ''] ?? item.itemType ?? '—';

  return (
    <div style={{
      background: 'var(--color-bg-surface)',
      border: `1px solid ${expanded ? 'var(--color-gold-muted)' : 'var(--color-gold-border)'}`,
      borderRadius: 8, overflow: 'hidden',
      borderLeft: `3px solid ${homebrew ? 'var(--color-rarity-very-rare)' : 'var(--color-info)'}`,
    }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          display: 'grid',
          gridTemplateColumns: `46px 1fr auto auto${showVal ? ' 24px' : ''}`,
          gap: 14, alignItems: 'center',
          width: '100%', background: 'none', border: 'none', cursor: 'pointer',
          padding: compact ? '10px 16px' : '13px 18px', textAlign: 'left',
        }}
      >
        <ItemSigil item={item} size={46} />

        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 9, flexWrap: 'wrap', marginBottom: 3 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: compact ? 14 : 16, color: 'var(--color-gold-bright)', fontWeight: 600 }}>
              {item.title}
            </span>
            {item.nonidentifiedName != null && item.nonidentifiedName !== '' && (
              <span style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--color-text-secondary)' }}>
                &ldquo;{item.nonidentifiedName}&rdquo;
              </span>
            )}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-text-secondary)', display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
            <span>{typeLabel}</span>
            {item.itemRarity != null && (
              <>
                <span style={{ color: 'var(--color-text-disabled)' }}>·</span>
                <span style={{ color: tint, textTransform: 'capitalize' }}>{item.itemRarity}</span>
              </>
            )}
            <span style={{ color: 'var(--color-text-disabled)' }}>·</span>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              color: homebrew ? 'var(--color-rarity-very-rare)' : 'var(--color-info-text)',
            }}>
              {homebrew ? 'custom registry' : 'wiki lookup'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          {item.isMagic ? (
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
              letterSpacing: '0.12em', textTransform: 'uppercase', padding: '2px 8px',
              borderRadius: 4, border: '1px solid var(--color-gold-border)',
              color: 'var(--color-gold-bright)', background: 'var(--gold-a05)',
            }}>Magic</span>
          ) : (
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
              letterSpacing: '0.12em', textTransform: 'uppercase', padding: '2px 8px',
              borderRadius: 4, border: '1px solid var(--color-gold-border)',
              color: 'var(--color-text-secondary)',
            }}>Mundane</span>
          )}
        </div>

        {/* Source badge */}
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
          letterSpacing: '0.1em', textTransform: 'uppercase', padding: '3px 8px',
          borderRadius: 4,
          border: `1px solid ${homebrew ? 'color-mix(in srgb, var(--color-rarity-very-rare) 20%, transparent)' : 'color-mix(in srgb, var(--color-info) 20%, transparent)'}`,
          color: homebrew ? 'var(--color-rarity-very-rare)' : 'var(--color-info-text)',
          background: homebrew ? 'color-mix(in srgb, var(--color-rarity-very-rare) 4%, transparent)' : 'color-mix(in srgb, var(--color-info) 4%, transparent)',
          whiteSpace: 'nowrap',
        }}>
          {homebrew ? 'Homebrew' : 'Official'}
        </span>

        {showVal && <StatusPip level={val.status} size={22} />}
      </button>

      {expanded && (
        <div style={{
          padding: compact ? '4px 18px 16px' : '6px 20px 20px',
          borderTop: '1px solid var(--color-gold-border)',
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 24, marginTop: 14 }}>

            {/* Left — description */}
            <div>
              {item.descriptionHtml != null && item.descriptionHtml !== '' && (
                <div style={{
                  marginBottom: 12, padding: '10px 14px',
                  background: 'var(--color-bg-overlay)',
                  border: '1px solid var(--color-gold-border)', borderRadius: 6,
                }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--color-gold-mid)', letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4 }}>
                    Description
                  </div>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--color-text-primary)', lineHeight: 1.55 }}
                    dangerouslySetInnerHTML={{ __html: item.descriptionHtml }} />
                </div>
              )}

              {/* Quick stats */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {item.damage != null && (
                  <span style={statChip()}>Damage: {item.damage}</span>
                )}
                {item.armorAcBase != null && (
                  <span style={statChip()}>AC: {item.armorAcBase}{item.armorCategory != null ? ` (${item.armorCategory})` : ''}</span>
                )}
                {item.itemBonus != null && (
                  <span style={statChip()}>+{item.itemBonus} bonus</span>
                )}
                {item.armorStrRequirement != null && (
                  <span style={statChip()}>STR {item.armorStrRequirement} req</span>
                )}
                {item.itemCost != null && (
                  <span style={statChip()}>{item.itemCost}</span>
                )}
                {item.itemWeight != null && (
                  <span style={statChip()}>{item.itemWeight} lb</span>
                )}
                {item.itemRequiresAttunement && (
                  <span style={{ ...statChip(), color: 'var(--color-warning)', borderColor: 'color-mix(in srgb, var(--color-warning) 30%, transparent)' }}>Attunement</span>
                )}
              </div>

              {/* Links */}
              <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
                {item.path != null && item.path !== '' && (
                  <a href={item.path} style={ghostLink()}>
                    <Icon name="scroll" size={12} /> Open item
                  </a>
                )}
                <span style={{ ...ghostLink(), cursor: 'default' }}>
                  {homebrew
                    ? <><Icon name="tools" size={12} /> Custom registry</>
                    : <><Icon name="read" size={12} /> Wiki lookup</>
                  }
                </span>
              </div>
            </div>

            {/* Right — validation (homebrew) or wiki note (official) */}
            <div>
              {showVal && (
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: 'var(--color-gold-mid)', letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Icon name="npc" size={12} style={{ color: 'var(--color-gold-muted)' }} /> Registry validation
                  </div>
                  {val.findings.length === 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-success)' }}>
                      <StatusPip level="pass" size={16} /> Schema valid — all required fields present.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {val.findings.map((f, i) => (
                        <div key={i} style={{ display: 'grid', gridTemplateColumns: '16px 1fr', gap: 9, alignItems: 'start' }}>
                          <StatusPip level={f.level} size={16} />
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-primary)', lineHeight: 1.45 }}>{f.msg}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {!homebrew && (
                <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                  Official items are not validated by the registry — the SRD wiki is their source of truth.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function statChip(): React.CSSProperties {
  return {
    fontFamily: 'var(--font-mono)', fontSize: 11,
    color: 'var(--color-text-secondary)',
    background: 'var(--color-bg-overlay)',
    border: '1px solid var(--color-gold-border)',
    borderRadius: 4, padding: '3px 8px',
  };
}

function ghostLink(): React.CSSProperties {
  return {
    display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none',
    padding: '7px 12px', borderRadius: 4, background: 'var(--color-bg-overlay)',
    border: '1px solid var(--color-gold-border)',
    fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--color-gold-mid)',
    letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 700,
  };
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function ItemRegistryScreen(_props: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const items = data.items;

  const [sourceFilter, setSource] = React.useState<'all' | 'homebrew' | 'official'>('all');
  const [typeFilter, setType] = React.useState<string | null>(null);
  const [magicOnly, setMagicOnly] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [showVal, setShowVal] = React.useState(true);
  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});

  /* Pre-validate once */
  const validated = React.useMemo(() =>
    items.map(it => ({ it, val: validateItem(it) })),
    [items]);

  /* Summary counts */
  const summary = React.useMemo(() => {
    const homebrew = validated.filter(v => isHomebrew(v.it)).length;
    const official = validated.filter(v => !isHomebrew(v.it)).length;
    const magic = items.filter(i => i.isMagic).length;
    const flagged = validated.filter(v => isHomebrew(v.it) && v.val.status !== 'pass').length;
    return { homebrew, official, magic, flagged };
  }, [validated, items]);

  /* Present item types */
  const presentTypes = React.useMemo(() => {
    const s = new Set(items.map(i => (i.itemType ?? '').toLowerCase()));
    return ITEM_TYPE_ORDER.filter(t => s.has(t));
  }, [items]);

  /* Filtered list */
  const visible = React.useMemo(() => validated.filter(({ it }) => {
    if (sourceFilter === 'homebrew' && !isHomebrew(it)) return false;
    if (sourceFilter === 'official' && isHomebrew(it)) return false;
    if (typeFilter != null && it.itemType?.toLowerCase() !== typeFilter) return false;
    if (magicOnly && !it.isMagic) return false;
    if (query) {
      const q = query.toLowerCase();
      if (!it.title.toLowerCase().includes(q) && !(it.descriptionHtml ?? '').toLowerCase().includes(q)) return false;
    }
    return true;
  }), [validated, sourceFilter, typeFilter, magicOnly, query]);

  const toggle = (id: string): void => setExpanded(p => ({ ...p, [id]: !p[id] }));
  const setAll = (v: boolean): void => {
    const n: Record<string, boolean> = {};
    visible.forEach(x => { n[x.it.id] = v; });
    setExpanded(n);
  };

  const segStyle = (active: boolean): React.CSSProperties => ({
    fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
    padding: '5px 12px', borderRadius: 4, border: 'none', cursor: 'pointer',
    background: active ? 'var(--canvas-raised)' : 'transparent',
    color: active ? 'var(--brass-bright)' : 'var(--ink-dim)',
    transition: '120ms ease',
  });

  const chipStyle = (active: boolean, color = 'var(--color-gold-mid)'): React.CSSProperties => ({
    fontFamily: 'var(--font-display)', fontSize: 9, fontWeight: 700, letterSpacing: '0.1em',
    textTransform: 'uppercase' as const, padding: '4px 10px', borderRadius: 4,
    border: `1px solid ${active ? color : 'var(--color-gold-border)'}`,
    background: active ? `color-mix(in srgb, ${color} 10%, transparent)` : 'transparent',
    color: active ? color : 'var(--color-text-secondary)',
    cursor: 'pointer', transition: '120ms ease',
  });

  const linkBtnStyle: React.CSSProperties = {
    background: 'none', border: 'none', cursor: 'pointer',
    fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--color-text-secondary)',
    letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 700, padding: 0,
  };

  if (items.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Items · Registry</span>
            <h2>Item Registry</h2>
            <p className="screen-blurb">No item nodes available from Drupal yet.</p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100%' }}>

      {/* Header */}
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Items · Registry</span>
          <h2>The Item Registry</h2>
        </div>
        <div className="screen-head-actions">
          <button
            type="button"
            className="ghost-btn"
            onClick={() => setShowVal(v => !v)}
          >
            {showVal ? 'Hide validation' : 'Show validation'}
          </button>
        </div>
      </header>

      {/* Summary tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'In Registry', value: summary.homebrew, color: 'var(--color-rarity-very-rare)', sub: 'homebrew · no wiki lookup', src: 'homebrew' as const },
          { label: 'Official', value: summary.official, color: 'var(--color-info)', sub: 'resolved via wiki', src: 'official' as const },
          { label: 'Magic Items', value: summary.magic, color: 'var(--color-gold-bright)', sub: 'is_magic = true', src: 'magic' as const },
          { label: 'Needs Attention', value: summary.flagged, color: summary.flagged ? 'var(--color-warning)' : 'var(--color-success)', sub: 'registry validation', src: 'flagged' as const },
        ].map(s => {
          const isActive = s.src === sourceFilter || (s.src === 'magic' && magicOnly);
          return (
            <button
              key={s.label}
              type="button"
              onClick={() => {
                if (s.src === 'homebrew' || s.src === 'official') setSource(sourceFilter === s.src ? 'all' : s.src);
                else if (s.src === 'magic') setMagicOnly(v => !v);
              }}
              style={{
                background: 'var(--canvas-raised)',
                border: `1px solid ${isActive ? s.color : 'var(--rule)'}`,
                borderRadius: 10, padding: '14px 16px', textAlign: 'left',
                cursor: s.src === 'flagged' ? 'default' : 'pointer',
                boxShadow: isActive ? `0 0 0 1px ${s.color}` : 'none',
                transition: '120ms ease',
              }}
            >
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--ink-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4 }}>
                {s.label}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 28, color: s.color, fontWeight: 700, lineHeight: 1.1 }}>{s.value}</div>
              <div style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 11, color: 'var(--ink-dim)', marginTop: 2 }}>{s.sub}</div>
            </button>
          );
        })}
      </div>

      {/* Filter bar */}
      <div style={{
        display: 'flex', flexDirection: 'column', gap: 10,
        marginBottom: 18, paddingBottom: 16, borderBottom: '1px solid var(--rule)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {/* Source toggle */}
          <div style={{ display: 'flex', gap: 2, background: 'var(--overlay-30)', padding: 3, borderRadius: 6, border: '1px solid var(--rule)' }}>
            {(['all', 'homebrew', 'official'] as const).map(v => (
              <button key={v} type="button" onClick={() => setSource(v)} style={segStyle(sourceFilter === v)}>
                {v === 'all' ? 'All' : v === 'homebrew' ? 'Homebrew' : 'Official'}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="search-field" style={{ flex: 1, minWidth: 200, maxWidth: 320 }}>
            <Icon name="search" size={13} />
            <input
              type="text"
              placeholder="Search items…"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
          </div>

          {/* Magic only chip */}
          <button
            type="button"
            onClick={() => setMagicOnly(v => !v)}
            style={chipStyle(magicOnly, 'var(--color-gold-bright)')}
          >
            Magic only
          </button>
        </div>

        {/* Type filters + expand/collapse */}
        {presentTypes.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink-dim)', textTransform: 'uppercase', letterSpacing: '0.12em', marginRight: 4 }}>Type</span>
            <button type="button" onClick={() => setType(null)} style={chipStyle(typeFilter === null)}>All</button>
            {presentTypes.map(tp => (
              <button
                key={tp}
                type="button"
                onClick={() => setType(typeFilter === tp ? null : tp)}
                style={chipStyle(typeFilter === tp)}
              >
                {ITEM_TYPE_LABEL[tp] ?? tp}
              </button>
            ))}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="muted mono" style={{ fontSize: 10 }}>{visible.length} of {items.length}</span>
              <button type="button" style={linkBtnStyle} onClick={() => setAll(true)}>Expand all</button>
              <span style={{ color: 'var(--ink-faint)' }}>·</span>
              <button type="button" style={linkBtnStyle} onClick={() => setAll(false)}>Collapse all</button>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {visible.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px 20px', border: '1px dashed var(--rule)', borderRadius: 8 }}>
          <p className="screen-blurb" style={{ textAlign: 'center' }}>No items match this filter.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {visible.map(({ it, val }) => (
            <RegistryRow
              key={it.id}
              item={it}
              val={val}
              expanded={!!expanded[it.id]}
              onToggle={() => toggle(it.id)}
              showValidation={showVal}
              compact={false}
            />
          ))}
        </div>
      )}
    </div>
  );
}
