/**
 * CharacterEditScreen — `characters/edit` and `npcs/n-edit`.
 *
 * The single place a character record is edited, covering every non-paragraph
 * field. Portrait, voice, and arc are reached by button instead, each having a
 * dedicated screen this form has no business duplicating.
 *
 * Switching the record type moves the character between the Characters and
 * NPCs rosters on the next build. Writes PATCH only changed fields via
 * /api/update-character-profile.
 */

import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon, Spinner } from '../atoms';
import {
  useConsoleData, playerCharacters, npcCharacters, rosterForScreen, ABILITY_KEYS,
} from '../ConsoleContext';
import type {
  ConsoleData, DrupalAbilityScores, DrupalCharacter, TermRef,
} from '../ConsoleContext';
import {
  EditSection, FieldGrid, TextField, TextAreaField, NumberField, BoolField,
  SelectField, TextRowsField, TermSelect, TermMultiSelect, HandoffCard,
} from '../FieldEditors';

/* ────────────────────────────────────────────────────────────
   Types
   ──────────────────────────────────────────────────────────── */

interface ApiError { error: string }

interface TermNodes { nodes: TermRef[] }

interface TermOptionsQuery {
  drupal: {
    termSpeciesItems:    TermNodes;
    termLineages:        TermNodes;
    termBackgrounds:     TermNodes;
    termLanguages:       TermNodes;
    termSkills:          TermNodes;
    termToolProfiencies: TermNodes;
    termFactions:        TermNodes;
    termTraits:          TermNodes;
  };
}

/** The editable shape of a character, flattened for form state. */
interface FormState {
  title:            string;
  firstName:        string;
  lastName:         string;
  nickname:         string;
  pronouns:         string;
  gender:           string;
  role:             string;
  campaignId:       string | null;
  characterType:    boolean;
  sourceCharacter:  boolean;
  speciesId:        string | null;
  lineageId:        string | null;
  backgroundId:     string | null;
  abilityScores:    DrupalAbilityScores;
  level:            number | null;
  maximumHitpoints: number | null;
  armorClass:       number | null;
  movementSpeed:    number | null;
  proficiencyBonus: number | null;
  gold:             number | null;
  personalityTraits: string[];
  ideals:            string[];
  bonds:             string[];
  flaws:             string[];
  personality:       string;
  notes:             string;
  majorPlotActions:     string[];
  specializedAbilities: string[];
  plotHooks:            string[];
  abilities:            string[];
  languages: TermRef[];
  skills:    TermRef[];
  tools:     TermRef[];
  factionId: string | null;
  keyTraits: TermRef[];
  recurring:        boolean;
  encounterTactics: string[];
  defeatConditions: string[];
  lairActions:      string[];
  legendaryActions: string[];
  regionalEffects:  string[];
  aiEnabled:      boolean;
  aiModel:        string;
  aiTemperature:  number | null;
  aiMaxTokens:    number | null;
  aiSystemPrompt: string;
}

type SectionId =
  | 'identity' | 'ancestry' | 'vitals' | 'roleplay'
  | 'story' | 'proficiencies' | 'antagonist' | 'ai';

/* ────────────────────────────────────────────────────────────
   Form state helpers
   ──────────────────────────────────────────────────────────── */

const GENDER_OPTIONS = [
  { value: 'female', label: 'Female' },
  { value: 'male',   label: 'Male' },
  { value: 'other',  label: 'Other' },
];

/* field_character_type is a boolean with PC as its on state. */
const RECORD_TYPE_OPTIONS = [
  { value: 'pc',  label: 'Player character' },
  { value: 'npc', label: 'NPC' },
];

const SOURCE_OPTIONS = [
  { value: 'template', label: 'Template' },
  { value: 'clone',    label: 'Campaign clone' },
];

