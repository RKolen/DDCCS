/**
 * MonsterStatBlockScreen — `monsters / m-view`
 *
 * Full 5e stat block: combat header, ability grid, traits, actions,
 * and the legendary / lair / regional boss mechanics.
 *
 * Design reference: /project/Monster Stat Block.html
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData } from '../ConsoleContext';
import type { DrupalMonster, MonsterAction } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

const ABILITIES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'] as const;

function mod(score: number): number { return Math.floor((score - 10) / 2); }
function fmtMod(m: number): string  { return m >= 0 ? `+${m}` : `${m}`; }

function crTierColor(cr: number | null): string {
  if (cr == null) return 'var(--ink-dim)';
  if (cr >= 17) return 'var(--color-danger)';
  if (cr >= 11) return 'var(--color-warning)';
  if (cr >= 5)  return 'var(--color-info)';
  return 'var(--color-success)';
}

/* ────────────────────────────────────────────────────────────
   Picker
   ──────────────────────────────────────────────────────────── */

function MonsterPicker({
  monsters, selectedId, onSelect,
}: {
  monsters: DrupalMonster[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}): React.ReactElement {
  return (
    <aside className="char-picker">
      <ul className="char-picker-list">
        {monsters.map(m => {
          const initials = m.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
          const color    = crTierColor(m.cr);
          return (
            <li key={m.id}>
              <button
                type="button"
                className={`char-picker-item${m.id === selectedId ? ' active' : ''}`}
                onClick={() => onSelect(m.id)}
                style={{ borderLeftColor: m.id === selectedId ? color : 'transparent' }}
              >
                <span className="char-pip" style={{ fontSize: 10, color: 'var(--brass)' }}>
                  {m.imageUrl
                    ? <img src={m.imageUrl} alt={m.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                    : initials
                  }
                </span>
                <span className="char-pip-meta">
                  <span className="char-pip-name">{m.title}</span>
                  <span className="char-pip-class" style={{ color }}>
                    {m.monsterType ?? ''}
                    {m.cr != null ? ` · CR ${m.cr}` : ''}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

/* ────────────────────────────────────────────────────────────
   Stat block sub-components
   ──────────────────────────────────────────────────────────── */

function SectionHead({ title, color = 'var(--brass)' }: { title: string; color?: string }): React.ReactElement {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      paddingBottom: 8, marginBottom: 12,
      borderBottom: `2px solid color-mix(in srgb, ${color} 30%, transparent)`,
    }}>
      <span style={{ flex: 1, height: 1, background: `color-mix(in srgb, ${color} 20%, transparent)` }} />
      <span style={{ fontFamily: 'var(--font-display)', fontSize: 9, color, letterSpacing: '0.2em', textTransform: 'uppercase', fontWeight: 700, flexShrink: 0 }}>
        {title}
      </span>
      <span style={{ flex: 1, height: 1, background: `color-mix(in srgb, ${color} 20%, transparent)` }} />
    </div>
  );
}

function AbilityGrid({ scores }: { scores: Record<string, number> }): React.ReactElement {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 8, margin: '16px 0' }}>
      {ABILITIES.map(ab => {
        const score = scores[ab] ?? 10;
        const m     = mod(score);
        return (
          <div key={ab} style={{
            background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
            borderRadius: 6, padding: '8px 4px', textAlign: 'center',
          }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 4 }}>{ab}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--ink)', lineHeight: 1 }}>{score}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--brass)', marginTop: 2 }}>{fmtMod(m)}</div>
          </div>
        );
      })}
    </div>
  );
}

function ActionList({ actions, accent }: { actions: MonsterAction[]; accent?: string }): React.ReactElement {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {actions.map((a, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '8px 1fr', gap: 10, alignItems: 'start' }}>
          <div style={{ width: 8, height: 8, borderRadius: 9999, background: accent ?? 'var(--brass)', marginTop: 6, flexShrink: 0 }} />
          <div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--ink)', letterSpacing: '0.04em' }}>
              {a.name}
              {a.cost != null && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: accent ?? 'var(--brass)', marginLeft: 6 }}>
                  ({a.cost} {a.cost === 1 ? 'action' : 'actions'})
                </span>
              )}
              {'. '}
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--ink-dim)', lineHeight: 1.5 }}>{a.desc}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function PropRow({ label, value }: { label: string; value: string }): React.ReactElement {
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 700, color: 'var(--brass)', flexShrink: 0 }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--ink-dim)' }}>{value}</span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Full stat block
   ──────────────────────────────────────────────────────────── */

