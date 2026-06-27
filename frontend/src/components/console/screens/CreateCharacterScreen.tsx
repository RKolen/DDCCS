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
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData } from '../ConsoleContext';
import { CreateBackgroundModal } from './CreateBackgroundModal';
import type { BackgroundDefinition } from './CreateBackgroundModal';

interface TermNode { name: string }
interface FeatNode { name: string; featType?: { name?: string } | null }

interface TaxonomyQuery {
  drupal: {
    termClasses:        { nodes: TermNode[] };
    termSkills:         { nodes: TermNode[] };
    termSpeciesItems:   { nodes: TermNode[] };
    termBackgrounds:    { nodes: TermNode[] };
    termLineages:       { nodes: TermNode[] };
    termAbilityScores:  { nodes: TermNode[] };
    termToolProfiencies:{ nodes: TermNode[] };
    termFeats:          { nodes: FeatNode[] };
  };
}

const OTHER_OPTION = '__other__';

/**
 * A taxonomy-backed select with an "Other (not on the list)" escape that
 * reveals a free-text input. New names are created on the backend at submit
 * via the createCharacter data producer's findOrCreateTerm.
 */
function VocabSelect({
  id, label, value, options, placeholder, onChange,
}: {
  id:          string;
  label:       string;
  value:       string;
  options:     string[];
  placeholder: string;
  onChange:    (value: string) => void;
}): React.ReactElement {
  const inList = value !== '' && options.includes(value);
  const [custom, setCustom] = React.useState(value !== '' && !inList);
  const selectValue = custom ? OTHER_OPTION : (inList ? value : '');

  const handleSelect = (next: string): void => {
    if (next === OTHER_OPTION) {
      setCustom(true);
      onChange('');
    } else {
      setCustom(false);
      onChange(next);
    }
  };

  return (
    <div className="modal-field">
      <label className="modal-label" htmlFor={id}>{label}</label>
      <select id={id} className="modal-select" value={selectValue}
        onChange={e => handleSelect(e.target.value)}>
        <option value="">Select…</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
        <option value={OTHER_OPTION}>Other (not on the list)…</option>
      </select>
      {custom && (
        <input id={`${id}-custom`} className="modal-input" style={{ marginTop: 8 }}
          value={value} placeholder={placeholder}
          onChange={e => onChange(e.target.value)} />
      )}
    </div>
  );
}

const ABILITIES = [
  ['strength', 'Strength'],
  ['dexterity', 'Dexterity'],
  ['constitution', 'Constitution'],
  ['intelligence', 'Intelligence'],
  ['wisdom', 'Wisdom'],
  ['charisma', 'Charisma'],
] as const;

type AbilityKey = (typeof ABILITIES)[number][0];

const STEPS = ['Identity', 'Class & Level', 'Ability Scores', 'Skills', 'Roleplay'] as const;

interface AbilityScores {
  strength:     number;
  dexterity:    number;
  constitution: number;
  intelligence: number;
  wisdom:       number;
  charisma:     number;
}

interface FormState {
  firstName:     string;
  lastName:      string;
  nickname:      string;
  className:     string;
  level:         number;
  abilityScores: AbilityScores;
  species:       string;
  subspecies:    string;
  background:    string;
  subclass:      string;
  backstory:     string;
  traits:        string;
  ideals:        string;
  bonds:         string;
  flaws:         string;
}

interface CreateResult {
  sourceId: string;
  title:    string;
  attached: boolean;
  warning?: string;
}

interface SkillChoice {
  id:    string;
  label: string;
  count: number;
  from:  string[];  // empty means any of this kind
  kind:  string;    // 'skill' | 'tool' | 'skill_or_tool'
}

interface SkillPlanState {
  granted:       string[];
  granted_tools: string[];
  choices:       SkillChoice[];
}