const ABILITY_LABELS: Record<keyof DrupalAbilityScores, string> = {
  strength:     'Strength',
  dexterity:    'Dexterity',
  constitution: 'Constitution',
  intelligence: 'Intelligence',
  wisdom:       'Wisdom',
  charisma:     'Charisma',
};

/** The 5e modifier for a score, as the sheet prints it. */
function abilityModifier(score: number | null): string | undefined {
  if (score == null) {
    return undefined;
  }
  const mod = Math.floor((score - 10) / 2);
  return mod >= 0 ? `+${mod}` : String(mod);
}

function toForm(char: DrupalCharacter): FormState {
  return {
    title:            char.title,
    firstName:        char.firstName ?? '',
    lastName:         char.lastName ?? '',
    nickname:         char.nickname ?? '',
    pronouns:         char.pronouns ?? '',
    gender:           char.gender ?? '',
    role:             char.role ?? '',
    campaignId:       char.campaignId,
    /* The Drupal field defaults to PC, so an unset flag is a player character. */
    characterType:    char.characterType !== false,
    sourceCharacter:  char.sourceCharacter === true,
    speciesId:        char.speciesId,
    lineageId:        char.lineageId,
    backgroundId:     char.backgroundId,
    abilityScores:    { ...char.abilityScores },
    level:            char.level,
    maximumHitpoints: char.maximumHitpoints,
    armorClass:       char.armorClass,
    movementSpeed:    char.movementSpeed ?? null,
    proficiencyBonus: char.proficiencyBonus ?? null,
    gold:             char.gold,
    personalityTraits: char.personalityTraits,
    ideals:            char.ideals,
    bonds:             char.bonds,
    flaws:             char.flaws,
    personality:       char.personality ?? '',
    notes:             char.notes ?? '',
    majorPlotActions:     char.majorPlotActions,
    specializedAbilities: char.specializedAbilities,
    plotHooks:            char.plotHooks,
    abilities:            char.abilities,
    languages: char.languages,
    skills:    char.skills,
    tools:     char.tools,
    factionId: char.factionId,
    keyTraits: char.keyTraits,
    recurring:        char.recurring ?? false,
    encounterTactics: char.encounterTactics,
    defeatConditions: char.defeatConditions,
    lairActions:      char.lairActions,
    legendaryActions: char.legendaryActions,
    regionalEffects:  char.regionalEffects,
    aiEnabled:      char.aiEnabled ?? false,
    aiModel:        char.aiModel ?? '',
    aiTemperature:  char.aiTemperature,
    aiMaxTokens:    char.aiMaxTokens,
    aiSystemPrompt: char.aiSystemPrompt ?? '',
  };
}

/** Rows the operator left blank are not values; drop them before comparing. */
function cleanRows(rows: string[]): string[] {
  return rows.map(r => r.trim()).filter(r => r !== '');
}

function sameRows(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((v, i) => v === b[i]);
}

function termIds(terms: TermRef[]): string[] {
  return terms.map(t => t.id);
}

/**
 * The fields that differ from what Drupal holds, keyed as the mutation expects.
 *
 * Sending only these is what makes the editor safe to use on a partially
 * loaded record: a field the console never queried is never in the diff, so it
 * cannot be blanked by a save.
 */
