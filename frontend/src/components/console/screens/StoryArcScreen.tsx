/**
 * StoryArcScreen — `stories/arcs`.
 *
 * The arc overview: one campaign's story arcs, what each one is made of, and
 * the full relationship web with inline editing. This is the authoring surface
 * for relations; a character sheet's Relations tab is the same data seen from
 * one character's side.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, storyArcsForCampaign, storiesForCampaign } from '../ConsoleContext';
import type { DrupalStoryArc } from '../ConsoleContext';
import { Icon, Spinner } from '../atoms';
import { ArcRelationsTable } from '../ArcRelationsTable';
import { ArcSuggestButtons } from '../ArcSuggestButtons';
import { ArcBackfillPanel } from '../ArcBackfillPanel';
import { useArcRelations } from '../../../utils/arcRelationsEdit';
import { partyRoster, npcRoster } from '../../../utils/arcRoster';
import { fetchJob, jobResult, resolveJob, JOB_TYPES } from '../../../utils/aiJobs';
import {
  toArcDraft,
  type ArcDraft,
  type DiscoveredNpc,
  type RawArcDraft,
} from '../../../utils/arcBackfill';
import type { DrupalArcRelation } from '../ConsoleContext';

function nameFor(ids: string[], all: Array<{ id: string; title: string }>): string[] {
  return ids
    .map(id => all.find(c => c.id === id)?.title)
    .filter((t): t is string => Boolean(t));
}

export function StoryArcScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined)
    ?? data.campaigns[0]?.name ?? null;

  const arcs = React.useMemo(
    () => (campaignName ? storyArcsForCampaign(data, campaignName) : []),
    [data, campaignName],
  );

  const campaign = data.campaigns.find(c => c.name === campaignName) ?? null;

  /* Every story on the campaign, not just an arc's own: the backfill reads the
     whole play history, which is what there is before any arc exists. */
  const campaignStories = React.useMemo(
    () => (campaignName ? storiesForCampaign(data, campaignName) : [])
      .map(s => ({ id: s.id, title: s.title, storyNumber: s.storyNumber })),
    [data, campaignName],
  );

  const selectedId = typeof ctx.arcId === 'string' ? ctx.arcId : null;
  const arc: DrupalStoryArc | null =
    arcs.find(a => a.id === selectedId) ?? arcs[0] ?? null;

  const party = React.useMemo(() => partyRoster(data, campaignName), [data, campaignName]);
  const npcs  = React.useMemo(() => npcRoster(data, campaignName), [data, campaignName]);
  const everyone = React.useMemo(() => [...party, ...npcs], [party, npcs]);

  const rel = useArcRelations(arc);

  /* Suggestion runs over the arc's own roster, not the whole campaign: the
     arc's party and its curated NPCs are who the bonds can be between. */
  const arcParty = React.useMemo(
    () => party.filter(p => arc?.partyIds.includes(p.id)),
    [party, arc],
  );
  const arcNpcs = React.useMemo(
    () => npcs.filter(n => arc?.npcIds.includes(n.id)),
    [npcs, arc],
  );

  const applySuggestions = React.useCallback(
    (side: 'party' | 'npc', relations: typeof rel.party[number][] | Parameters<typeof rel.add>[1][]): void => {
      for (const relation of relations) {
        rel.add(side, relation);
      }
    },
    [rel],
  );

  const stories = React.useMemo(
    () => data.stories.filter(s => arc && s.storyArcId === arc.id),
    [data.stories, arc],
  );

  /* A queued run stores its suggestions on the job rather than writing them,
     so an unattended run cannot overwrite hand-written bonds. Picking the job
     up loads them into the tables for the same accept/reject review. */
  const reviewJobId = typeof ctx.reviewJobId === 'string' ? ctx.reviewJobId : null;
  const [picked, setPicked] = React.useState<string | null>(null);
  const [jobNotice, setJobNotice] = React.useState<string | null>(null);
  const [queuedDraft, setQueuedDraft] = React.useState<ArcDraft | null>(null);
  const [queuedCast, setQueuedCast] = React.useState<DiscoveredNpc[]>([]);

  /* The backfill belongs on the empty state, but a queued run can also finish
     after an arc exists - following that job here must not drop its proposal. */
  const showBackfill = arcs.length === 0 || queuedDraft !== null;

  React.useEffect(() => {
    if (!reviewJobId || picked === reviewJobId) {
      return;
    }
    setPicked(reviewJobId);
    void (async () => {
      const job = await fetchJob(reviewJobId);

      /* A backfill job carries a whole arc proposal, not relations: it goes to
         the review form, which is the only thing that can create the arc. */
      if (job?.type === JOB_TYPES.backfill) {
        const backfill = jobResult<{
          draft?: RawArcDraft | null;
          cast?:  DiscoveredNpc[];
        }>(job);
        const draft = toArcDraft(backfill?.draft);
        if (draft === null) {
          setJobNotice('That run proposed no arc.');
          return;
        }
        setQueuedDraft(draft);
        setQueuedCast(backfill?.cast ?? []);
        setJobNotice('Loaded the proposed arc from the queued run. Edit it, then accept.');
        await resolveJob(reviewJobId, true);
        return;
      }

      const result = jobResult<{
        side?: 'party' | 'npc';
        suggested?: DrupalArcRelation[];
      }>(job);
      const suggested = result?.suggested ?? [];
      if (suggested.length === 0) {
        setJobNotice('That run produced no suggestions.');
        return;
      }
      for (const relation of suggested) {
        rel.add(result?.side === 'npc' ? 'npc' : 'party', relation);
      }
      setJobNotice(
        `Loaded ${suggested.length} suggestion(s) from the queued run. Review, then save.`,
      );
      await resolveJob(reviewJobId, true);
    })();
  }, [reviewJobId, picked, rel]);

  const addRow = (side: 'party' | 'npc'): void => {
    rel.add(side, {
      sourceId: null, sourceName: null,
      targetId: null, targetName: null,
      type: '', tier: side === 'party' ? 2 : 1, note: '',
    });
  };

  return (
    <div className="screen-storyarc">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Story arcs</span>
          <h2>{campaignName ?? 'No campaign selected'}</h2>
          <p className="screen-blurb">
            The plans this campaign&apos;s stories are written against, and the
            relationship web inside each one.
          </p>
        </div>
      </header>

      {showBackfill && campaign && (
        <section className="arc-prose">
          <h4>
            {arcs.length === 0
              ? 'No arcs on this campaign yet'
              : 'Proposed arc from a queued run'}
          </h4>
          <ArcBackfillPanel
            campaignId={campaign.id}
            campaignName={campaign.name}
            stories={campaignStories}
            party={party}
            npcs={npcs}
            incoming={queuedDraft}
            incomingCast={queuedCast}
          />
          {jobNotice && <p className="arc-saved">{jobNotice}</p>}
          {arcs.length === 0 && (
            <p className="arc-hint">
              Or plan one from scratch in &quot;Create New Story Arc&quot;.
            </p>
          )}
        </section>
      )}

      {arcs.length === 0 ? (
        campaign ? null : <p className="arc-empty">Select a campaign first.</p>
      ) : (
        <div className="arc-layout">
          <aside className="arc-list">
            {arcs.map(a => (
              <button
                key={a.id}
                type="button"
                className={`arc-list-item${a.id === arc?.id ? ' active' : ''}`}
                onClick={() => setCtx({ ...ctx, arcId: a.id })}
              >
                <strong>{a.title}</strong>
                <span>
                  {[a.levelRange ? `Levels ${a.levelRange}` : null,
                    a.faction,
                    `${a.partyRelations.length + a.npcRelations.length} relations`]
                    .filter(Boolean).join(' · ')}
                </span>
              </button>
            ))}
          </aside>

          {arc && (
            <div className="arc-detail">
              <div className="arc-detail-head">
                <h3>{arc.title}</h3>
                {/* Gatsby builds pages for characters, stories, monsters and
                    items - not story arcs, so arc.path is a Drupal alias with
                    no Gatsby route behind it. Link where it actually resolves. */}
                {arc.path && (
                  <a
                    href={drupalAdminUrl(arc.path)}
                    className="ghost-btn"
                    style={{ textDecoration: 'none' }}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Icon name="scroll" size={11} /> Open in Drupal
                  </a>
                )}
              </div>

              <dl className="arc-summary">
                <dt>Levels</dt><dd>{arc.levelRange || '-'}</dd>
                <dt>Target stories</dt>
                <dd>{arc.targetStories ?? '-'} ({stories.length} written)</dd>
                <dt>Antagonist faction</dt><dd>{arc.faction ?? '-'}</dd>
                <dt>Party</dt>
                <dd>{nameFor(arc.partyIds, party).join(', ') || '-'}</dd>
                <dt>NPCs</dt>
                <dd>{nameFor(arc.npcIds, npcs).join(', ') || '-'}</dd>
              </dl>

              {arc.body && (
                <section className="arc-prose">
                  <h4>Premise</h4>
                  <p>{arc.body}</p>
                </section>
              )}
              {arc.overallPlot && (
                <section className="arc-prose">
                  <h4>Act spine</h4>
                  <pre>{arc.overallPlot}</pre>
                </section>
              )}

              {stories.length > 0 && (
                <section className="arc-prose">
                  <h4>Stories in this arc</h4>
                  <ul className="arc-story-list">
                    {stories.map(s => (
                      <li key={s.id}>
                        <span className="arc-story-num">{s.storyNumber ?? '-'}</span>
                        {s.path ? <Link to={s.path}>{s.title}</Link> : s.title}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section className="arc-prose">
                <h4>Suggest relations</h4>
                <p className="arc-hint">
                  Asks the model about one character at a time against the rest of
                  the arc&apos;s roster, then merges the batches. Suggestions are
                  added to the tables below for review - nothing is written until
                  you save.
                </p>
                <ArcSuggestButtons
                  party={arcParty}
                  npcs={arcNpcs}
                  context={arc.overallPlot ?? arc.body ?? ''}
                  onSuggested={applySuggestions}
                  arcId={arc.id}
                />
                {jobNotice && <p className="arc-saved">{jobNotice}</p>}
              </section>

              <section className="arc-prose">
                <h4>Party relationships</h4>
                <ArcRelationsTable
                  side="party"
                  rows={rel.party}
                  roster={party}
                  onUpdate={rel.update}
                  onRemove={rel.remove}
                  onAdd={addRow}
                  empty="No bonds recorded inside the party yet."
                />
              </section>

              <section className="arc-prose">
                <h4>NPC relationships</h4>
                <ArcRelationsTable
                  side="npc"
                  rows={rel.npc}
                  roster={everyone}
                  onUpdate={rel.update}
                  onRemove={rel.remove}
                  onAdd={addRow}
                  empty="No connections recorded between the party and this arc's NPCs yet."
                />
              </section>

              {rel.error && <p className="arc-error">{rel.error}</p>}
              {rel.notice && <p className="arc-saved">{rel.notice}</p>}

              <div className="wizard-foot">
                <button
                  type="button"
                  className="primary-btn"
                  disabled={rel.saving}
                  onClick={() => { void rel.save(); }}
                >
                  {rel.saving ? <Spinner label="Saving" /> : <Icon name="scroll" size={11} />}
                  {rel.saving ? ' Saving' : ' Save relations'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
