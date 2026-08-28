/**
 * Wizard for the story Generate image button.
 *
 * Extract events, pick one, confirm who is in the shot, queue the render,
 * then accept or discard. All heavy work is a queued job.
 */

import * as React from 'react';
import { AiTag, Icon, Spinner } from './atoms';
import {
  enqueueJob, fetchJob, isFinished, jobResult, resolveJob, useJobPolling, JOB_TYPES,
  type AiJob,
} from '../../utils/aiJobs';
import {
  eventsFromResult, toPeoplePayload, toRosterPayload,
  type StoryEventChoice, type StoryEventsJobResult,
  type StoryIllustrationJobResult, type StoryImageRosterPerson,
} from '../../utils/storyImage';

export interface StoryImageWizardProps {
  storyId: string;
  storyTitle: string;
  roster: StoryImageRosterPerson[];
  /** Character ids present in this story; empty means the whole party. */
  presentIds?: string[];
  /** Job the activity bar sent us back to, still running or awaiting review. */
  reviewJobId?: string | null;
  /** Icon-only trigger for the public story sidebar. */
  compact?: boolean;
}

type Phase = 'idle' | 'events' | 'pick' | 'cast' | 'render' | 'review';

export function StoryImageWizard({
  storyId, storyTitle, roster, presentIds = [], reviewJobId = null, compact = false,
}: StoryImageWizardProps): React.ReactElement {
  const [open, setOpen] = React.useState(false);
  const [phase, setPhase] = React.useState<Phase>('idle');
  const [error, setError] = React.useState<string | null>(null);
  const [eventsJobId, setEventsJobId] = React.useState<string | null>(null);
  const [renderJobId, setRenderJobId] = React.useState<string | null>(null);
  const [events, setEvents] = React.useState<StoryEventChoice[]>([]);
  const [picked, setPicked] = React.useState<StoryEventChoice | null>(null);
  const [inShot, setInShot] = React.useState<Set<string>>(new Set());
  const [likeness, setLikeness] = React.useState<Set<string>>(new Set());
  const [candidate, setCandidate] = React.useState<StoryIllustrationJobResult & { jobId: string } | null>(null);
  const [reviewing, setReviewing] = React.useState<'accept' | 'discard' | null>(null);

  const defaultShot = React.useMemo(() => {
    const present = new Set(presentIds);
    const pcs = roster.filter(person => !person.isNpc);
    const chosen = present.size > 0
      ? pcs.filter(person => present.has(person.characterId))
      : pcs;
    return new Set(chosen.map(person => person.characterId));
  }, [roster, presentIds]);

  const onEventsDone = React.useCallback((job: AiJob) => {
    if (job.state === 'failure') {
      setError(job.message ?? 'Event extraction failed.');
      setPhase('idle');
      setEventsJobId(null);
      return;
    }
    const result = jobResult<StoryEventsJobResult>(job);
    const found = eventsFromResult(result);
    if (found.length === 0) {
      setError('No illustratable events were found in this story.');
      setPhase('idle');
      return;
    }
    setEvents(found);
    setPhase('pick');
    if (job.id) {
      void resolveJob(job.id, true).catch(() => undefined);
    }
  }, []);

  const onRenderDone = React.useCallback((job: AiJob) => {
    if (job.state === 'failure') {
      setError(job.message ?? 'Scene render failed.');
      setPhase('cast');
      setRenderJobId(null);
      return;
    }
    const result = jobResult<StoryIllustrationJobResult>(job);
    if (result == null || result.review !== 'pending') {
      setError('The render finished but returned nothing to review.');
      setPhase('cast');
      return;
    }
    setCandidate({ ...result, jobId: job.id });
    setPhase('review');
  }, []);

  useJobPolling(eventsJobId, onEventsDone);
  useJobPolling(renderJobId, onRenderDone);

  /* Pick up a job the activity bar sent us to, whether it is still running or
     already finished and waiting on a decision. */
  React.useEffect(() => {
    if (!reviewJobId) return undefined;
    let cancelled = false;
    void (async (): Promise<void> => {
      const job = await fetchJob(reviewJobId);
      if (cancelled || job === null) return;
      const jobStory = job.subjectId
        ?? jobResult<StoryEventsJobResult | StoryIllustrationJobResult>(job)?.storyId
        ?? null;
      if (jobStory != null && jobStory !== storyId) return;
      setOpen(true);
      setError(null);
      if (job.type === JOB_TYPES.storyEvents) {
        if (!isFinished(job)) {
          setPhase('events');
          setEventsJobId(job.id);
          return;
        }
        onEventsDone(job);
        return;
      }
      if (job.type === JOB_TYPES.illustration) {
        if (!isFinished(job)) {
          setPhase('render');
          setRenderJobId(job.id);
          return;
        }
        onRenderDone(job);
      }
    })();
    return () => { cancelled = true; };
  }, [reviewJobId, storyId, onEventsDone, onRenderDone]);

  const startEvents = async (): Promise<void> => {
    setError(null);
    setCandidate(null);
    setPicked(null);
    setOpen(true);
    setPhase('events');
    try {
      const job = await enqueueJob(
        JOB_TYPES.storyEvents,
        `Events: ${storyTitle}`,
        { storyId, roster: toRosterPayload(roster) },
      );
      setEventsJobId(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not queue event extraction.');
      setPhase('idle');
    }
  };

  const chooseEvent = (event: StoryEventChoice): void => {
    setPicked(event);
    setInShot(new Set(defaultShot));
    const withPortrait = new Set(
      roster
        .filter(person => defaultShot.has(person.characterId) && person.portraitUrl)
        .map(person => person.characterId),
    );
    setLikeness(withPortrait);
    setPhase('cast');
  };

  const toggle = (
    set: Set<string>,
    setter: React.Dispatch<React.SetStateAction<Set<string>>>,
    id: string,
  ): void => {
    const next = new Set(set);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setter(next);
  };

  const startRender = async (): Promise<void> => {
    if (picked == null) return;
    setError(null);
    setPhase('render');
    const selected = roster.filter(person => inShot.has(person.characterId));
    try {
      const job = await enqueueJob(
        JOB_TYPES.illustration,
        `Scene: ${picked.title}`,
        {
          storyId,
          title: picked.title,
          excerpt: picked.excerpt,
          roster: toRosterPayload(roster),
          people: toPeoplePayload(selected, likeness),
        },
      );
      setRenderJobId(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not queue the illustration.');
      setPhase('cast');
    }
  };

  const review = async (accepted: boolean): Promise<void> => {
    if (candidate == null) return;
    setReviewing(accepted ? 'accept' : 'discard');
    try {
      await resolveJob(candidate.jobId, accepted);
      setCandidate(null);
      setOpen(false);
      setPhase('idle');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not record the decision.');
    } finally {
      setReviewing(null);
    }
  };

  const running = phase === 'events' || phase === 'render';
  const label = phase === 'events' ? 'Finding events...'
    : phase === 'render' ? 'Conjuring...'
      : 'Generate image';

  return (
    <div className={`story-image-wizard${compact ? ' story-image-wizard--compact' : ''}`}>
      <button
        type="button"
        className={`big-medallion big-medallion--ai${compact ? ' big-medallion--compact' : ''}${running ? ' state-running' : ''}${phase === 'review' ? ' state-done' : ''}`}
        onClick={() => { if (!running) void startEvents(); }}
        disabled={running}
        title={label}
      >
        <AiTag label="" />
        <Icon name="image" size={compact ? 16 : 14} />
        {!compact && <span className="medallion-label">{label}</span>}
      </button>

      {open && (
        <div className="story-image-panel" role="dialog" aria-label="Generate a scene illustration">
          {error && <p className="arc-error">{error}</p>}

          {phase === 'events' && <Spinner label="Finding events" />}

          {phase === 'pick' && (
            <>
              <p className="story-image-lead">Pick the moment to illustrate.</p>
              <ul className="arc-picker">
                {events.map(event => (
                  <li key={event.title}>
                    <button type="button" className="story-image-event" onClick={() => chooseEvent(event)}>
                      <span className="arc-picker-name">{event.title}</span>
                      <span className="arc-picker-meta">{event.oneLine}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}

          {phase === 'cast' && picked && (
            <>
              <p className="story-image-lead">
                {picked.title}. Who is in this shot? Likeness uses a stored
                portrait; everyone else is described in the prompt.
              </p>
              <ul className="arc-picker">
                {roster.map(person => (
                  <li key={person.characterId || person.name}>
                    <label>
                      <input
                        type="checkbox"
                        checked={inShot.has(person.characterId)}
                        onChange={() => toggle(inShot, setInShot, person.characterId)}
                      />
                      {person.portraitUrl
                        ? <img src={person.portraitUrl} alt="" className="story-image-thumb" />
                        : <span className="story-image-thumb story-image-thumb--empty" />}
                      <span className="arc-picker-name">{person.name}</span>
                      <span className="arc-picker-meta">{person.isNpc ? 'NPC' : 'PC'}</span>
                    </label>
                    {inShot.has(person.characterId) && person.portraitUrl && (
                      <label className="story-image-likeness">
                        <input
                          type="checkbox"
                          checked={likeness.has(person.characterId)}
                          onChange={() => toggle(likeness, setLikeness, person.characterId)}
                        />
                        Use likeness
                      </label>
                    )}
                  </li>
                ))}
              </ul>
              <div className="story-image-actions">
                <button type="button" className="ghost-btn" onClick={() => setPhase('pick')}>Back</button>
                <button type="button" className="ghost-btn" onClick={() => void startRender()}>
                  Queue illustration
                </button>
              </div>
            </>
          )}

          {phase === 'render' && <Spinner label="Rendering on the host queue" />}

          {phase === 'review' && candidate && (
            <div className="portrait-review">
              <span className="portrait-review-tag">Not attached yet</span>
              {candidate.imageUrl && (
                <img src={candidate.imageUrl} alt={candidate.alt} className="story-image-preview" />
              )}
              <p className="portrait-review-note">
                {candidate.usedIpadapter
                  ? `Likeness from ${candidate.usedIpadapter} portrait(s)`
                  : 'No IPAdapter likeness applied'}
                {candidate.swappedFaces && candidate.swappedFaces.length > 0
                  ? `; swapped ${candidate.swappedFaces.join(', ')}`
                  : ''}.
                Nothing is stored on the story until you accept.
              </p>
              <div className="portrait-review-actions">
                <button type="button" className="ghost-btn" disabled={reviewing !== null} onClick={() => void review(true)}>
                  {reviewing === 'accept' ? 'Attaching…' : 'Accept illustration'}
                </button>
                <button type="button" className="ghost-btn" disabled={reviewing !== null} onClick={() => void review(false)}>
                  Discard
                </button>
              </div>
            </div>
          )}

          {phase !== 'events' && phase !== 'render' && (
            <button type="button" className="story-image-close" onClick={() => { setOpen(false); setPhase('idle'); }}>
              Close
            </button>
          )}
        </div>
      )}
    </div>
  );
}