function StatBlock({ monster }: { monster: DrupalMonster }): React.ReactElement {
  const tierColor = crTierColor(monster.cr);
  const isBoss    = monster.profileType === 'major';
  const hasLeg    = isBoss && monster.legendaryActions != null && (monster.legendaryActions.available) > 0;
  const hasLair   = isBoss && monster.lairActions != null && monster.lairActions.enabled;
  const hasReg    = isBoss && monster.regionalEffects != null && monster.regionalEffects.enabled;

  const saves   = monster.saves ?? {};
  const saveStr = Object.entries(saves).map(([k, v]) => `${k} ${v}`).join(', ');
  const skills  = monster.skills ?? {};
  const skillStr = Object.entries(skills).map(([k, v]) => `${k} ${v}`).join(', ');

  return (
    <div>
      {/* Identity band */}
      <div style={{
        background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
        borderTop: `3px solid ${tierColor}`, borderRadius: 10, padding: '16px 20px', marginBottom: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 24, color: 'var(--brass-bright)', fontWeight: 700, letterSpacing: '0.04em', margin: 0 }}>
              {monster.title}
            </h2>
            {monster.nickname != null && (
              <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 14, color: 'var(--ink-dim)', margin: '2px 0 6px' }}>
                &ldquo;{monster.nickname}&rdquo;
              </p>
            )}
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', margin: 0 }}>
              {[monster.size, monster.monsterType, monster.alignment].filter(Boolean).join(' · ')}
            </p>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 28, fontWeight: 700, color: tierColor, lineHeight: 1 }}>
              {monster.cr ?? '?'}
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 8, color: tierColor, letterSpacing: '0.14em', textTransform: 'uppercase' }}>Challenge</div>
          </div>
        </div>
        {monster.tagline != null && (
          <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 14, color: 'var(--ink-dim)', marginTop: 10, lineHeight: 1.5, borderTop: '1px solid var(--rule)', paddingTop: 10 }}>
            {monster.tagline}
          </p>
        )}
      </div>

      {/* Combat stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
        {[
          { label: 'Hit Points', value: `${monster.hp ?? '—'} / ${monster.maxHp ?? '—'}`, sub: monster.hitDice ?? '' },
          { label: 'Armor Class', value: monster.ac?.toString() ?? '—', sub: monster.acNote ?? '' },
          { label: 'Speed', value: monster.speed ?? '—', sub: '' },
          { label: 'Prof Bonus', value: monster.profBonus != null ? `+${monster.profBonus}` : '—', sub: '' },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 8, padding: '10px 14px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 8, color: 'var(--brass-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--ink)' }}>{s.value}</div>
            {s.sub && <div style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--ink-faint)', marginTop: 2 }}>{s.sub}</div>}
          </div>
        ))}
      </div>

      {/* Ability scores */}
      {monster.scores != null && <AbilityGrid scores={monster.scores} />}

      <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '16px 20px', marginBottom: 16 }}>
        {saveStr && <PropRow label="Saving Throws" value={saveStr} />}
        {skillStr && <PropRow label="Skills" value={skillStr} />}
        {monster.resistances.length > 0 && <PropRow label="Resistances" value={monster.resistances.join(', ')} />}
        {monster.immunities.length > 0 && <PropRow label="Immunities" value={monster.immunities.join(', ')} />}
        {monster.conditionImmunities.length > 0 && <PropRow label="Condition Immunities" value={monster.conditionImmunities.join(', ')} />}
        {monster.senses.length > 0 && <PropRow label="Senses" value={monster.senses.join(', ')} />}
        {monster.languages.length > 0 && <PropRow label="Languages" value={monster.languages.join(', ')} />}
      </div>

      {/* Traits */}
      {monster.traits.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <SectionHead title="Traits" />
          <ActionList actions={monster.traits} />
        </div>
      )}

      {/* Actions */}
      {monster.actions.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <SectionHead title="Actions" />
          <ActionList actions={monster.actions} />
        </div>
      )}

      {/* Legendary Actions */}
      {hasLeg && monster.legendaryActions != null && (
        <div style={{
          background: 'color-mix(in srgb, var(--brass) 6%, transparent)',
          border: '1px solid var(--gold-a15)', borderRadius: 10,
          padding: '14px 18px', marginBottom: 12,
        }}>
          <SectionHead title={`Legendary Actions (${monster.legendaryActions.available}/round)`} color="var(--brass)" />
          <ActionList actions={monster.legendaryActions.actions} accent="var(--brass)" />
        </div>
      )}

      {/* Lair Actions */}
      {hasLair && monster.lairActions != null && (
        <div style={{
          background: 'color-mix(in srgb, var(--color-warning) 5%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-warning) 25%, transparent)',
          borderRadius: 10, padding: '14px 18px', marginBottom: 12,
        }}>
          <SectionHead title={`Lair Actions${monster.lairActions.lairLocation != null ? ` · ${monster.lairActions.lairLocation}` : ''}`} color="var(--color-warning)" />
          <ActionList actions={monster.lairActions.actions} accent="var(--color-warning)" />
        </div>
      )}

      {/* Regional Effects */}
      {hasReg && monster.regionalEffects != null && (
        <div style={{
          background: 'color-mix(in srgb, var(--color-info) 5%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-info) 25%, transparent)',
          borderRadius: 10, padding: '14px 18px', marginBottom: 12,
        }}>
          <SectionHead title={`Regional Effects${monster.regionalEffects.radius != null ? ` · ${monster.regionalEffects.radius}` : ''}`} color="var(--color-info)" />
          <ActionList actions={monster.regionalEffects.effects} accent="var(--color-info)" />
        </div>
      )}

      {/* DM flavor */}
      {(monster.encounterTactics.length > 0 || monster.plotHooks.length > 0 || monster.defeatConditions.length > 0) && (
        <div style={{
          background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
          borderRadius: 10, padding: '14px 18px', marginTop: 16,
        }}>
          <SectionHead title="DM Notes" color="var(--brass-dim)" />
          {monster.encounterTactics.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>Encounter Tactics</div>
              {monster.encounterTactics.map((t, i) => (
                <p key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', marginBottom: 4, lineHeight: 1.5 }}>{t}</p>
              ))}
            </div>
          )}
          {monster.plotHooks.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>Plot Hooks</div>
              {monster.plotHooks.map((h, i) => (
                <p key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', marginBottom: 4, lineHeight: 1.5 }}>{h}</p>
              ))}
            </div>
          )}
          {monster.defeatConditions.length > 0 && (
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>Defeat Conditions</div>
              {monster.defeatConditions.map((d, i) => (
                <p key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', marginBottom: 4, lineHeight: 1.5 }}>{d}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function MonsterStatBlockScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data     = useConsoleData();
  const monsters = data.monsters;
  const idx      = (ctx.monsterIdx as number | undefined) ?? 0;
  const monster  = monsters[idx] ?? null;

  if (monsters.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Monsters · Stat Block</span>
            <h2>Monster Stat Block</h2>
            <p className="screen-blurb">No monster nodes available from Drupal yet.</p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-chardetails">
      <MonsterPicker
        monsters={monsters}
        selectedId={monster?.id ?? null}
        onSelect={id => {
          const i = monsters.findIndex(m => m.id === id);
          if (i !== -1) setCtx({ ...ctx, monsterIdx: i });
        }}
      />
      {monster != null && (
        <div className="char-sheet-detail" style={{ flex: 1, overflowY: 'auto', padding: '20px 28px 40px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <span className="reader-eyebrow">Monsters · Stat Block</span>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => setCtx({ ...ctx, _itemId: 'm-encounter' })}
            >
              <Icon name="play" size={11} /> Launch Encounter
            </button>
          </div>
          <StatBlock key={monster.id} monster={monster} />
        </div>
      )}
    </div>
  );
}
