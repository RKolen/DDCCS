/**
 * EncounterSpotlightScreen — `monsters / m-encounter`
 *
 * Live DM combat dashboard: HP tracker, legendary action economy,
 * recharge toggle, lair action reminder, save DCs parsed from prose,
 * and active party threat panel.
 *
 * All state is local — encounter state is never persisted.
 * Design reference: /project/Encounter Spotlight.html
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import type { DrupalMonster } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

function crTierColor(cr: number | null): string {
  if (cr == null) return 'var(--ink-dim)';
  if (cr >= 17) return 'var(--color-danger)';
  if (cr >= 11) return 'var(--color-warning)';
  if (cr >= 5)  return 'var(--color-info)';
  return 'var(--color-success)';
}

/** Extract "DC NN Ability" prompts from all stat-block text. */
function extractSaveDCs(monster: DrupalMonster): Array<{ ability: string; dc: number }> {
  const texts = [
    ...monster.traits.map(a => a.desc),
    ...monster.actions.map(a => a.desc),
    ...(monster.legendaryActions?.actions.map(a => a.desc) ?? []),
    ...(monster.lairActions?.actions.map(a => a.desc) ?? []),
  ].join(' ');

  const re = /DC (\d+) (Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma|Str|Dex|Con|Int|Wis|Cha)/g;
  const found: Record<string, number> = {};
  let match;
  while ((match = re.exec(texts)) !== null) {
    const ab = match[2].slice(0, 3);
    const dc = parseInt(match[1], 10);
    if (!found[ab] || dc > found[ab]) found[ab] = dc;
  }
  return Object.entries(found).map(([ability, dc]) => ({ ability, dc }));
}

/** Find actions with "(Recharge N-N)" in the name. */
function extractRecharges(monster: DrupalMonster): Array<{ name: string; range: string; ready: boolean }> {
  return monster.actions
    .map(a => {
      const r = a.name.match(/\(Recharge ([^)]+)\)/);
      if (!r) return null;
      return { name: a.name.replace(/\s*\(Recharge[^)]*\)/, ''), range: `(Recharge ${r[1]})`, ready: true };
    })
    .filter((x): x is NonNullable<typeof x> => x !== null);
}

/* ────────────────────────────────────────────────────────────
   Picker (compact inline)
   ──────────────────────────────────────────────────────────── */

function MonsterSelect({
  monsters, selectedId, onSelect,
}: {
  monsters: DrupalMonster[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}): React.ReactElement {
  return (
    <select
      className="console-select"
      aria-label="Select monster"
      value={selectedId ?? ''}
      onChange={e => onSelect(e.target.value)}
    >
      {monsters.map(m => (
        <option key={m.id} value={m.id}>
          {m.title}{m.cr != null ? ` (CR ${m.cr})` : ''}
        </option>
      ))}
    </select>
  );
}

/* ────────────────────────────────────────────────────────────
   HP Tracker
   ──────────────────────────────────────────────────────────── */

function HpTracker({
  maxHp, hp, onHpChange,
}: {
  maxHp: number;
  hp: number;
  onHpChange: (next: number) => void;
}): React.ReactElement {
  const [delta, setDelta] = React.useState('');
  const pct   = Math.max(0, hp / maxHp);
  const color = pct > 0.5 ? 'var(--color-success)' : pct > 0.25 ? 'var(--color-warning)' : 'var(--color-danger)';

  const apply = (sign: 1 | -1): void => {
    const n = parseInt(delta, 10);
    if (!isNaN(n) && n > 0) {
      onHpChange(Math.max(0, Math.min(maxHp, hp + sign * n)));
      setDelta('');
    }
  };

  return (
    <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '16px 18px' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 10 }}>
        Hit Points
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 36, fontWeight: 700, color, lineHeight: 1 }}>{hp}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 16, color: 'var(--ink-faint)' }}>/ {maxHp}</span>
      </div>
      {/* HP bar */}
      <div style={{ height: 6, borderRadius: 3, background: 'var(--canvas)', border: '1px solid var(--rule)', overflow: 'hidden', marginBottom: 14 }}>
        <div style={{ width: `${pct * 100}%`, height: '100%', background: color, borderRadius: 3, transition: '300ms ease' }} />
      </div>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="number"
          min={1}
          value={delta}
          onChange={e => setDelta(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') apply(1); }}
          placeholder="Amount"
          style={{
            flex: 1, background: 'var(--canvas)', border: '1px solid var(--rule)',
            borderRadius: 4, color: 'var(--ink)', fontFamily: 'var(--font-mono)',
            fontSize: 14, padding: '6px 10px',
          }}
        />
        <button type="button" className="ghost-btn" onClick={() => apply(-1)} title="Deal damage">
          <Icon name="close" size={11} /> Damage
        </button>
        <button type="button" className="ghost-btn" onClick={() => apply(1)} title="Heal">
          <Icon name="plus" size={11} /> Heal
        </button>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Legendary action economy pips
   ──────────────────────────────────────────────────────────── */

function LegendaryTracker({
  available, spent, onToggle, onReset,
}: {
  available: number;
  spent: number;
  onToggle: (i: number) => void;
  onReset: () => void;
}): React.ReactElement {
  return (
    <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--gold-a15)', borderRadius: 10, padding: '14px 18px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
          Legendary Actions
        </span>
        <button type="button" style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--ink-dim)',
          letterSpacing: '0.1em', textTransform: 'uppercase', padding: 0,
        }} onClick={onReset}>
          Reset
        </button>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {Array.from({ length: available }, (_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onToggle(i)}
            title={i < spent ? 'Used' : 'Available'}
            style={{
              width: 36, height: 36, borderRadius: 9999,
              border: `2px solid var(--brass)`,
              background: i < spent ? 'var(--gold-a20)' : 'var(--brass)',
              cursor: 'pointer', transition: '120ms ease',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700,
              color: i < spent ? 'var(--brass-dim)' : 'var(--canvas)',
            }}>
              {i < spent ? '×' : '✓'}
            </span>
          </button>
        ))}
      </div>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', marginTop: 8 }}>
        {Math.max(0, available - spent)} of {available} remaining · resets at end of turn
      </p>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Recharge abilities
   ──────────────────────────────────────────────────────────── */