function buildPatch(form: FormState, char: DrupalCharacter): Record<string, unknown> {
  const patch: Record<string, unknown> = {};
  const base = toForm(char);

  const scalar = <K extends keyof FormState>(key: K, current: FormState[K]): void => {
    if (current !== base[key]) patch[key] = current;
  };

  scalar('title', form.title.trim());
  scalar('firstName', form.firstName);
  scalar('lastName', form.lastName);
  scalar('nickname', form.nickname);
  scalar('pronouns', form.pronouns);
  scalar('gender', form.gender);
  scalar('role', form.role);
  scalar('campaignId', form.campaignId);
  scalar('characterType', form.characterType);
  scalar('sourceCharacter', form.sourceCharacter);
  scalar('speciesId', form.speciesId);
  scalar('lineageId', form.lineageId);
  scalar('backgroundId', form.backgroundId);
  scalar('factionId', form.factionId);
  scalar('level', form.level);
  scalar('maximumHitpoints', form.maximumHitpoints);
  scalar('armorClass', form.armorClass);
  scalar('movementSpeed', form.movementSpeed);
  scalar('proficiencyBonus', form.proficiencyBonus);
  scalar('gold', form.gold);
  scalar('personality', form.personality);
  scalar('notes', form.notes);
  scalar('recurring', form.recurring);
  scalar('aiEnabled', form.aiEnabled);
  scalar('aiModel', form.aiModel);
  scalar('aiTemperature', form.aiTemperature);
  scalar('aiMaxTokens', form.aiMaxTokens);
  scalar('aiSystemPrompt', form.aiSystemPrompt);

  /* The term selects hold UUIDs but the mutation keys them by field name. */
  if (patch.campaignId !== undefined) {
    patch.campaign = patch.campaignId;
    delete patch.campaignId;
  }
  if (patch.speciesId !== undefined) {
    patch.species = patch.speciesId;
    delete patch.speciesId;
  }
  if (patch.lineageId !== undefined) {
    patch.lineage = patch.lineageId;
    delete patch.lineageId;
  }
  if (patch.backgroundId !== undefined) {
    patch.background = patch.backgroundId;
    delete patch.backgroundId;
  }
  if (patch.factionId !== undefined) {
    patch.faction = patch.factionId;
    delete patch.factionId;
  }

  const rowFields: Array<keyof FormState> = [
    'personalityTraits', 'ideals', 'bonds', 'flaws',
    'majorPlotActions', 'specializedAbilities', 'plotHooks', 'abilities',
    'encounterTactics', 'defeatConditions', 'lairActions',
    'legendaryActions', 'regionalEffects',
  ];
  for (const key of rowFields) {
    const next = cleanRows(form[key] as string[]);
    if (!sameRows(next, base[key] as string[])) patch[key] = next;
  }

  const termFields: Array<'languages' | 'skills' | 'tools' | 'keyTraits'> = [
    'languages', 'skills', 'tools', 'keyTraits',
  ];
  for (const key of termFields) {
    const next = termIds(form[key]);
    if (!sameRows(next, termIds(base[key]))) patch[key] = next;
  }

  /* Each ability score is its own paragraph in Drupal, so only the abilities
     that actually moved are sent and the rest are left untouched. A score can
     be changed but not cleared — an empty box means "leave it alone". */
  const scores: Record<string, number> = {};
  for (const key of ABILITY_KEYS) {
    const next = form.abilityScores[key];
    if (next != null && next !== base.abilityScores[key]) scores[key] = next;
  }
  if (Object.keys(scores).length > 0) patch.abilityScores = scores;

  return patch;
}

/* ────────────────────────────────────────────────────────────
   Picker
   ──────────────────────────────────────────────────────────── */

