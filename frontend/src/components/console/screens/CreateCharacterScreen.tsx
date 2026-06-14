/**
 * CreateCharacterScreen — `characters / template`
 *
 * A simplified, derive-not-ask character creation wizard. The user supplies
 * only what cannot be computed (identity, class, level, ability scores, skill
 * picks, optional roleplay). Hit points, proficiency, saves, class features
 * and spell slots are derived server-side by the Python sidecar and shown
 * read-only on the Review step.
 *
 * On create, a source character is persisted (field_source_character = true)
 * via the createCharacter GraphQL mutation, and — when a campaign is active —
 * a campaign clone is attached via addCharacterToCampaign. All writes go
 * through /api/create-character.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData } from '../ConsoleContext';

const CLASS_OPTIONS = [
  'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter', 'Monk',
  'Paladin', 'Ranger', 'Rogue', 'Sorcerer', 'Warlock', 'Wizard',
] as const;

const SKILL_OPTIONS = [
  'Acrobatics', 'Animal Handling', 'Arcana', 'Athletics', 'Deception',
  'History', 'Insight', 'Intimidation', 'Investigation', 'Medicine',
  'Nature', 'Perception', 'Performance', 'Persuasion', 'Religion',
  'Sleight of Hand', 'Stealth', 'Survival',
] as const;

const ABILITIES = [
  ['strength', 'Strength'],
  ['dexterity', 'Dexterity'],
  ['constitution', 'Constitution'],
  ['intelligence', 'Intelligence'],
  ['wisdom', 'Wisdom'],
  ['charisma', 'Charisma'],
] as const;

type AbilityKey = (typeof ABILITIES)[number][0];

const STEPS = ['Identity', 'Class & Level', 'Ability Scores', 'Skills', 'Roleplay', 'Review'] as const;

interface AbilityScores {
  strength:     number;
  dexterity:    number;
  constitution: number;
  intelligence: number;
  wisdom:       number;
  charisma:     number;
}

interface FormState {
  name:          string;
  className:     string;
  level:         number;
  abilityScores: AbilityScores;
  species:       string;
  background:    string;
  subclass:      string;
  skills:        string[];
  backstory:     string;
  traits:        string;
  ideals:        string;
  bonds:         string;
  flaws:         string;
}

interface DerivedPreview {
  max_hit_points:    number;
  proficiency_bonus: number;
  class_abilities:   string[];
  spell_slots:       Record<string, number>;
  skills:            Record<string, unknown>;
}

interface CreateResult {
  sourceId: string;
  title:    string;
  attached: boolean;
  warning?: string;
}

const DEFAULT_FORM: FormState = {
  name:          '',
  className:     'Fighter',
  level:         1,
  abilityScores: { strength: 10, dexterity: 10, constitution: 10, intelligence: 10, wisdom: 10, charisma: 10 },
  species:       'Human',
  background:    '',
  subclass:      '',
  skills:        [],
  backstory:     '',
  traits:        '',
  ideals:        '',
  bonds:         '',
  flaws:         '',
};

function modifier(score: number): string {
  const mod = Math.floor((score - 10) / 2);
  return mod >= 0 ? `+${mod}` : `${mod}`;
}

function splitLines(value: string): string[] {
  return value.split('\n').map(s => s.trim()).filter(Boolean);
}

export function CreateCharacterScreen({ ctx }: ScreenProps): React.ReactElement {
  const { campaigns } = useConsoleData();
  const activeCampaign =
    campaigns.find(c => c.name === ctx.activeCampaignName) ?? campaigns[0] ?? null;

  const [step,       setStep]       = React.useState(0);
  const [form,       setForm]       = React.useState<FormState>(DEFAULT_FORM);
  const [preview,    setPreview]    = React.useState<DerivedPreview | null>(null);
  const [loading,    setLoading]    = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error,      setError]      = React.useState<string | null>(null);
  const [result,     setResult]     = React.useState<CreateResult | null>(null);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const setAbility = (key: AbilityKey, value: number): void => {
    setForm(prev => ({ ...prev, abilityScores: { ...prev.abilityScores, [key]: value } }));
  };

  const toggleSkill = (skill: string): void => {
    setForm(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill],
    }));
  };

  const requestBody = React.useCallback((dryRun: boolean) => ({
    name:              form.name.trim(),
    className:         form.className,
    level:             form.level,
    abilityScores:     form.abilityScores,
    skills:            form.skills,
    background:        form.background.trim(),
    species:           form.species.trim(),
    subclass:          form.subclass.trim() || null,
    backstory:         form.backstory.trim(),
    personalityTraits: splitLines(form.traits),
    ideals:            splitLines(form.ideals),
    bonds:             splitLines(form.bonds),
    flaws:             splitLines(form.flaws),
    campaignId:        dryRun ? null : (activeCampaign?.id ?? null),
    dryRun,
  }), [form, activeCampaign]);

  const loadPreview = React.useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/create-character', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(requestBody(true)),
      });
      const data = (await res.json()) as { character?: DerivedPreview; error?: string };
      if (!res.ok || !data.character) {
        setError(data.error ?? `Preview failed (${res.status})`);
        return;
      }
      setPreview(data.character);
    } catch {
      setError('Could not reach the server for a preview.');
    } finally {
      setLoading(false);
    }
  }, [requestBody]);

  const goNext = (): void => {
    const next = step + 1;
    setStep(next);
    if (STEPS[next] === 'Review') void loadPreview();
  };

  const handleCreate = async (): Promise<void> => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch('/api/create-character', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(requestBody(false)),
      });
      const data = (await res.json()) as CreateResult & { error?: string };
      if (!res.ok && res.status !== 207) {
        setError(data.error ?? `Creation failed (${res.status})`);
        return;
      }
      setResult(data);
    } catch {
      setError('Could not reach the server.');
    } finally {
      setSubmitting(false);
    }
  };

  const canContinue = step !== 0 || form.name.trim().length > 0;

  if (result) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Characters</span>
            <h2>Character Created</h2>
            <p className="screen-blurb">
              <strong>{result.title}</strong> was created as a source character.
              {result.attached
                ? ` A copy was added to ${activeCampaign?.name ?? 'the active campaign'}.`
                : ' No active campaign — create or select one to add a copy to a party.'}
            </p>
            {result.warning && <p className="modal-error" role="alert">{result.warning}</p>}
          </div>
          <div className="screen-head-actions">
            <button
              type="button"
              className="primary-btn"
              onClick={() => { setResult(null); setPreview(null); setForm(DEFAULT_FORM); setStep(0); }}
            >
              Create another
            </button>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Characters</span>
          <h2>Create Character from Template</h2>
          <p className="screen-blurb">
            Step {step + 1} of {STEPS.length} — {STEPS[step]}.
            {activeCampaign
              ? ` Will be added to ${activeCampaign.name}.`
              : ' No active campaign — the character will be created as a source only.'}
          </p>
        </div>
      </header>

      <ol className="wizard-steps" style={{ display: 'flex', gap: 8, listStyle: 'none', padding: 0, margin: '16px 0', flexWrap: 'wrap' }}>
        {STEPS.map((label, i) => (
          <li
            key={label}
            style={{
              fontFamily: 'var(--font-mono)', fontSize: 11, padding: '4px 10px', borderRadius: 12,
              border: '1px solid var(--rule)',
              color: i === step ? 'var(--color-on-danger)' : 'var(--ink-dim)',
              background: i === step ? 'var(--color-partial)' : 'transparent',
            }}
          >
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      <div className="wizard-body" style={{ marginTop: 8 }}>
        {STEPS[step] === 'Identity' && (
          <>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-name">Name</label>
              <input id="cc-name" className="modal-input" value={form.name} autoFocus
                onChange={e => update('name', e.target.value)} placeholder="Character name" />
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-species">Species</label>
              <input id="cc-species" className="modal-input" value={form.species}
                onChange={e => update('species', e.target.value)} placeholder="e.g. Human, Elf" />
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-bg">Background</label>
              <input id="cc-bg" className="modal-input" value={form.background}
                onChange={e => update('background', e.target.value)} placeholder="e.g. Soldier, Sage" />
            </div>
          </>
        )}

        {STEPS[step] === 'Class & Level' && (
          <>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-class">Class</label>
              <select id="cc-class" className="modal-select" value={form.className}
                onChange={e => update('className', e.target.value)}>
                {CLASS_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-subclass">Subclass (optional)</label>
              <input id="cc-subclass" className="modal-input" value={form.subclass}
                onChange={e => update('subclass', e.target.value)} placeholder="e.g. College of Lore" />
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-level">Level</label>
              <input id="cc-level" type="number" min={1} max={20} className="modal-input" value={form.level}
                onChange={e => update('level', Math.min(20, Math.max(1, Number(e.target.value) || 1)))} />
            </div>
          </>
        )}

        {STEPS[step] === 'Ability Scores' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {ABILITIES.map(([key, label]) => (
              <div className="modal-field" key={key}>
                <label className="modal-label" htmlFor={`cc-${key}`}>{label} ({modifier(form.abilityScores[key])})</label>
                <input id={`cc-${key}`} type="number" min={1} max={30} className="modal-input"
                  value={form.abilityScores[key]}
                  onChange={e => setAbility(key, Math.min(30, Math.max(1, Number(e.target.value) || 10)))} />
              </div>
            ))}
          </div>
        )}

        {STEPS[step] === 'Skills' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {SKILL_OPTIONS.map(skill => (
              <label key={skill} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                <input type="checkbox" checked={form.skills.includes(skill)} onChange={() => toggleSkill(skill)} />
                {skill}
              </label>
            ))}
          </div>
        )}

        {STEPS[step] === 'Roleplay' && (
          <>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-backstory">Backstory (optional)</label>
              <textarea id="cc-backstory" className="modal-input" rows={4} value={form.backstory}
                onChange={e => update('backstory', e.target.value)} />
            </div>
            {([['traits', 'Personality Traits'], ['ideals', 'Ideals'], ['bonds', 'Bonds'], ['flaws', 'Flaws']] as const).map(([key, label]) => (
              <div className="modal-field" key={key}>
                <label className="modal-label" htmlFor={`cc-${key}`}>{label} (one per line, optional)</label>
                <textarea id={`cc-${key}`} className="modal-input" rows={2} value={form[key]}
                  onChange={e => update(key, e.target.value)} />
              </div>
            ))}
          </>
        )}

        {STEPS[step] === 'Review' && (
          <div className="wizard-review">
            {loading && <p className="screen-blurb">Deriving sheet…</p>}
            {preview && (
              <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', fontSize: 14 }}>
                <dt><strong>Name</strong></dt><dd>{form.name} — {form.className} {form.level}</dd>
                <dt><strong>Hit Points</strong></dt><dd>{preview.max_hit_points}</dd>
                <dt><strong>Proficiency</strong></dt><dd>+{preview.proficiency_bonus}</dd>
                <dt><strong>Skills</strong></dt><dd>{Object.keys(preview.skills).join(', ') || '—'}</dd>
                <dt><strong>Class Features</strong></dt><dd>{preview.class_abilities.join(', ') || '—'}</dd>
                <dt><strong>Spell Slots</strong></dt>
                <dd>{Object.entries(preview.spell_slots).map(([lvl, n]) => `L${lvl}:${n}`).join('  ') || '—'}</dd>
              </dl>
            )}
          </div>
        )}
      </div>

      {error && <p className="modal-error" role="alert" style={{ marginTop: 12 }}>{error}</p>}

      <div className="modal-actions" style={{ marginTop: 20 }}>
        <button type="button" className="ghost-btn" disabled={step === 0 || submitting}
          onClick={() => setStep(s => Math.max(0, s - 1))}>
          Back
        </button>
        {STEPS[step] === 'Review' ? (
          <button type="button" className="primary-btn" disabled={submitting || loading || !form.name.trim()}
            onClick={() => void handleCreate()}>
            {submitting ? 'Creating…' : 'Create Character'}
          </button>
        ) : (
          <button type="button" className="primary-btn" disabled={!canContinue} onClick={goNext}>
            Next
          </button>
        )}
      </div>
    </div>
  );
}
