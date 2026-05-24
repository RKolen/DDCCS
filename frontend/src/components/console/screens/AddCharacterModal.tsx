import * as React from 'react';
import type { DrupalCharacter } from '../ConsoleContext';

interface AddCharacterModalProps {
  campaignId:   string;
  campaignName: string;
  available:    DrupalCharacter[];
  onAdded:      () => void;
  onClose:      () => void;
}

interface ApiError { error: string }

export function AddCharacterModal({
  campaignId,
  campaignName,
  available,
  onAdded,
  onClose,
}: AddCharacterModalProps): React.ReactElement {
  const [selected,   setSelected]   = React.useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = React.useState(false);
  const [error,      setError]      = React.useState<string | null>(null);

  const toggle = (id: string): void => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else { next.add(id); }
      return next;
    });
  };

  const handleSubmit = async (): Promise<void> => {
    if (selected.size === 0) return;
    setSubmitting(true);
    setError(null);

    try {
      for (const characterId of selected) {
        const res = await fetch('/api/campaign-party', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ campaignId, characterId }),
        });
        if (!res.ok) {
          const data = (await res.json()) as ApiError;
          setError(data.error ?? `Error ${res.status}`);
          return;
        }
      }
      onAdded();
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>): void => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={handleBackdropClick}>
      <div
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title-add-char"
        style={{ width: 480 }}
      >
        <h2 className="modal-title" id="modal-title-add-char">
          Add characters to {campaignName}
        </h2>

        {available.length === 0 ? (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', marginBottom: 20 }}>
            All characters are already in this campaign.
          </p>
        ) : (
          <div style={{ maxHeight: 320, overflowY: 'auto', marginBottom: 16 }}>
            {available.map(char => {
              const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
              const isChecked = selected.has(char.id);
              return (
                <button
                  key={char.id}
                  type="button"
                  onClick={() => toggle(char.id)}
                  style={{
                    display:         'flex',
                    alignItems:      'center',
                    gap:             12,
                    width:           '100%',
                    padding:         '8px 10px',
                    background:      isChecked ? 'rgba(201,169,110,.12)' : 'transparent',
                    border:          `1px solid ${isChecked ? 'var(--brass-dim)' : 'transparent'}`,
                    borderRadius:    4,
                    cursor:          'pointer',
                    color:           'var(--ink)',
                    textAlign:       'left',
                    marginBottom:    4,
                    transition:      'background 120ms, border-color 120ms',
                  }}
                >
                  <span style={{
                    width:          32,
                    height:         32,
                    borderRadius:   '50%',
                    background:     'var(--color-bg-overlay)',
                    border:         '1px solid var(--rule-strong)',
                    display:        'flex',
                    alignItems:     'center',
                    justifyContent: 'center',
                    fontSize:       11,
                    fontFamily:     'var(--font-display)',
                    color:          'var(--brass)',
                    flexShrink:     0,
                    overflow:       'hidden',
                  }}>
                    {char.imageUrl
                      ? <img src={char.imageUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                      : initials}
                  </span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: 13 }}>{char.title}</span>
                    {char.characterClass && (
                      <span style={{ display: 'block', fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--ink-dim)' }}>
                        {char.characterClass}{char.level != null ? ` · Lv ${char.level}` : ''}
                      </span>
                    )}
                  </span>
                  <span style={{
                    width:          18,
                    height:         18,
                    border:         `1px solid ${isChecked ? 'var(--brass)' : 'var(--rule-strong)'}`,
                    borderRadius:   3,
                    background:     isChecked ? 'var(--brass)' : 'transparent',
                    color:          'var(--desk-wood-dark)',
                    display:        'flex',
                    alignItems:     'center',
                    justifyContent: 'center',
                    fontSize:       11,
                    flexShrink:     0,
                    transition:     'background 120ms, border-color 120ms',
                  }}>
                    {isChecked ? '✓' : ''}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {error && <p className="modal-error" role="alert">{error}</p>}

        <div className="modal-actions">
          <button type="button" className="ghost-btn" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button
            type="button"
            className="primary-btn"
            disabled={submitting || selected.size === 0}
            onClick={() => void handleSubmit()}
          >
            {submitting ? 'Adding...' : `Add ${selected.size > 0 ? selected.size : ''} character${selected.size !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