function RechargePanel({
  recharges, onToggle,
}: {
  recharges: Array<{ name: string; range: string; ready: boolean }>;
  onToggle: (i: number) => void;
}): React.ReactElement {
  return (
    <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '14px 18px' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 10 }}>
        Recharge Abilities
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {recharges.map((r, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              type="button"
              onClick={() => onToggle(i)}
              style={{
                width: 22, height: 22, borderRadius: 4, flexShrink: 0,
                border: `1px solid ${r.ready ? 'var(--color-success)' : 'var(--rule)'}`,
                background: r.ready ? 'var(--success-a10)' : 'transparent',
                cursor: 'pointer', transition: '120ms ease',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: r.ready ? 'var(--color-success)' : 'var(--ink-faint)', fontWeight: 700 }}>
                {r.ready ? '✓' : '×'}
              </span>
            </button>
            <div>
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: r.ready ? 'var(--ink)' : 'var(--ink-faint)' }}>{r.name}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', marginLeft: 6 }}>{r.range}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Save DC reference
   ──────────────────────────────────────────────────────────── */

function SaveDCPanel({ saveDCs }: { saveDCs: Array<{ ability: string; dc: number }> }): React.ReactElement {
  if (saveDCs.length === 0) return <></>;
  return (
    <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '14px 18px' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 10 }}>
        Saving Throw DCs
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {saveDCs.map(({ ability, dc }) => (
          <div key={ability} style={{
            background: 'var(--canvas)', border: '1px solid var(--rule)',
            borderRadius: 6, padding: '8px 10px', textAlign: 'center',
          }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 8, color: 'var(--brass-dim)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 3 }}>{ability}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--color-warning)' }}>{dc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Party threat panel
   ──────────────────────────────────────────────────────────── */

function PartyPanel({ campaign }: { campaign: string | null }): React.ReactElement {
  const data  = useConsoleData();
  const party = playerCharacters(data).filter(c =>
    campaign == null || c.campaign === campaign
  );

  if (party.length === 0) return <></>;

  return (
    <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '14px 18px' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 10 }}>
        Active Party
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {party.map(c => {
          const initials = c.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
          return (
            <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                background: 'var(--canvas)', border: '1px solid var(--rule)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                overflow: 'hidden',
              }}>
                {c.imageUrl
                  ? <img src={c.imageUrl} alt={c.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass)', fontWeight: 700 }}>{initials}</span>
                }
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--ink)', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {c.title}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink-dim)' }}>
                  {c.characterClass != null ? `${c.characterClass} ${c.level ?? ''}` : ''}
                </div>
              </div>
              {c.maximumHitpoints != null && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)', flexShrink: 0 }}>
                  {c.maximumHitpoints} HP
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Round tracker
   ──────────────────────────────────────────────────────────── */

function RoundTracker({ round, onNext }: { round: number; onNext: () => void }): React.ReactElement {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16,
      background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
      borderRadius: 10, padding: '12px 18px',
    }}>
      <div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 2 }}>Round</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 700, color: 'var(--brass-bright)', lineHeight: 1 }}>{round}</div>
      </div>
      <button type="button" className="primary-btn" onClick={onNext} style={{ marginLeft: 'auto' }}>
        <Icon name="chevron" size={11} /> Next Round
      </button>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function EncounterSpotlightScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data     = useConsoleData();
  const monsters = data.monsters;
  const idx      = (ctx.monsterIdx as number | undefined) ?? 0;
  const monster  = monsters[idx] ?? null;

  const [hp,            setHp]           = React.useState<number | null>(null);
  const [legendarySpent, setLegSpent]    = React.useState(0);
  const [recharges,     setRecharges]    = React.useState<Array<{ name: string; range: string; ready: boolean }>>([]);
  const [round,         setRound]        = React.useState(1);

  /* Reset combat state when monster changes */
  React.useEffect(() => {
    if (monster != null) {
      setHp(monster.maxHp ?? 0);
      setLegSpent(0);
      setRecharges(extractRecharges(monster));
      setRound(1);
    }
  }, [monster?.id]); /* eslint-disable-line react-hooks/exhaustive-deps */

  const saveDCs    = React.useMemo(() => monster ? extractSaveDCs(monster) : [], [monster]);
  const currentHp  = hp ?? (monster?.maxHp ?? 0);
  const maxHp      = monster?.maxHp ?? 0;
  const legCount   = monster?.legendaryActions?.available ?? 0;
  const isBoss     = monster?.profileType === 'major';
  const hasLair    = isBoss && (monster?.lairActions?.enabled ?? false);

  const nextRound = (): void => {
    setRound(r => r + 1);
    setLegSpent(0);
    setRecharges(prev => prev.map(r => r.ready ? r : { ...r, ready: true }));
  };

  const toggleLeg = (i: number): void => {
    setLegSpent(prev => i < prev ? i : Math.min(legCount, prev + 1));
  };

  const toggleRecharge = (i: number): void => {
    setRecharges(prev => prev.map((r, ri) => ri === i ? { ...r, ready: !r.ready } : r));
  };

  if (monsters.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Monsters · Encounter Spotlight</span>
            <h2>Encounter Spotlight</h2>
            <p className="screen-blurb">No monster nodes available from Drupal yet.</p>
          </div>
        </header>
      </div>
    );
  }

  const tierColor = crTierColor(monster?.cr ?? null);

  return (
    <div style={{ minHeight: '100%' }}>
      {/* Header */}
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Monsters · Encounter Spotlight</span>
          <h2 style={{ color: tierColor }}>
            {monster?.title ?? 'Select monster'}
          </h2>
          {monster != null && (
            <p className="screen-blurb">
              {[monster.size, monster.monsterType, monster.alignment].filter(Boolean).join(' · ')}
              {monster.cr != null ? ` · CR ${monster.cr}` : ''}
            </p>
          )}
        </div>
        <div className="screen-head-actions">
          <MonsterSelect
            monsters={monsters}
            selectedId={monster?.id ?? null}
            onSelect={id => {
              const i = monsters.findIndex(m => m.id === id);
              if (i !== -1) setCtx({ ...ctx, monsterIdx: i });
            }}
          />
        </div>
      </header>

      {monster != null && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
          {/* Left column — HP + legendary */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <RoundTracker round={round} onNext={nextRound} />

            {maxHp > 0 && (
              <HpTracker maxHp={maxHp} hp={currentHp} onHpChange={setHp} />
            )}

            {isBoss && legCount > 0 && (
              <LegendaryTracker
                available={legCount}
                spent={legendarySpent}
                onToggle={toggleLeg}
                onReset={() => setLegSpent(0)}
              />
            )}

            {recharges.length > 0 && (
              <RechargePanel recharges={recharges} onToggle={toggleRecharge} />
            )}

            {hasLair && monster.lairActions != null && (
              <div style={{
                background: 'color-mix(in srgb, var(--color-warning) 6%, transparent)',
                border: '1px solid color-mix(in srgb, var(--color-warning) 25%, transparent)',
                borderRadius: 10, padding: '12px 16px',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <Icon name="flag" size={14} style={{ color: 'var(--color-warning)', flexShrink: 0 }} />
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: 'var(--color-warning)', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 700 }}>
                    Lair Action — Initiative 20
                  </div>
                  {monster.lairActions.lairLocation != null && (
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', marginTop: 2 }}>
                      {monster.lairActions.lairLocation}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right column — DCs + party */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <SaveDCPanel saveDCs={saveDCs} />
            <PartyPanel campaign={monster.campaign} />

            {(monster.encounterTactics.length > 0 || monster.defeatConditions.length > 0) && (
              <div style={{ background: 'var(--canvas-raised)', border: '1px solid var(--rule)', borderRadius: 10, padding: '14px 18px' }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', marginBottom: 10 }}>
                  Tactics
                </div>
                {monster.encounterTactics.map((t, i) => (
                  <p key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5, marginBottom: 6 }}>{t}</p>
                ))}
                {monster.defeatConditions.length > 0 && (
                  <>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--brass-dim)', letterSpacing: '0.16em', textTransform: 'uppercase', margin: '10px 0 6px' }}>
                      Defeat
                    </div>
                    {monster.defeatConditions.map((d, i) => (
                      <p key={i} style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.5, marginBottom: 4 }}>{d}</p>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
