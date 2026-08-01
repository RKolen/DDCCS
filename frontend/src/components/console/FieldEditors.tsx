/**
 * FieldEditors — form primitives for the console's character editor.
 *
 * The character record is wide (identity, vitals, roleplay, story, taxonomy
 * references, per-character AI overrides), so the editor is built from a small
 * set of field components rather than hand-rolled markup per field. Stage 2 of
 * the editor — the paragraph-backed structures — composes the same pieces.
 *
 * `TextRowsField` is the one that earns its place: the multi-value text fields
 * were previously edited as a newline-delimited textarea, which gave no signal
 * that each line becomes a separate Drupal field value. One row per value makes
 * the cardinality visible and makes reordering possible.
 */

import * as React from 'react';
import { Icon } from './atoms';
import type { TermRef } from './ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Shared styles
   ──────────────────────────────────────────────────────────── */

const labelStyle: React.CSSProperties = {
  display: 'block', fontFamily: 'var(--font-display)', fontSize: 9,
  fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
  color: 'var(--brass-dim)', marginBottom: 5,
};

const inputStyle: React.CSSProperties = {
  width: '100%', background: 'var(--canvas)',
  border: '1px solid var(--rule)', borderRadius: 4,
  color: 'var(--ink)', fontFamily: 'var(--font-body)', fontSize: 14,
  padding: '8px 10px',
};

const hintStyle: React.CSSProperties = {
  fontFamily: 'var(--font-body)', fontStyle: 'italic',
  fontSize: 11, color: 'var(--ink-faint)', marginLeft: 8, fontWeight: 400,
  textTransform: 'none', letterSpacing: 0,
};

interface FieldProps {
  label: string;
  hint?: string;
}

function FieldLabel({ label, hint, htmlFor }: FieldProps & { htmlFor?: string }): React.ReactElement {
  return (
    <label style={labelStyle} htmlFor={htmlFor}>
      {label}
      {hint != null && <span style={hintStyle}>{hint}</span>}
    </label>
  );
}

/** Stable DOM ids so every label points at its control. */
function useFieldId(label: string): string {
  const generated = React.useId();
  return `${generated}-${label.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`;
}

/* ────────────────────────────────────────────────────────────
   Collapsible section
   ──────────────────────────────────────────────────────────── */

export function EditSection({
  title, blurb, open, onToggle, children,
}: {
  title: string;
  blurb?: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <section style={{
      border: '1px solid var(--rule)', borderRadius: 8,
      background: 'var(--canvas-raised)', overflow: 'hidden',
    }}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        style={{
          display: 'flex', alignItems: 'center', gap: 10, width: '100%',
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '12px 16px', textAlign: 'left',
        }}
      >
        <Icon
          name={open ? 'chevronDown' : 'chevron'}
          size={11}
          style={{ color: 'var(--brass-dim)', flexShrink: 0 }}
        />
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 700,
          letterSpacing: '0.14em', textTransform: 'uppercase',
          color: 'var(--brass-bright)',
        }}>
          {title}
        </span>
        {blurb != null && (
          <span style={{
            fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--ink-faint)',
            fontStyle: 'italic',
          }}>
            {blurb}
          </span>
        )}
      </button>
      {open && (
        <div style={{ padding: '4px 16px 18px', borderTop: '1px solid var(--rule)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 14 }}>
            {children}
          </div>
        </div>
      )}
    </section>
  );
}