const DEFAULT_FORM: FormState = {
  firstName:     '',
  lastName:      '',
  nickname:      '',
  className:     'Fighter',
  level:         1,
  abilityScores: { strength: 10, dexterity: 10, constitution: 10, intelligence: 10, wisdom: 10, charisma: 10 },
  species:       'Human',
  subspecies:    '',
  background:    '',
  subclass:      '',
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
  const taxonomy = useStaticQuery<TaxonomyQuery>(graphql`
    query CreateCharacterTaxonomy {
      drupal {
        termClasses(first: 50) { nodes { name } }
        termSkills(first: 50) { nodes { name } }
        termSpeciesItems(first: 100) { nodes { name } }
        termBackgrounds(first: 100) { nodes { name } }
        termLineages(first: 100) { nodes { name } }
        termAbilityScores(first: 10) { nodes { name } }
        termToolProfiencies(first: 100) { nodes { name } }
        termFeats(first: 100) { nodes { name featType { ... on Drupal_TermFeatType { name } } } }
      }
    }
  `);
  const sortedNames = (nodes: TermNode[]): string[] =>
    nodes.map(n => n.name).sort((a, b) => a.localeCompare(b));
  const classOptions      = React.useMemo(() => sortedNames(taxonomy.drupal.termClasses.nodes), [taxonomy]);
  const skillOptions      = React.useMemo(() => sortedNames(taxonomy.drupal.termSkills.nodes), [taxonomy]);
  const speciesOptions    = React.useMemo(() => sortedNames(taxonomy.drupal.termSpeciesItems.nodes), [taxonomy]);
  const backgroundOptions = React.useMemo(() => sortedNames(taxonomy.drupal.termBackgrounds.nodes), [taxonomy]);
  const lineageOptions    = React.useMemo(() => sortedNames(taxonomy.drupal.termLineages.nodes), [taxonomy]);
  const abilityScoreOptions = React.useMemo(() => sortedNames(taxonomy.drupal.termAbilityScores.nodes), [taxonomy]);
  const toolOptions       = React.useMemo(() => sortedNames(taxonomy.drupal.termToolProfiencies.nodes), [taxonomy]);
  const originFeatOptions = React.useMemo(
    () => taxonomy.drupal.termFeats.nodes
      .filter(f => f.featType?.name === 'Origin')
      .map(f => f.name)
      .sort((a, b) => a.localeCompare(b)),
    [taxonomy],
  );

  const { campaigns } = useConsoleData();
  const activeCampaign =
    campaigns.find(c => c.name === ctx.activeCampaignName) ?? campaigns[0] ?? null;

  const [step,       setStep]       = React.useState(0);
  const [form,       setForm]       = React.useState<FormState>(DEFAULT_FORM);
  const [submitting, setSubmitting] = React.useState(false);
  const [error,      setError]      = React.useState<string | null>(null);
  const [result,     setResult]     = React.useState<CreateResult | null>(null);
  const [bgDefinition, setBgDefinition] = React.useState<BackgroundDefinition | null>(null);
  const [showBgModal,  setShowBgModal]  = React.useState(false);
  const [resolvingBg,  setResolvingBg]  = React.useState(false);

  // A background not in the taxonomy is a homebrew background defined via modal;
  // one in the taxonomy is an official background resolved from the rules wiki.
  const isHomebrewBackground =
    form.background.trim() !== '' && !backgroundOptions.includes(form.background);

  // Changing the background invalidates any prior definition; a homebrew choice
  // opens the modal to define it.
  const lastBgRef = React.useRef('');
  React.useEffect(() => {
    if (form.background === lastBgRef.current) return;
    lastBgRef.current = form.background;
    setBgDefinition(null);
    if (isHomebrewBackground) setShowBgModal(true);
  }, [form.background, isHomebrewBackground]);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const setAbility = (key: AbilityKey, value: number): void => {
    setForm(prev => ({ ...prev, abilityScores: { ...prev.abilityScores, [key]: value } }));
  };

  const [skillPlan,     setSkillPlan]     = React.useState<SkillPlanState | null>(null);
  const [grantedSel,    setGrantedSel]    = React.useState<string[]>([]);
  const [grantedToolSel, setGrantedToolSel] = React.useState<string[]>([]);
  const [choiceSel,     setChoiceSel]     = React.useState<Record<string, string[]>>({});
  const [loadingSkills, setLoadingSkills] = React.useState(false);

  // Choice items can be skills or tools; split each into the right field by
  // checking which vocabulary it belongs to.
  const choiceItems = React.useMemo(() => Object.values(choiceSel).flat(), [choiceSel]);
  const selectedSkills = React.useMemo(
    () => Array.from(new Set([...grantedSel, ...choiceItems.filter(i => skillOptions.includes(i))])),
    [grantedSel, choiceItems, skillOptions],
  );
  const selectedTools = React.useMemo(
    () => Array.from(new Set([...grantedToolSel, ...choiceItems.filter(i => toolOptions.includes(i))])),
    [grantedToolSel, choiceItems, toolOptions],
  );

  // Resolve the class + species/subspecies skill plan, then layer on background
  // grants (fixed skills + the Skilled feat's three free picks).
  const loadSkillPlan = React.useCallback(async (): Promise<void> => {
    setLoadingSkills(true);
    try {
      const res = await fetch('/api/skill-plan', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          className: form.className, level: form.level,
          species: form.species.trim(), subspecies: form.subspecies.trim() || null,
        }),
      });
      const data = (await res.json()) as {
        granted?: string[]; granted_tools?: string[]; choices?: SkillChoice[];
      };
      const granted = Array.from(new Set([...(data.granted ?? []), ...(bgDefinition?.skills ?? [])]));
      const grantedTools = Array.from(new Set([...(data.granted_tools ?? []), ...(bgDefinition?.tools ?? [])]));
      const choices = [...(data.choices ?? [])];
      if (bgDefinition?.feat === 'Skilled') {
        choices.push({ id: 'feat:Skilled', label: 'Skilled feat', count: 3, from: [], kind: 'skill_or_tool' });
      }
      setSkillPlan({ granted, granted_tools: grantedTools, choices });
      setGrantedSel(granted);
      setGrantedToolSel(grantedTools);
      setChoiceSel({});
    } catch {
      const bgSkills = bgDefinition?.skills ?? [];
      const bgTools = bgDefinition?.tools ?? [];
      setSkillPlan({ granted: bgSkills, granted_tools: bgTools, choices: [] });
      setGrantedSel(bgSkills);
      setGrantedToolSel(bgTools);
    } finally {
      setLoadingSkills(false);
    }
  }, [form.className, form.level, form.species, form.subspecies, bgDefinition]);

  const toggleGranted = (skill: string): void => {
    setGrantedSel(prev => (prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]));
  };

  const toggleGrantedTool = (tool: string): void => {
    setGrantedToolSel(prev => (prev.includes(tool) ? prev.filter(t => t !== tool) : [...prev, tool]));
  };

  const toggleChoice = (choiceId: string, skill: string, count: number): void => {
    setChoiceSel(prev => {
      const current = prev[choiceId] ?? [];
      if (current.includes(skill)) {
        return { ...prev, [choiceId]: current.filter(s => s !== skill) };
      }
      if (current.length >= count) return prev;
      return { ...prev, [choiceId]: [...current, skill] };
    });
  };

  const requestBody = React.useCallback(() => ({
    name:              `${form.firstName.trim()} ${form.lastName.trim()}`.trim(),
    firstName:         form.firstName.trim(),
    lastName:          form.lastName.trim() || null,
    nickname:          form.nickname.trim() || null,
    className:         form.className,
    level:             form.level,
    abilityScores:     form.abilityScores,
    skills:            selectedSkills,
    tools:             selectedTools,
    background:        form.background.trim(),
    backgroundDefinition: bgDefinition,
    species:           form.species.trim(),
    subspecies:        form.subspecies.trim() || null,
    subclass:          form.subclass.trim() || null,
    backstory:         form.backstory.trim(),
    personalityTraits: splitLines(form.traits),
    ideals:            splitLines(form.ideals),
    bonds:             splitLines(form.bonds),
    flaws:             splitLines(form.flaws),
    campaignId:        activeCampaign?.id ?? null,
    dryRun:            false,
  }), [form, activeCampaign, isHomebrewBackground, bgDefinition, selectedSkills, selectedTools]);

  // Resolve an official background's granted data from the rules wiki the first
  // time the user advances past the Identity step (used to pre-select skills).
  const resolveBackground = React.useCallback(async (): Promise<void> => {
    const name = form.background.trim();
    if (name === '' || isHomebrewBackground || bgDefinition !== null) return;
    setResolvingBg(true);
    try {
      const res = await fetch('/api/resolve-background', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ name }),
      });
      const data = (await res.json()) as { background?: {
        ability_options?: string[]; feat?: string; feat_description?: string; skills?: string[];
        tools?: string[]; gold?: number; equipment?: string[];
      } | null };
      const b = data.background;
      if (res.ok && b) {
        setBgDefinition({
          abilities: b.ability_options ?? [], skills: b.skills ?? [], tools: b.tools ?? [],
          feat: b.feat ?? '', feat_description: b.feat_description ?? '',
          gold: b.gold ?? 0, equipment: b.equipment ?? [],
        });
      }
    } catch {
      /* Non-fatal: proceed without background grants. */
    } finally {
      setResolvingBg(false);
    }
  }, [form.background, isHomebrewBackground, bgDefinition]);

  const goNext = async (): Promise<void> => {
    if (STEPS[step] === 'Identity') await resolveBackground();
    const next = Math.min(STEPS.length - 1, step + 1);
    if (STEPS[next] === 'Skills' && skillPlan === null) await loadSkillPlan();
    setStep(next);
  };

  const handleCreate = async (): Promise<void> => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch('/api/create-character', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(requestBody()),
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

  const canContinue = step !== 0 || form.firstName.trim().length > 0;

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
              onClick={() => {
                setResult(null); setForm(DEFAULT_FORM); setStep(0);
                setBgDefinition(null); setSkillPlan(null);
                setGrantedSel([]); setGrantedToolSel([]); setChoiceSel({});
              }}
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
              <label className="modal-label" htmlFor="cc-first">First name</label>
              <input id="cc-first" className="modal-input" value={form.firstName} autoFocus
                onChange={e => update('firstName', e.target.value)} placeholder="First name" />
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-last">Last name (optional)</label>
              <input id="cc-last" className="modal-input" value={form.lastName}
                onChange={e => update('lastName', e.target.value)} placeholder="Last name" />
            </div>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-nick">Nickname (optional)</label>
              <input id="cc-nick" className="modal-input" value={form.nickname}
                onChange={e => update('nickname', e.target.value)} placeholder="Nickname" />
            </div>
            <VocabSelect id="cc-species" label="Species" value={form.species}
              options={speciesOptions} placeholder="New species name"
              onChange={v => update('species', v)} />
            <VocabSelect id="cc-subspecies" label="Subspecies (optional)" value={form.subspecies}
              options={lineageOptions} placeholder="New subspecies name"
              onChange={v => update('subspecies', v)} />
            <VocabSelect id="cc-bg" label="Background" value={form.background}
              options={backgroundOptions} placeholder="New background name"
              onChange={v => update('background', v)} />
            {isHomebrewBackground && (
              <div className="modal-field">
                <button type="button" className="ghost-btn" onClick={() => setShowBgModal(true)}>
                  {bgDefinition ? 'Edit homebrew background details' : 'Define homebrew background…'}
                </button>
                {bgDefinition && (
                  <p className="screen-blurb" style={{ marginTop: 6 }}>
                    {bgDefinition.abilities.length} abilities · {bgDefinition.skills.length} skills ·
                    {' '}{bgDefinition.tools.length} tools · {bgDefinition.feat || 'no feat'}
                  </p>
                )}
              </div>
            )}
          </>
        )}

        {STEPS[step] === 'Class & Level' && (
          <>
            <div className="modal-field">
              <label className="modal-label" htmlFor="cc-class">Class</label>
              <select id="cc-class" className="modal-select" value={form.className}
                onChange={e => update('className', e.target.value)}>
                {classOptions.map(c => <option key={c} value={c}>{c}</option>)}
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
          loadingSkills ? (
            <p className="screen-blurb">Resolving skill options…</p>
          ) : (
            <>
              {skillPlan && skillPlan.granted.length > 0 && (
                <div className="modal-field">
                  <label className="modal-label">Granted (species &amp; background) — uncheck to drop</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                    {skillPlan.granted.map(skill => (
                      <label key={skill} style={{ display: 'flex', gap: 6, fontSize: 13 }}>
                        <input type="checkbox" checked={grantedSel.includes(skill)} onChange={() => toggleGranted(skill)} />
                        {skill}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {skillPlan && skillPlan.granted_tools.length > 0 && (
                <div className="modal-field">
                  <label className="modal-label">Granted tools (class &amp; background) — uncheck to drop</label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                    {skillPlan.granted_tools.map(tool => (
                      <label key={tool} style={{ display: 'flex', gap: 6, fontSize: 13 }}>
                        <input type="checkbox" checked={grantedToolSel.includes(tool)} onChange={() => toggleGrantedTool(tool)} />
                        {tool}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {skillPlan?.choices.map(choice => {
                const base = choice.kind === 'tool' ? toolOptions
                  : choice.kind === 'skill_or_tool' ? [...skillOptions, ...toolOptions]
                  : skillOptions;
                const options = choice.from.length > 0 ? choice.from : base;
                const picked = choiceSel[choice.id] ?? [];
                return (
                  <div className="modal-field" key={choice.id}>
                    <label className="modal-label">
                      {choice.label}: choose {choice.count} — {picked.length}/{choice.count}
                    </label>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                      {options.map(option => {
                        const checked = picked.includes(option);
                        const usedElsewhere = grantedSel.includes(option) || grantedToolSel.includes(option)
                          || Object.entries(choiceSel).some(([id, list]) => id !== choice.id && list.includes(option));
                        const atLimit = !checked && picked.length >= choice.count;
                        const disabled = usedElsewhere || atLimit;
                        return (
                          <label key={option} style={{ display: 'flex', gap: 6, fontSize: 13, opacity: disabled ? 0.45 : 1 }}>
                            <input type="checkbox" checked={checked} disabled={disabled}
                              onChange={() => toggleChoice(choice.id, option, choice.count)} />
                            {option}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                );
              })}

              {(!skillPlan
                || (skillPlan.granted.length === 0 && skillPlan.granted_tools.length === 0
                    && skillPlan.choices.length === 0)) && (
                <p className="screen-blurb">No skill or tool grants/choices for this character.</p>
              )}
            </>
          )
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

      </div>

      {error && <p className="modal-error" role="alert" style={{ marginTop: 12 }}>{error}</p>}

      <div className="modal-actions" style={{ marginTop: 20 }}>
        <button type="button" className="ghost-btn" disabled={step === 0 || submitting}
          onClick={() => setStep(s => Math.max(0, s - 1))}>
          Back
        </button>
        {step === STEPS.length - 1 ? (
          <button type="button" className="primary-btn" disabled={submitting || !form.firstName.trim()}
            onClick={() => void handleCreate()}>
            {submitting ? 'Creating…' : 'Create Character'}
          </button>
        ) : (
          <button type="button" className="primary-btn"
            disabled={!canContinue || resolvingBg || loadingSkills}
            onClick={() => void goNext()}>
            {resolvingBg ? 'Resolving background…' : loadingSkills ? 'Loading skills…' : 'Next'}
          </button>
        )}
      </div>

      {showBgModal && (
        <CreateBackgroundModal
          name={form.background.trim()}
          abilityOptions={abilityScoreOptions}
          skillOptions={skillOptions}
          toolOptions={toolOptions}
          featOptions={originFeatOptions}
          initial={bgDefinition}
          onSave={def => { setBgDefinition(def); setShowBgModal(false); }}
          onClose={() => setShowBgModal(false)}
        />
      )}
    </div>
  );
}