function CharPicker({
  roster, selectedId, onSelect,
}: {
  roster: DrupalCharacter[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}): React.ReactElement {
  return (
    <aside className="char-picker">
      <ul className="char-picker-list">
        {roster.map(c => {
          const initials = c.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
          return (
            <li key={c.id}>
              <button
                type="button"
                className={`char-picker-item${c.id === selectedId ? ' active' : ''}`}
                onClick={() => onSelect(c.id)}
              >
                <span className="char-pip">
                  {c.imageUrl
                    ? <img src={c.imageUrl} alt={c.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                    : initials
                  }
                </span>
                <span className="char-pip-meta">
                  <span className="char-pip-name">{c.title}</span>
                  {c.characterClass != null && (
                    <span className="char-pip-class">
                      {c.characterClass}{c.level != null ? ` ${c.level}` : ''}
                    </span>
                  )}
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
   Edit form
   ──────────────────────────────────────────────────────────── */

interface EditFormProps {
  char: DrupalCharacter;
  data: ConsoleData;
  options: TermOptionsQuery['drupal'];
  onJump: (itemId: string, targetIndex: number) => void;
}

function EditForm({ char, data, options, onJump }: EditFormProps): React.ReactElement {
  const [form, setForm] = React.useState<FormState>(() => toForm(char));
  /* On an NPC the antagonist group is the reason the operator opened this
     screen, so it starts expanded there and collapsed on a player character. */
  const [open, setOpen] = React.useState<Record<SectionId, boolean>>(() => ({
    identity: true, ancestry: true, vitals: false, roleplay: true,
    story: false, proficiencies: false, ai: false,
    antagonist: char.characterType === false,
  }));
  const [saving, setSaving]   = React.useState(false);
  const [error, setError]     = React.useState<string | null>(null);
  const [savedAt, setSavedAt] = React.useState<string | null>(null);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm(prev => ({ ...prev, [key]: value }));
    setSavedAt(null);
  };
  const setScore = (key: keyof DrupalAbilityScores, value: number | null): void => {
    setForm(prev => ({ ...prev, abilityScores: { ...prev.abilityScores, [key]: value } }));
    setSavedAt(null);
  };
  const toggle = (id: SectionId): void => setOpen(prev => ({ ...prev, [id]: !prev[id] }));

  const patch = buildPatch(form, char);
  const isDirty = Object.keys(patch).length > 0;

  /* Read the classification from the form, not the record: switching a record
     to NPC should reveal the antagonist fields before the save, not after the
     next build moves it to the other roster. */
  const isNpc = !form.characterType;
  const savedIsNpc = char.characterType === false;

  /* The campaign select reads the same term list the campaign switcher does,
     so a campaign with no characters yet is still assignable. */
  const campaignOptions: TermRef[] = data.campaigns.map(c => ({ id: c.id, name: c.name }));
  /* An NPC only earns the full character sheet once it is marked recurring;
     a walk-on part does not need vitals, proficiencies or an AI profile. */
  const fullProfile = !isNpc || form.recurring;

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/update-character-profile', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ id: char.id, fields: patch }),
      });
      if (!res.ok) {
        const body = (await res.json()) as ApiError;
        setError(body.error ?? `Error ${res.status}`);
        return;
      }
      setSavedAt(new Date().toLocaleTimeString());
      /* Drop blank rows from the form now that they were dropped on the way
         out, so the view matches what was stored. */
      setForm(prev => ({
        ...prev,
        personalityTraits: cleanRows(prev.personalityTraits),
        ideals:            cleanRows(prev.ideals),
        bonds:             cleanRows(prev.bonds),
        flaws:             cleanRows(prev.flaws),
      }));
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setSaving(false);
    }
  };

  const portraitIdx = playerCharacters(data).findIndex(c => c.id === char.id);
  const npcIdx      = npcCharacters(data).findIndex(c => c.id === char.id);
  /* Keyed off the saved classification, not the form: the other screens still
     hold this record in the roster it was last built into. */
  const studioIdx   = savedIsNpc ? npcIdx : portraitIdx;

  const voiceSummary = char.voiceId != null
    ? `${char.voiceId} · pitch ${char.voicePitch ?? 0} · speed ${char.voiceSpeed ?? 1}`
    : 'No voice assigned';
  const arcSummary = char.arc != null
    ? `${char.arc.stage} · ${char.arc.direction} · ${char.arc.storiesAnalyzed} stories analysed`
    : 'Never analysed';

  return (
    <div className="char-sheet-detail" style={{ flex: 1, overflowY: 'auto', padding: '28px 32px 40px' }}>

      {/* Header */}
      <div style={{ marginBottom: 22 }}>
        <span className="reader-eyebrow">{savedIsNpc ? 'NPCs' : 'Characters'} · Edit profile</span>
        <h2 style={{
          fontFamily: 'var(--font-display)', fontSize: 26, color: 'var(--brass-bright)',
          letterSpacing: '0.04em', margin: '4px 0 6px',
        }}>
          {char.title}
        </h2>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', margin: 0 }}>
          {[
            char.characterClass,
            char.level != null ? `Level ${char.level}` : null,
            char.campaign,
            savedIsNpc ? 'NPC' : 'Player character',
          ].filter(Boolean).join(' · ')}
        </p>
      </div>

      {/* Handoffs to the screens that own these fields */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 22 }}>
        <HandoffCard
          title="Portrait"
          summary={char.imageUrl != null ? 'Generated in the portrait studio' : 'No portrait yet'}
          actionLabel="Open portrait studio"
          thumbnailUrl={char.imageUrl}
          thumbnailAlt={char.title}
          onOpen={() => onJump(savedIsNpc ? 'n-ascii' : 'ascii', studioIdx)}
        />
        <HandoffCard
          title="Voice"
          summary={voiceSummary}
          actionLabel="Open consultation"
          onOpen={() => onJump(savedIsNpc ? 'n-consult' : 'consult', studioIdx)}
        />
        <HandoffCard
          title="Arc analysis"
          summary={arcSummary}
          actionLabel="Open arc analysis"
          onOpen={() => onJump(savedIsNpc ? 'n-arc' : 'arc', studioIdx)}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

        <EditSection title="Identity" open={open.identity} onToggle={() => toggle('identity')}>
          <FieldGrid>
            <TextField label="Name" value={form.title} onChange={v => set('title', v)} />
            <TextField label="Nickname" value={form.nickname} onChange={v => set('nickname', v)} />
            <TextField label="First name" value={form.firstName} onChange={v => set('firstName', v)} />
            <TextField label="Last name" value={form.lastName} onChange={v => set('lastName', v)} />
            <TextField
              label="Pronouns"
              hint="used in narration"
              value={form.pronouns}
              onChange={v => set('pronouns', v)}
              placeholder="e.g. she/her"
            />
            <SelectField
              label="Gender"
              value={form.gender}
              options={GENDER_OPTIONS}
              onChange={v => set('gender', v)}
            />
            <TextField
              label="Role"
              hint={isNpc ? 'how this NPC reads at the table' : 'party role'}
              value={form.role}
              onChange={v => set('role', v)}
            />
          </FieldGrid>
          <FieldGrid>
            <TermSelect
              label="Campaign"
              hint="blank leaves the record unassigned"
              value={form.campaignId}
              options={campaignOptions}
              onChange={v => set('campaignId', v)}
            />
            <SelectField
              label="Record type"
              hint={form.characterType !== (char.characterType !== false)
                ? `saving moves this record to the ${isNpc ? 'NPCs' : 'Characters'} roster`
                : 'player character or NPC'}
              value={form.characterType ? 'pc' : 'npc'}
              options={RECORD_TYPE_OPTIONS}
              onChange={v => set('characterType', v === 'pc')}
              allowEmpty={false}
            />
            <SelectField
              label="Source character"
              hint="a template is reused across campaigns"
              value={form.sourceCharacter ? 'template' : 'clone'}
              options={SOURCE_OPTIONS}
              onChange={v => set('sourceCharacter', v === 'template')}
              allowEmpty={false}
            />
          </FieldGrid>
        </EditSection>

        <EditSection title="Ancestry" open={open.ancestry} onToggle={() => toggle('ancestry')}>
          <FieldGrid>
            <TermSelect
              label="Species"
              value={form.speciesId}
              options={options.termSpeciesItems.nodes}
              onChange={v => set('speciesId', v)}
            />
            <TermSelect
              label="Lineage"
              value={form.lineageId}
              options={options.termLineages.nodes}
              onChange={v => set('lineageId', v)}
            />
            <TermSelect
              label="Background"
              value={form.backgroundId}
              options={options.termBackgrounds.nodes}
              onChange={v => set('backgroundId', v)}
            />
          </FieldGrid>
        </EditSection>

        {fullProfile && (
          <EditSection title="Vitals" open={open.vitals} onToggle={() => toggle('vitals')}>
            <FieldGrid min={140}>
              <NumberField label="Level" value={form.level} onChange={v => set('level', v)} min={1} />
              <NumberField label="Max HP" value={form.maximumHitpoints} onChange={v => set('maximumHitpoints', v)} min={0} />
              <NumberField label="Armor class" value={form.armorClass} onChange={v => set('armorClass', v)} min={0} />
              <NumberField label="Speed" hint="ft" value={form.movementSpeed} onChange={v => set('movementSpeed', v)} min={0} />
              <NumberField label="Proficiency bonus" value={form.proficiencyBonus} onChange={v => set('proficiencyBonus', v)} min={0} />
              <NumberField label="Gold" hint="gp" value={form.gold} onChange={v => set('gold', v)} min={0} />
            </FieldGrid>
            <FieldGrid min={140}>
              {ABILITY_KEYS.map(key => (
                <NumberField
                  key={key}
                  label={ABILITY_LABELS[key]}
                  hint={abilityModifier(form.abilityScores[key])}
                  value={form.abilityScores[key]}
                  onChange={v => setScore(key, v)}
                  min={1}
                  max={30}
                />
              ))}
            </FieldGrid>
            <p style={{
              fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12,
              color: 'var(--ink-faint)', margin: 0,
            }}>
              Class and subclass, spell slots and equipment are paragraph-backed
              and are still edited in Drupal. A blank ability score is left as it
              is on save — it cannot be cleared from here.
            </p>
          </EditSection>
        )}

        <EditSection
          title="Roleplay"
          blurb="what the AI draws on for voice and motivation"
          open={open.roleplay}
          onToggle={() => toggle('roleplay')}
        >
          <FieldGrid min={280}>
            <TextRowsField
              label="Personality traits"
              values={form.personalityTraits}
              onChange={v => set('personalityTraits', v)}
              placeholder="How they look, act, and speak"
            />
            <TextRowsField
              label="Ideals"
              values={form.ideals}
              onChange={v => set('ideals', v)}
              placeholder="What drives them above all else"
            />
            <TextRowsField
              label="Bonds"
              values={form.bonds}
              onChange={v => set('bonds', v)}
              placeholder="Who or what they care most about"
            />
            <TextRowsField
              label="Flaws"
              values={form.flaws}
              onChange={v => set('flaws', v)}
              placeholder="Their vices or compulsions"
            />
          </FieldGrid>
          <FieldGrid min={240}>
            <TermSelect
              label="Faction"
              hint={isNpc ? 'how this NPC stands to the party' : 'allegiance'}
              value={form.factionId}
              options={options.termFactions.nodes}
              onChange={v => set('factionId', v)}
            />
            <TermMultiSelect
              label="Key traits"
              hint="shared vocabulary — reused across the roster"
              values={form.keyTraits}
              options={options.termTraits.nodes}
              onChange={v => set('keyTraits', v)}
            />
          </FieldGrid>
          <TextAreaField
            label="Personality"
            hint="prose summary"
            value={form.personality}
            onChange={v => set('personality', v)}
            rows={3}
          />
          <TextAreaField
            label="Notes"
            hint="DM notes, not shown to players"
            value={form.notes}
            onChange={v => set('notes', v)}
            rows={3}
          />
        </EditSection>

        <EditSection title="Story" open={open.story} onToggle={() => toggle('story')}>
          <FieldGrid min={280}>
            <TextRowsField
              label="Major plot actions"
              values={form.majorPlotActions}
              onChange={v => set('majorPlotActions', v)}
            />
            <TextRowsField
              label="Plot hooks"
              values={form.plotHooks}
              onChange={v => set('plotHooks', v)}
            />
            <TextRowsField
              label="Specialized abilities"
              values={form.specializedAbilities}
              onChange={v => set('specializedAbilities', v)}
            />
            <TextRowsField
              label="Abilities"
              values={form.abilities}
              onChange={v => set('abilities', v)}
            />
          </FieldGrid>
        </EditSection>

        {fullProfile && (
          <EditSection title="Proficiencies" open={open.proficiencies} onToggle={() => toggle('proficiencies')}>
            <FieldGrid min={240}>
              <TermMultiSelect
                label="Languages"
                values={form.languages}
                options={options.termLanguages.nodes}
                onChange={v => set('languages', v)}
              />
              <TermMultiSelect
                label="Skills"
                values={form.skills}
                options={options.termSkills.nodes}
                onChange={v => set('skills', v)}
              />
              <TermMultiSelect
                label="Tools"
                values={form.tools}
                options={options.termToolProfiencies.nodes}
                onChange={v => set('tools', v)}
              />
            </FieldGrid>
          </EditSection>
        )}

        {isNpc && (
          <EditSection
            title="Antagonist"
            blurb="how this NPC behaves in an encounter"
            open={open.antagonist}
            onToggle={() => toggle('antagonist')}
          >
            <BoolField
              label="Recurring"
              hint="a recurring NPC gets the full character profile"
              value={form.recurring}
              onChange={v => set('recurring', v)}
            />
            <FieldGrid min={280}>
              <TextRowsField
                label="Encounter tactics"
                values={form.encounterTactics}
                onChange={v => set('encounterTactics', v)}
              />
              <TextRowsField
                label="Defeat conditions"
                values={form.defeatConditions}
                onChange={v => set('defeatConditions', v)}
              />
              <TextRowsField
                label="Lair actions"
                values={form.lairActions}
                onChange={v => set('lairActions', v)}
              />
              <TextRowsField
                label="Legendary actions"
                values={form.legendaryActions}
                onChange={v => set('legendaryActions', v)}
              />
              <TextRowsField
                label="Regional effects"
                values={form.regionalEffects}
                onChange={v => set('regionalEffects', v)}
              />
            </FieldGrid>
          </EditSection>
        )}

        {isNpc && !form.recurring && (
          <p style={{
            fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--ink-faint)',
            fontStyle: 'italic', margin: 0, padding: '0 4px',
          }}>
            Vitals, proficiencies and the AI profile are hidden for a one-off NPC.
            Turn on <strong>Recurring</strong> above to fill in the full character
            profile.
          </p>
        )}

        {fullProfile && (
          <EditSection
            title="AI profile"
            blurb="per-character overrides"
            open={open.ai}
            onToggle={() => toggle('ai')}
          >
            <FieldGrid min={180}>
              <BoolField label="AI enabled" value={form.aiEnabled} onChange={v => set('aiEnabled', v)} />
              <TextField label="Model" value={form.aiModel} onChange={v => set('aiModel', v)} />
              <NumberField
                label="Temperature"
                value={form.aiTemperature}
                onChange={v => set('aiTemperature', v)}
                min={0}
                max={2}
                step={0.1}
              />
              <NumberField
                label="Max tokens"
                value={form.aiMaxTokens}
                onChange={v => set('aiMaxTokens', v)}
                min={1}
              />
            </FieldGrid>
            <TextAreaField
              label="System prompt"
              value={form.aiSystemPrompt}
              onChange={v => set('aiSystemPrompt', v)}
              rows={4}
            />
          </EditSection>
        )}
      </div>

      {/* Footer */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap',
        paddingTop: 18, marginTop: 18, borderTop: '1px solid var(--rule)',
      }}>
        <button
          type="button"
          className="primary-btn"
          disabled={saving || !isDirty}
          onClick={() => void handleSave()}
        >
          {saving ? <Spinner /> : <Icon name="tools" size={11} />}
          {saving ? 'Saving…' : 'Save changes'}
        </button>

        {isDirty && !saving && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--brass-dim)' }}>
            {Object.keys(patch).length} field{Object.keys(patch).length === 1 ? '' : 's'} changed
          </span>
        )}
        {!isDirty && savedAt == null && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)' }}>
            No changes
          </span>
        )}
        {savedAt != null && !isDirty && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-success)' }}>
            Saved at {savedAt}
          </span>
        )}
        {error != null && (
          <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
            {error}
          </span>
        )}
      </div>

      <p style={{
        fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12,
        color: 'var(--ink-faint)', margin: '10px 0 0',
      }}>
        Saved values reach other screens on the next page load — the console reads
        its data from the Gatsby build.
      </p>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function CharacterEditScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data   = useConsoleData();
  const isNpc  = ctx.npcMode === true;
  const pinned = typeof ctx.editCharId === 'string' ? ctx.editCharId : null;

  /* 100 is graphql_compose's hard ceiling on `first`, not a guess at the size:
     the largest of these vocabularies currently holds 38 terms. */
  const options = useStaticQuery<TermOptionsQuery>(graphql`
    query CharacterEditTerms {
      drupal {
        termSpeciesItems(first: 100)    { nodes { id name } }
        termLineages(first: 100)        { nodes { id name } }
        termBackgrounds(first: 100)     { nodes { id name } }
        termLanguages(first: 100)       { nodes { id name } }
        termSkills(first: 100)          { nodes { id name } }
        termToolProfiencies(first: 100) { nodes { id name } }
        termFactions(first: 100)        { nodes { id name } }
        termTraits(first: 100)          { nodes { id name } }
      }
    }
  `);

  /* A deep link may name a character outside the active campaign; rosterForScreen
     pins it so the link always lands somewhere. NPCs are not campaign-scoped, so
     for them this is the whole NPC list. */
  const roster = rosterForScreen(data, {
    npcMode:      isNpc,
    campaignName: ctx.activeCampaignName,
    pinnedId:     pinned,
  });

  const pinnedIdx = pinned != null ? roster.findIndex(c => c.id === pinned) : -1;
  const idx  = pinnedIdx !== -1 ? pinnedIdx : (ctx.charIdx ?? 0);
  const char = roster[idx] ?? roster[0] ?? null;

  /* Jump to the screen that owns a field group, translating the selection into
     that screen's own roster index — this screen's roster is campaign-scoped
     and theirs is not, so the raw index would select the wrong character. */
  const jump = (itemId: string, targetIndex: number): void => {
    setCtx({
      ...ctx,
      editCharId: undefined,
      _jumpTo: {
        sectionId: isNpc ? 'npcs' : 'characters',
        itemId,
        charIdx: targetIndex >= 0 ? targetIndex : 0,
      },
    });
  };

  if (char == null) {
    /* Only the player roster is campaign-scoped, so only it can be empty
       "in <campaign>" — an empty NPC roster means there are none at all. */
    const scope = !isNpc && ctx.activeCampaignName != null && ctx.activeCampaignName !== ''
      ? ` in ${ctx.activeCampaignName}`
      : '';
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">{isNpc ? 'NPCs' : 'Characters'} · Edit profile</span>
            <h2>Edit {isNpc ? 'NPC' : 'character'} profile</h2>
            <p className="screen-blurb">
              No {isNpc ? 'NPCs' : 'characters'} found{scope}.
            </p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-chardetails">
      <CharPicker
        roster={roster}
        selectedId={char.id}
        onSelect={id => {
          const i = roster.findIndex(c => c.id === id);
          if (i !== -1) setCtx({ ...ctx, charIdx: i, editCharId: undefined });
        }}
      />
      <EditForm
        key={char.id}
        char={char}
        data={data}
        options={options.drupal}
        onJump={jump}
      />
    </div>
  );
}
