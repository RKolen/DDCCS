/**
 * MediaPickerModal — choose a character's portrait from the Drupal media library.
 *
 * Lists existing image media (`/api/list-portrait-media`), pre-selects the one
 * matching the character's current portrait, and on confirm points the
 * character's field_image at the chosen media (`/api/set-portrait-media`).
 * Used by the Portrait Studio (swap a freshly generated image for an older one)
 * and the Character Edit screen (pick a portrait without generating).
 */

import * as React from 'react';
import { Icon, Spinner } from './atoms';

interface MediaOption {
  id:   string;
  name: string;
  url:  string;
  alt:  string;
}

interface ListMediaResponse { media?: MediaOption[]; error?: string }
interface SetMediaResponse { imageUrl?: string | null; error?: string }

interface MediaPickerModalProps {
  characterId:      string;
  characterTitle:   string;
  currentImageUrl?: string | null;
  /** Media type to filter the library by (e.g. 'character_portrait'). */
  mediaType?:       string;
  onClose:          () => void;
  /** Called after the portrait is saved, with the new image URL. */
  onSelected:       (imageUrl: string | null) => void;
}

export function MediaPickerModal({
  characterId, characterTitle, currentImageUrl, mediaType, onClose, onSelected,
}: MediaPickerModalProps): React.ReactElement {
  const [media, setMedia] = React.useState<MediaOption[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);

  /* Close on Escape, mirroring ImageLightbox. */
  React.useEffect(() => {
    const handler = (e: KeyboardEvent): void => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  /* Load the media library once, pre-selecting the current portrait. */
  React.useEffect(() => {
    let cancelled = false;
    const load = async (): Promise<void> => {
      try {
        const query = mediaType ? `?type=${encodeURIComponent(mediaType)}` : '';
        const res = await fetch(`/api/list-portrait-media${query}`);
        const data = (await res.json()) as ListMediaResponse;
        if (cancelled) return;
        if (!res.ok) { setError(data.error ?? `Error ${res.status}`); return; }
        const list = data.media ?? [];
        // Put the current portrait first so it reads as pre-selected.
        const current = currentImageUrl ?? null;
        list.sort((a, b) => {
          const av = a.url === current ? 0 : 1;
          const bv = b.url === current ? 0 : 1;
          return av - bv;
        });
        setMedia(list);
        const match = list.find(m => m.url === current);
        if (match) setSelectedId(match.id);
      } catch {
        if (!cancelled) setError('Network error — could not load the media library.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [currentImageUrl, mediaType]);

  const handleSave = async (): Promise<void> => {
    if (selectedId == null) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/set-portrait-media', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ id: characterId, mediaId: selectedId }),
      });
      const data = (await res.json()) as SetMediaResponse;
      if (!res.ok) { setError(data.error ?? `Error ${res.status}`); return; }
      onSelected(data.imageUrl ?? null);
      onClose();
    } catch {
      setError('Network error — could not save the portrait.');
    } finally {
      setSaving(false);
    }
  };

  const selectedUrl = media.find(m => m.id === selectedId)?.url ?? currentImageUrl ?? null;
  const isCurrent = selectedUrl != null && selectedUrl === currentImageUrl;

  return (
    <div className="lightbox-backdrop" onClick={onClose}>
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--canvas)', border: '1px solid var(--rule)', borderRadius: 6,
          width: 'min(880px, 92vw)', maxHeight: '88vh', display: 'flex', flexDirection: 'column',
          boxShadow: '0 12px 48px #00000080',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--rule)' }}>
          <div>
            <span className="reader-eyebrow">Select portrait</span>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--brass-bright)', margin: '2px 0 0' }}>
              {characterTitle}
            </h2>
          </div>
          <button type="button" className="ghost-btn" onClick={onClose}>
            <Icon name="close" size={11} /> Close
          </button>
        </div>

        {/* Grid */}
        <div style={{ padding: 20, overflowY: 'auto' }}>
          {loading && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-dim)' }}>Loading media…</p>
          )}
          {!loading && media.length === 0 && error == null && (
            <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', color: 'var(--ink-dim)' }}>
              No image media found in Drupal yet.
            </p>
          )}
          {!loading && media.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 12 }}>
              {media.map(m => {
                const active = m.id === selectedId;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setSelectedId(m.id)}
                    title={m.name}
                    style={{
                      padding: 0, cursor: 'pointer', background: 'var(--surface)',
                      border: active ? '2px solid var(--brass-bright)' : '1px solid var(--rule)',
                      borderRadius: 4, overflow: 'hidden', display: 'flex', flexDirection: 'column',
                    }}
                  >
                    <img
                      src={m.url}
                      alt={m.alt || m.name}
                      style={{ width: '100%', aspectRatio: '3 / 4', objectFit: 'cover', display: 'block' }}
                    />
                    <span style={{
                      fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink-dim)',
                      padding: '4px 6px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                    }}>
                      {m.name}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 20px', borderTop: '1px solid var(--rule)' }}>
          <button
            type="button"
            className="primary-btn"
            disabled={saving || selectedId == null || isCurrent}
            onClick={() => void handleSave()}
          >
            {saving ? <Spinner /> : <Icon name="image" size={11} />}
            {saving ? 'Saving…' : (isCurrent ? 'Current portrait' : 'Set as portrait')}
          </button>
          {error != null && (
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
              {error}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
