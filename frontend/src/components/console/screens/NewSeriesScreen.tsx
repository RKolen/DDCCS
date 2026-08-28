/**
 * NewSeriesScreen — `stories/new-series`.
 *
 * Creates a story arc: the multi-story plan a run of stories is written
 * against. Replaces the original one-line-premise mockup, which could not
 * express an arc that spans levels, acts, thirteen PCs and ten antagonists.
 *
 * The arc is created in Drupal at the end of step 1 and patched as the user
 * advances, so a refresh mid-wizard costs one step rather than everything.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData } from '../ConsoleContext';
import type { DrupalCharacter } from '../ConsoleContext';
import { Icon, Spinner } from '../atoms';
import { ArcSuggestButtons } from '../ArcSuggestButtons';
import { importArcMarkdown, type ArcImportResult, type ParsedRelation } from '../../../utils/arcMarkdown';
import { partyRoster, npcRoster, importRoster, factionOptions } from '../../../utils/arcRoster';
import type { ArcFieldPayload, ArcRelationPayload } from '../../../utils/arcPayload';
import type { DrupalArcRelation } from '../ConsoleContext';

const STEPS = ['Premise', 'Antagonists', 'Party', 'Relations', 'Review'] as const;

/** A relation the operator can still reject before it is written. */
interface ReviewRelation extends ParsedRelation {
  accepted: boolean;
}

function toReview(rels: ParsedRelation[]): ReviewRelation[] {
  return rels.map(r => ({ ...r, accepted: true }));
}

function toPayload(rels: ReviewRelation[]): ArcRelationPayload[] {
  return rels
    .filter(r => r.accepted)
    .map(({ source, target, type, tier, note }) => ({ source, target, type, tier, note }));
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  const payload = (await res.json()) as T & { error?: string };
  if (!res.ok || payload.error) {
    throw new Error(payload.error ?? `Request failed (${res.status})`);
  }
  return payload;
}