/** Responsive column grid used to pack short fields together. */
export function FieldGrid({
  children, min = 200,
}: {
  children: React.ReactNode;
  min?: number;
}): React.ReactElement {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(auto-fit, minmax(${min}px, 1fr))`,
      gap: 14,
    }}>
      {children}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Scalar fields
   ──────────────────────────────────────────────────────────── */

export function TextField({
  label, hint, value, onChange, placeholder,
}: FieldProps & {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
}): React.ReactElement {
  const id = useFieldId(label);
  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      <input
        id={id}
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={e => onChange(e.target.value)}
        style={inputStyle}
      />
    </div>
  );
}

export function TextAreaField({
  label, hint, value, onChange, placeholder, rows = 4,
}: FieldProps & {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  rows?: number;
}): React.ReactElement {
  const id = useFieldId(label);
  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      <textarea
        id={id}
        rows={rows}
        value={value}
        placeholder={placeholder}
        onChange={e => onChange(e.target.value)}
        style={{ ...inputStyle, resize: 'vertical' }}
      />
    </div>
  );
}

/**
 * A numeric field that keeps its own string state.
 *
 * Storing the raw string is what lets the box be empty: binding a number
 * directly makes a cleared box read as 0, which would silently write a level-0
 * character. An empty box means "no value" and sends null.
 */
export function NumberField({
  label, hint, value, onChange, min, max, step,
}: FieldProps & {
  value: number | null;
  onChange: (next: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
}): React.ReactElement {
  const id = useFieldId(label);
  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      <input
        id={id}
        type="number"
        value={value == null ? '' : String(value)}
        min={min}
        max={max}
        step={step}
        onChange={e => {
          const raw = e.target.value.trim();
          if (raw === '') {
            onChange(null);
            return;
          }
          const parsed = Number(raw);
          onChange(Number.isFinite(parsed) ? parsed : null);
        }}
        style={inputStyle}
      />
    </div>
  );
}

export function BoolField({
  label, hint, value, onChange,
}: FieldProps & {
  value: boolean;
  onChange: (next: boolean) => void;
}): React.ReactElement {
  const id = useFieldId(label);
  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      <label
        htmlFor={id}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer',
          fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink)',
        }}
      >
        <input
          id={id}
          type="checkbox"
          checked={value}
          onChange={e => onChange(e.target.checked)}
          style={{ accentColor: 'var(--brass)', width: 15, height: 15 }}
        />
        {value ? 'Yes' : 'No'}
      </label>
    </div>
  );
}

export function SelectField({
  label, hint, value, options, onChange, emptyLabel = '— none —', allowEmpty = true,
}: FieldProps & {
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (next: string) => void;
  emptyLabel?: string;
  /** Offer the blank option. Turn off for a field that is always one of the
      listed values, so it cannot be cleared into a meaningless state. */
  allowEmpty?: boolean;
}): React.ReactElement {
  const id = useFieldId(label);
  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      <select
        id={id}
        className="console-select"
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ width: '100%' }}
      >
        {allowEmpty && <option value="">{emptyLabel}</option>}
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Multi-value text
   ──────────────────────────────────────────────────────────── */

const rowBtnStyle: React.CSSProperties = {
  background: 'none', border: '1px solid var(--rule)', borderRadius: 4,
  color: 'var(--ink-faint)', cursor: 'pointer', padding: '0 7px',
  height: 30, display: 'flex', alignItems: 'center', flexShrink: 0,
  fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1,
};

/**
 * Edit a multi-value text field as one row per stored value.
 *
 * Each row is one Drupal field delta. Reordering matters because the order is
 * persisted and shows up in generated prose and on the character sheet.
 */
export function TextRowsField({
  label, hint, values, onChange, placeholder,
}: FieldProps & {
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}): React.ReactElement {
  const replace = (index: number, next: string): void => {
    onChange(values.map((v, i) => (i === index ? next : v)));
  };
  const remove = (index: number): void => {
    onChange(values.filter((_, i) => i !== index));
  };
  const move = (index: number, delta: number): void => {
    const target = index + delta;
    if (target < 0 || target >= values.length) return;
    const next = [...values];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  };

  return (
    <div>
      <FieldLabel label={label} hint={hint ?? 'one entry per row'} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {values.map((value, index) => (
          /* Index keys are correct here: rows are positional, and a stable id
             would have to be invented for values that are plain strings. */
          <div key={index} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              type="text"
              value={value}
              placeholder={placeholder}
              onChange={e => replace(index, e.target.value)}
              style={{ ...inputStyle, height: 30, padding: '4px 10px', fontSize: 13 }}
            />
            <button
              type="button"
              style={rowBtnStyle}
              onClick={() => move(index, -1)}
              disabled={index === 0}
              aria-label={`Move ${label} entry ${index + 1} up`}
              title="Move up"
            >
              ↑
            </button>
            <button
              type="button"
              style={rowBtnStyle}
              onClick={() => move(index, 1)}
              disabled={index === values.length - 1}
              aria-label={`Move ${label} entry ${index + 1} down`}
              title="Move down"
            >
              ↓
            </button>
            <button
              type="button"
              style={rowBtnStyle}
              onClick={() => remove(index)}
              aria-label={`Remove ${label} entry ${index + 1}`}
              title="Remove"
            >
              <Icon name="close" size={10} />
            </button>
          </div>
        ))}
        <div>
          <button
            type="button"
            className="ghost-btn ghost-small"
            onClick={() => onChange([...values, ''])}
          >
            <Icon name="plus" size={10} /> Add {label.toLowerCase()}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Taxonomy references
   ──────────────────────────────────────────────────────────── */

/**
 * Single taxonomy reference, addressed by term UUID.
 *
 * The value written to Drupal is the UUID, not the name — the mutation checks
 * it against the field's vocabulary, so a name would be both ambiguous and
 * uncheckable.
 */
export function TermSelect({
  label, hint, value, options, onChange,
}: FieldProps & {
  value: string | null;
  options: TermRef[];
  onChange: (next: string | null) => void;
}): React.ReactElement {
  const missing = value != null && !options.some(o => o.id === value);
  return (
    <div>
      <SelectField
        label={label}
        hint={hint}
        value={value ?? ''}
        options={options.map(o => ({ value: o.id, label: o.name }))}
        onChange={next => onChange(next === '' ? null : next)}
      />
      {missing && (
        <p style={{
          fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--color-warning)',
          margin: '4px 0 0',
        }}>
          The saved term is not in this vocabulary&apos;s list — saving will clear it.
        </p>
      )}
    </div>
  );
}

/** Multi-value taxonomy reference, shown as removable chips plus an add list. */
export function TermMultiSelect({
  label, hint, values, options, onChange,
}: FieldProps & {
  values: TermRef[];
  options: TermRef[];
  onChange: (next: TermRef[]) => void;
}): React.ReactElement {
  const id = useFieldId(label);
  const selected = new Set(values.map(v => v.id));
  const available = options.filter(o => !selected.has(o.id));

  return (
    <div>
      <FieldLabel label={label} hint={hint} htmlFor={id} />
      {values.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
          {values.map(term => (
            <span
              key={term.id}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '3px 6px 3px 9px', borderRadius: 4,
                border: '1px solid var(--rule)', background: 'var(--canvas)',
                fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--ink)',
              }}
            >
              {term.name}
              <button
                type="button"
                onClick={() => onChange(values.filter(v => v.id !== term.id))}
                aria-label={`Remove ${term.name}`}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--ink-faint)', padding: 0, display: 'flex',
                }}
              >
                <Icon name="close" size={9} />
              </button>
            </span>
          ))}
        </div>
      )}
      <select
        id={id}
        className="console-select"
        value=""
        disabled={available.length === 0}
        onChange={e => {
          const term = options.find(o => o.id === e.target.value);
          if (term) onChange([...values, term]);
        }}
        style={{ width: '100%' }}
      >
        <option value="">
          {available.length === 0 ? 'All options selected' : `Add ${label.toLowerCase()}…`}
        </option>
        {available.map(o => (
          <option key={o.id} value={o.id}>{o.name}</option>
        ))}
      </select>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Read-only and handoff
   ──────────────────────────────────────────────────────────── */

/** A field this screen deliberately does not own, shown for context. */
export function ReadOnlyField({
  label, value, note,
}: {
  label: string;
  value: string;
  note?: string;
}): React.ReactElement {
  return (
    <div>
      <FieldLabel label={label} hint={note} />
      <div style={{
        ...inputStyle,
        color: 'var(--ink-dim)', background: 'transparent',
        borderStyle: 'dashed',
      }}>
        {value}
      </div>
    </div>
  );
}

/**
 * A card pointing at the screen that owns a field group.
 *
 * Portrait, voice, and arc analysis each have a dedicated screen with tooling
 * this form has no business duplicating — a media picker here was how the
 * portrait ended up editable in two places.
 */
export function HandoffCard({
  title, summary, actionLabel, onOpen, thumbnailUrl, thumbnailAlt,
}: {
  title: string;
  summary: string;
  actionLabel: string;
  onOpen: () => void;
  thumbnailUrl?: string | null;
  thumbnailAlt?: string;
}): React.ReactElement {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      padding: '12px 14px', borderRadius: 6,
      border: '1px solid var(--rule)', background: 'var(--canvas)',
    }}>
      {thumbnailUrl != null && thumbnailUrl !== '' && (
        <img
          src={thumbnailUrl}
          alt={thumbnailAlt ?? ''}
          style={{
            width: 44, height: 58, objectFit: 'cover', borderRadius: 4,
            border: '1px solid var(--rule)', flexShrink: 0,
          }}
        />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700,
          letterSpacing: '0.12em', textTransform: 'uppercase',
          color: 'var(--brass-dim)', marginBottom: 3,
        }}>
          {title}
        </div>
        <div style={{
          fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--ink-dim)',
        }}>
          {summary}
        </div>
      </div>
      <button type="button" className="ghost-btn" onClick={onOpen}>
        {actionLabel}
      </button>
    </div>
  );
}
