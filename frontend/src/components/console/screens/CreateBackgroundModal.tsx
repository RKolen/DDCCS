import * as React from 'react';

/**
 * CreateBackgroundModal — defines a homebrew background when the wizard's
 * background selector uses "Other (not on the list)". The collected definition
 * (ability options, skills, tools, origin feat, gold, equipment) is saved onto
 * a Homebrew-edition background term server-side during character creation.
 */

export interface BackgroundDefinition {
  abilities:        string[];
  skills:           string[];
  tools:            string[];
  feat:             string;
  feat_description?: string;
  gold:             number;
  equipment:        string[];
}

const ABILITY_CHOICE_LIMIT = 3;

interface CreateBackgroundModalProps {
  name:            string;
  abilityOptions:  string[];
  skillOptions:    string[];
  toolOptions:     string[];
  featOptions:     string[];
  initial:         BackgroundDefinition | null;
  onSave:          (definition: BackgroundDefinition) => void;
  onClose:         () => void;
}

const EMPTY: BackgroundDefinition = {
  abilities: [], skills: [], tools: [], feat: '', gold: 0, equipment: [],
};

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter(v => v !== value) : [...list, value];
}

export function CreateBackgroundModal({
  name, abilityOptions, skillOptions, toolOptions, featOptions, initial, onSave, onClose,
}: CreateBackgroundModalProps): React.ReactElement {
  const [def, setDef] = React.useState<BackgroundDefinition>(initial ?? EMPTY);

  const set = <K extends keyof BackgroundDefinition>(key: K, value: BackgroundDefinition[K]): void => {
    setDef(prev => ({ ...prev, [key]: value }));
  };

  const toggleAbility = (ability: string): void => {
    setDef(prev => {
      if (prev.abilities.includes(ability)) {
        return { ...prev, abilities: prev.abilities.filter(a => a !== ability) };
      }
      if (prev.abilities.length >= ABILITY_CHOICE_LIMIT) return prev;
      return { ...prev, abilities: [...prev.abilities, ability] };
    });
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>): void => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={handleBackdropClick}>
      <div className="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="modal-title-bg"
        style={{ maxHeight: '85vh', overflowY: 'auto' }}>
        <h2 className="modal-title" id="modal-title-bg">Define background: {name}</h2>
        <p className="screen-blurb">Homebrew background. Choose what it grants.</p>

        <div className="modal-field">
          <label className="modal-label">
            Ability Score Options (choose {ABILITY_CHOICE_LIMIT}) — {def.abilities.length}/{ABILITY_CHOICE_LIMIT}
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
            {abilityOptions.map(a => {
              const checked = def.abilities.includes(a);
              const atLimit = !checked && def.abilities.length >= ABILITY_CHOICE_LIMIT;
              return (
                <label key={a} style={{ display: 'flex', gap: 6, fontSize: 13, opacity: atLimit ? 0.5 : 1 }}>
                  <input type="checkbox" checked={checked} disabled={atLimit} onChange={() => toggleAbility(a)} />
                  {a}
                </label>
              );
            })}
          </div>
        </div>

        <div className="modal-field">
          <label className="modal-label">Skill Proficiencies</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
            {skillOptions.map(s => (
              <label key={s} style={{ display: 'flex', gap: 6, fontSize: 13 }}>
                <input type="checkbox" checked={def.skills.includes(s)}
                  onChange={() => set('skills', toggle(def.skills, s))} />
                {s}
              </label>
            ))}
          </div>
        </div>

        <div className="modal-field">
          <label className="modal-label">Tool Proficiencies</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
            {toolOptions.map(t => (
              <label key={t} style={{ display: 'flex', gap: 6, fontSize: 13 }}>
                <input type="checkbox" checked={def.tools.includes(t)}
                  onChange={() => set('tools', toggle(def.tools, t))} />
                {t}
              </label>
            ))}
          </div>
        </div>

        <div className="modal-field">
          <label className="modal-label" htmlFor="bg-feat">Origin Feat</label>
          <select id="bg-feat" className="modal-select" value={def.feat}
            onChange={e => set('feat', e.target.value)}>
            <option value="">Select…</option>
            {featOptions.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>

        <div className="modal-field">
          <label className="modal-label" htmlFor="bg-gold">Gold (alternative to equipment)</label>
          <input id="bg-gold" type="number" min={0} className="modal-input" value={def.gold}
            onChange={e => set('gold', Math.max(0, Number(e.target.value) || 0))} />
        </div>

        <div className="modal-field">
          <label className="modal-label" htmlFor="bg-equip">Equipment package (one item per line)</label>
          <textarea id="bg-equip" className="modal-input" rows={3}
            value={def.equipment.join('\n')}
            onChange={e => set('equipment', e.target.value.split('\n').map(s => s.trim()).filter(Boolean))} />
        </div>

        <div className="modal-actions">
          <button type="button" className="ghost-btn" onClick={onClose}>Cancel</button>
          <button type="button" className="primary-btn"
            disabled={def.abilities.length === 0 && def.skills.length === 0 && def.feat === ''}
            onClick={() => onSave(def)}>
            Save background
          </button>
        </div>
      </div>
    </div>
  );
}