/** A checkbox roster column, used for both the party and NPC pickers. */
function PickerList({
  people, selected, onToggle, empty,
}: {
  people:   DrupalCharacter[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  empty:    string;
}): React.ReactElement {
  if (people.length === 0) {
    return <p className="arc-empty">{empty}</p>;
  }
  return (
    <ul className="arc-picker">
      {people.map(p => (
        <li key={p.id}>
          <label>
            <input
              type="checkbox"
              checked={selected.has(p.id)}
              onChange={() => onToggle(p.id)}
            />
            <span className="arc-picker-name">{p.title}</span>
            {p.characterClass && <span className="arc-picker-meta">{p.characterClass}</span>}
            {p.role && <span className="arc-picker-tag">{p.role}</span>}
          </label>
        </li>
      ))}
    </ul>
  );
}

/** Accept/reject review list for one relation side. */
function RelationReview({
  rels, onToggle, nameOf,
}: {
  rels:     ReviewRelation[];
  onToggle: (index: number) => void;
  nameOf:   (id: string) => string;
}): React.ReactElement {
  if (rels.length === 0) {
    return <p className="arc-empty">Nothing yet. Import a document on step 1 to seed these.</p>;
  }
  return (
    <ul className="arc-relations">
      {rels.map((r, i) => (
        <li key={`${r.source}-${r.target}-${i}`} className={r.accepted ? '' : 'rejected'}>
          <label className="arc-rel-head">
            <input type="checkbox" checked={r.accepted} onChange={() => onToggle(i)} />
            <span className="arc-rel-tier">T{r.tier ?? '-'}</span>
            <span className="arc-rel-pair">
              {nameOf(r.source)} <span className="arc-rel-arrow">-&gt;</span> {nameOf(r.target)}
            </span>
            {r.type && <span className="arc-rel-type">{r.type}</span>}
          </label>
          {r.note && <p className="arc-rel-note">{r.note}</p>}
        </li>
      ))}
    </ul>
  );
}

export function NewSeriesScreen({ ctx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined)
    ?? data.campaigns[0]?.name ?? null;
  const campaign = data.campaigns.find(c => c.name === campaignName) ?? null;

  const party    = React.useMemo(() => partyRoster(data, campaignName), [data, campaignName]);
  const npcs     = React.useMemo(() => npcRoster(data, campaignName), [data, campaignName]);
  const roster   = React.useMemo(() => importRoster(data, campaignName), [data, campaignName]);
  const factions = React.useMemo(() => factionOptions(npcs), [npcs]);

  const nameOf = React.useCallback((id: string): string =>
    roster.find(r => r.id === id)?.title ?? id, [roster]);

  const [step, setStep]   = React.useState(0);
  const [arcId, setArcId] = React.useState<string | null>(null);
  const [busy, setBusy]   = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [saved, setSaved] = React.useState<string | null>(null);

  const [title, setTitle]                 = React.useState('');
  const [body, setBody]                   = React.useState('');
  const [overallPlot, setOverallPlot]     = React.useState('');
  const [levelRange, setLevelRange]       = React.useState('');
  const [targetStories, setTargetStories] = React.useState('');
  const [factionId, setFactionId]         = React.useState('');

  const [partyIds, setPartyIds] = React.useState<Set<string>>(new Set());
  const [npcIds, setNpcIds]     = React.useState<Set<string>>(new Set());

  const [partyRels, setPartyRels] = React.useState<ReviewRelation[]>([]);
  const [npcRels, setNpcRels]     = React.useState<ReviewRelation[]>([]);

  const [importText, setImportText] = React.useState('');
  const [preview, setPreview]       = React.useState<ArcImportResult | null>(null);

  /* Prefill the party from the campaign's current party the first time the
     roster is known — the arc almost always starts as "everyone". */
  React.useEffect(() => {
    if (partyIds.size > 0 || party.length === 0) {
      return;
    }
    const current = new Set(campaign?.currentPartyIds ?? []);
    const seed = party.filter(p => current.has(p.id)).map(p => p.id);
    setPartyIds(new Set(seed.length > 0 ? seed : party.map(p => p.id)));
  }, [party, campaign, partyIds.size]);

  const toggle = (set: Set<string>, apply: (next: Set<string>) => void) => (id: string): void => {
    const next = new Set(set);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    apply(next);
  };

  /* ── Markdown import ─────────────────────────────── */

  function runPreview(): void {
    setError(null);
    if (!importText.trim()) {
      setPreview(null);
      return;
    }
    setPreview(importArcMarkdown(importText, roster));
  }

  function applyPreview(): void {
    if (!preview) {
      return;
    }
    if (preview.fields.body)        setBody(preview.fields.body);
    if (preview.fields.overallPlot) setOverallPlot(preview.fields.overallPlot);
    if (preview.fields.levelRange)  setLevelRange(preview.fields.levelRange);
    if (preview.partyIds.length > 0) setPartyIds(new Set(preview.partyIds));
    if (preview.partyRelations.length > 0) setPartyRels(toReview(preview.partyRelations));
    if (preview.npcRelations.length > 0) {
      setNpcRels(toReview(preview.npcRelations));
      /* Anyone named as a relation target is in the arc by definition. */
      const named = new Set(npcIds);
      for (const rel of preview.npcRelations) {
        if (npcs.some(n => n.id === rel.target)) named.add(rel.target);
        if (npcs.some(n => n.id === rel.source)) named.add(rel.source);
      }
      setNpcIds(named);
    }
    setPreview(null);
    setImportText('');
  }

  /* ── Persistence ─────────────────────────────────── */

  function fieldsForStep(index: number): ArcFieldPayload {
    if (index === 0) {
      return {
        body,
        overallPlot,
        levelRange,
        targetStories: targetStories.trim() === '' ? null : Number(targetStories),
      };
    }
    if (index === 1) {
      return { faction: factionId, npcs: Array.from(npcIds) };
    }
    if (index === 2) {
      return { party: Array.from(partyIds) };
    }
    return {};
  }

  async function saveStep(index: number): Promise<string | null> {
    if (index === 0 && !arcId) {
      const created = await postJson<{ id: string }>('/api/create-story-arc', {
        campaignId: campaign?.id,
        title,
        fields:     fieldsForStep(0),
      });
      setArcId(created.id);
      return created.id;
    }
    if (!arcId) {
      return null;
    }
    const fields = index === 0 ? { ...fieldsForStep(0), title } : fieldsForStep(index);
    if (Object.keys(fields).length > 0) {
      await postJson('/api/update-story-arc', { id: arcId, fields });
    }
    if (index === 3) {
      await postJson('/api/save-arc-relations', {
        id:        arcId,
        relations: { party: toPayload(partyRels), npc: toPayload(npcRels) },
      });
    }
    return arcId;
  }

  async function advance(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await saveStep(step);
      setStep(s => Math.min(s + 1, STEPS.length - 1));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function finish(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await saveStep(3);
      setSaved(arcId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  /* Suggestions land in the same accept/reject list the import feeds, so a
     run adds to the review rather than replacing what is already there. */
  const applySuggested = React.useCallback(
    (side: 'party' | 'npc', relations: DrupalArcRelation[]): void => {
      const rows: ReviewRelation[] = relations
        .filter(r => r.sourceId && r.targetId)
        .map(r => ({
          source:     r.sourceId as string,
          target:     r.targetId as string,
          sourceText: r.sourceName ?? '',
          targetText: r.targetName ?? '',
          type:       r.type ?? '',
          tier:       (r.tier ?? 2) as 1 | 2 | 3,
          note:       r.note ?? '',
          accepted:   true,
        }));
      const setter = side === 'party' ? setPartyRels : setNpcRels;
      setter(existing => {
        const seen = new Set(existing.map(e => [e.source, e.target].sort().join('|')));
        const fresh = rows.filter(r => !seen.has([r.source, r.target].sort().join('|')));
        return [...existing, ...fresh];
      });
    },
    [],
  );

  const canAdvance =
    step === 0 ? Boolean(campaign && title.trim()) : Boolean(arcId);

  /* ── Render ──────────────────────────────────────── */

  const factionMembers = factionId
    ? npcs.filter(n => n.factionId === factionId)
    : [];

  return (
    <div className="screen-newseries">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">New story arc</span>
          <h2>Start a story arc</h2>
          <p className="screen-blurb">
            The multi-story plan a run of stories is written against: premise, act
            spine, antagonists, party, and the relationship web between them.
            {campaignName ? ` Building for ${campaignName}.` : ' No campaign selected.'}
          </p>
        </div>
      </header>

      <div className="wizard">
        <ol className="wizard-steps">
          {STEPS.map((label, i) => (
            <li key={label} className={i === step ? 'active' : ''}>
              <span>{i + 1}</span> {label}
            </li>
          ))}
        </ol>

        <div className="wizard-pane">
          {error && <p className="arc-error">{error}</p>}

          {/* ── 1. Premise ── */}
          {step === 0 && (
            <>
              <label className="form-row">
                <span>Arc title</span>
                <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. The Shadow Over Bree"
                />
              </label>

              <div className="form-row">
                <span>Import from markdown</span>
                <p className="arc-hint">
                  Paste an existing arc document. Headings, act lines, level ranges,
                  roster tables and relationship pairs are read out of it; names are
                  matched against this campaign, and anything that does not match is
                  listed rather than guessed at.
                </p>
                <textarea
                  className="arc-textarea"
                  rows={6}
                  value={importText}
                  onChange={e => setImportText(e.target.value)}
                  placeholder="Paste an arc summary or relationships document..."
                />
                <div className="arc-inline-actions">
                  <button type="button" className="ghost-btn" onClick={runPreview}>
                    Preview import
                  </button>
                </div>
              </div>

              {preview && (
                <div className="arc-preview">
                  <h4>Import preview</h4>
                  <ul>
                    <li>Premise: {preview.fields.body ? 'found' : 'not found'}</li>
                    <li>Act spine: {preview.fields.overallPlot ? 'found' : 'not found'}</li>
                    <li>Level range: {preview.fields.levelRange ?? 'not found'}</li>
                    <li>Party matched: {preview.partyIds.length}</li>
                    <li>Party relations: {preview.partyRelations.length}</li>
                    <li>NPC relations: {preview.npcRelations.length}</li>
                  </ul>
                  {preview.unmatched.length > 0 && (
                    <p className="arc-unmatched">
                      Unmatched ({preview.unmatched.length}): {preview.unmatched.join(', ')}
                    </p>
                  )}
                  <div className="arc-inline-actions">
                    <button type="button" className="primary-btn" onClick={applyPreview}>
                      Apply to this arc
                    </button>
                    <button type="button" className="ghost-btn" onClick={() => setPreview(null)}>
                      Discard
                    </button>
                  </div>
                </div>
              )}

              <label className="form-row">
                <span>Premise</span>
                <textarea
                  className="arc-textarea"
                  rows={8}
                  value={body}
                  onChange={e => setBody(e.target.value)}
                  placeholder="What this arc is, in full."
                />
              </label>

              <label className="form-row">
                <span>Act spine / overall plot</span>
                <textarea
                  className="arc-textarea"
                  rows={8}
                  value={overallPlot}
                  onChange={e => setOverallPlot(e.target.value)}
                  placeholder="ACT I ... ACT II ... ACT III ..."
                />
              </label>

              <div className="arc-field-pair">
                <label className="form-row">
                  <span>Level range</span>
                  <input
                    type="text"
                    value={levelRange}
                    onChange={e => setLevelRange(e.target.value)}
                    placeholder="4-10"
                  />
                </label>
                <label className="form-row">
                  <span>Target story count</span>
                  <input
                    type="number"
                    min={1}
                    value={targetStories}
                    onChange={e => setTargetStories(e.target.value)}
                    placeholder="6"
                  />
                </label>
              </div>
            </>
          )}

          {/* ── 2. Antagonists ── */}
          {step === 1 && (
            <>
              <label className="form-row">
                <span>Antagonist faction</span>
                <p className="arc-hint">
                  The faction's members are the antagonist roster. Adding someone to
                  the faction adds them to every arc that opposes it, so there is one
                  source of truth rather than a per-arc villain list.
                </p>
                <select value={factionId} onChange={e => setFactionId(e.target.value)}>
                  <option value="">(none)</option>
                  {factions.map(f => (
                    <option key={f.id} value={f.id}>{f.name} ({f.count})</option>
                  ))}
                </select>
              </label>

              {factionId && (
                <div className="form-row">
                  <span>Members ({factionMembers.length})</span>
                  <p className="arc-hint">Tick the ones that actually appear in this arc.</p>
                  <PickerList
                    people={factionMembers}
                    selected={npcIds}
                    onToggle={toggle(npcIds, setNpcIds)}
                    empty="No characters carry this faction."
                  />
                </div>
              )}

              <div className="form-row">
                <span>Other NPCs</span>
                <PickerList
                  people={npcs.filter(n => n.factionId !== factionId)}
                  selected={npcIds}
                  onToggle={toggle(npcIds, setNpcIds)}
                  empty="No NPCs available."
                />
              </div>
            </>
          )}

          {/* ── 3. Party ── */}
          {step === 2 && (
            <div className="form-row">
              <span>Party ({partyIds.size} of {party.length})</span>
              <p className="arc-hint">
                Prefilled from the campaign's current party. These are the campaign's
                own character records, not the canonical templates they were cloned
                from.
              </p>
              <PickerList
                people={party}
                selected={partyIds}
                onToggle={toggle(partyIds, setPartyIds)}
                empty={
                  campaignName
                    ? `No characters belong to ${campaignName} yet.`
                    : 'Select a campaign first.'
                }
              />
            </div>
          )}

          {/* ── 4. Relations ── */}
          {step === 3 && (
            <>
              <div className="form-row">
                <span>Suggest relations</span>
                <p className="arc-hint">
                  Asks the model about one character at a time, then merges the
                  batches. Suggestions join the lists below for review - nothing is
                  written until you finish.
                </p>
                <ArcSuggestButtons
                  party={party.filter(p => partyIds.has(p.id))}
                  npcs={npcs.filter(n => npcIds.has(n.id))}
                  context={overallPlot || body}
                  onSuggested={applySuggested}
                />
              </div>
              <div className="form-row">
                <span>Party relationships ({partyRels.filter(r => r.accepted).length})</span>
                <RelationReview
                  rels={partyRels}
                  nameOf={nameOf}
                  onToggle={i => setPartyRels(rs =>
                    rs.map((r, j) => (j === i ? { ...r, accepted: !r.accepted } : r)))}
                />
              </div>
              <div className="form-row">
                <span>NPC relationships ({npcRels.filter(r => r.accepted).length})</span>
                <RelationReview
                  rels={npcRels}
                  nameOf={nameOf}
                  onToggle={i => setNpcRels(rs =>
                    rs.map((r, j) => (j === i ? { ...r, accepted: !r.accepted } : r)))}
                />
              </div>
            </>
          )}

          {/* ── 5. Review ── */}
          {step === 4 && (
            <div className="arc-review">
              <h4>{title || '(untitled arc)'}</h4>
              <dl className="arc-summary">
                <dt>Campaign</dt><dd>{campaignName ?? '-'}</dd>
                <dt>Levels</dt><dd>{levelRange || '-'}</dd>
                <dt>Target stories</dt><dd>{targetStories || '-'}</dd>
                <dt>Antagonist faction</dt>
                <dd>{factions.find(f => f.id === factionId)?.name ?? '-'}</dd>
                <dt>Party</dt><dd>{partyIds.size}</dd>
                <dt>NPCs</dt><dd>{npcIds.size}</dd>
                <dt>Party relations</dt><dd>{partyRels.filter(r => r.accepted).length}</dd>
                <dt>NPC relations</dt><dd>{npcRels.filter(r => r.accepted).length}</dd>
              </dl>
              {saved && (
                <p className="arc-saved">
                  Saved. The arc is on {campaignName} and stories can now be attached to it.
                </p>
              )}
            </div>
          )}

          <div className="wizard-foot">
            <button
              type="button"
              className="ghost-btn"
              disabled={step === 0 || busy}
              onClick={() => setStep(s => Math.max(s - 1, 0))}
            >
              Back
            </button>
            {step < STEPS.length - 1 ? (
              <button
                type="button"
                className="primary-btn"
                disabled={!canAdvance || busy}
                onClick={() => { void advance(); }}
              >
                {busy ? <Spinner label="Saving" /> : <Icon name="sparkle" size={11} />}
                {step === 0 && !arcId ? ' Create arc' : ' Save and continue'}
              </button>
            ) : (
              <button
                type="button"
                className="primary-btn"
                disabled={busy || !arcId}
                onClick={() => { void finish(); }}
              >
                {busy ? <Spinner label="Saving" /> : null} Finish
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
