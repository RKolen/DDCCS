import * as React from 'react';
import type { DrupalCampaign } from '../console/ConsoleContext';

interface CreateCampaignModalProps {
  onCreated: (campaign: DrupalCampaign) => void;
  onClose:   () => void;
}

interface ApiCampaignResponse {
  id:             string;
  name:           string;
  campaignStatus: string | null;
  error?:         string;
}

const STATUS_OPTIONS = [
  { value: 'active',    label: 'Active'    },
  { value: 'completed', label: 'Completed' },
  { value: 'on_hold',   label: 'On Hold'   },
] as const;

export function CreateCampaignModal({
  onCreated,
  onClose,
}: CreateCampaignModalProps): React.ReactElement {
  const [name,       setName]       = React.useState('');
  const [status,     setStatus]     = React.useState('active');
  const [submitting, setSubmitting] = React.useState(false);
  const [error,      setError]      = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Campaign name is required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res  = await fetch('/api/campaigns', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ name: trimmed, status }),
      });

      const data = (await res.json()) as ApiCampaignResponse;

      if (!res.ok) {
        setError(data.error ?? `Error ${res.status}`);
        return;
      }

      onCreated({
        id:             data.id,
        name:           data.name,
        campaignStatus: data.campaignStatus,
      });
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
        aria-labelledby="modal-title-create-campaign"
      >
        <h2 className="modal-title" id="modal-title-create-campaign">New Campaign</h2>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <div className="modal-field">
            <label className="modal-label" htmlFor="campaign-name">Name</label>
            <input
              id="campaign-name"
              type="text"
              className="modal-input"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Enter campaign name"
              autoFocus
              disabled={submitting}
            />
          </div>

          <div className="modal-field">
            <label className="modal-label" htmlFor="campaign-status">Status</label>
            <select
              id="campaign-status"
              className="modal-select"
              value={status}
              onChange={e => setStatus(e.target.value)}
              disabled={submitting}
            >
              {STATUS_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {error && <p className="modal-error" role="alert">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="ghost-btn" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="primary-btn" disabled={submitting || !name.trim()}>
              {submitting ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
