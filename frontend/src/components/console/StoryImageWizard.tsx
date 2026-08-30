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
  ANGLE_OPTIONS, DEFAULT_ANGLE, DEFAULT_SHOT, SHOT_OPTIONS,
  eventsFromResult, passageTitle, passagesFromBody, toPeoplePayload, toRosterPayload,
  type StoryEventChoice, type StoryEventsJobResult,
  type StoryIllustrationJobResult, type StoryImageRosterPerson,
} from '../../utils/storyImage';

export interface StoryImageWizardProps {
  storyId: string;
  storyTitle: string;
  roster: StoryImageRosterPerson[];
  /** Character ids present in this story; empty means the whole party. */
  presentIds?: string[];
  /** The story body, so a passage can be picked without asking the model. */
  storyBody?: string;
  /** Job the activity bar sent us back to, still running or awaiting review. */
  reviewJobId?: string | null;
  /** Icon-only trigger for the public story sidebar. */
  compact?: boolean;
}

type Phase = 'idle' | 'events' | 'pick' | 'manual' | 'cast' | 'render' | 'review';

/**
 * Say who got a likeness, and by which of the two mechanisms.
 *
 * Reporting a count for one path and names for the other read as a
 * contradiction - "2 portraits" beside four names looks like two people went
 * missing, when in fact the two leads simply went unnamed.
 *
 * @param candidate The finished render awaiting review.
 * @returns One sentence naming both groups, or saying there were none.
 */
function likenessSummary(candidate: StoryIllustrationJobResult): string {
  const leads = candidate.leadFaces ?? [];
  const swapped = candidate.swappedFaces ?? [];
  const total = leads.length + swapped.length;
  if (total === 0) return 'No likeness applied - everyone is described in the prompt.';
  const parts: string[] = [];
  if (leads.length > 0) parts.push(`${leads.join(', ')} from portrait`);
  if (swapped.length > 0) parts.push(`${swapped.join(', ')} by face swap`);
  return `Likeness for ${total}: ${parts.join('; ')}.`;
}

/**
 * Whether a roster member can drive likeness.
 *
 * Likeness conditions the render on a stored portrait, so a character without
 * one has nothing to condition on and must not be offered the choice.
 *
 * @param person A roster member.
 * @returns True when a portrait URL is present.
 */
function hasPortrait(person: StoryImageRosterPerson): boolean {
  return person.portraitUrl.trim() !== '';
}

export function StoryImageWizard({
  storyId, storyTitle, roster, presentIds = [], reviewJobId = null, compact = false,
  storyBody = '',
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
  const [custom, setCustom] = React.useState('');
  const [shot, setShot] = React.useState(DEFAULT_SHOT);
  const [angle, setAngle] = React.useState(DEFAULT_ANGLE);

  const passages = React.useMemo(() => passagesFromBody(storyBody), [storyBody]);
  const pcs = React.useMemo(() => roster.filter(person => !person.isNpc), [roster]);
  const npcs = React.useMemo(() => roster.filter(person => person.isNpc), [roster]);

  const defaultShot = React.useMemo(() => {
    const present = new Set(presentIds);
    const chosen = present.size > 0
      ? pcs.filter(person => present.has(person.characterId))
      : pcs;
    return new Set(chosen.map(person => person.characterId));
  }, [pcs, presentIds]);

  const onEventsDone = React.useCallback((job: AiJob) => {
    if (job.state === 'failure') {
      setError(job.message ?? 'Event extraction failed.');
      setEvents([]);
      setPhase('manual');
      setEventsJobId(null);
      return;
    }
    const result = jobResult<StoryEventsJobResult>(job);
    const found = eventsFromResult(result);
    setEvents(found);
    // A model that proposes nothing hands the choice back; it does not end it.
    setPhase(found.length === 0 ? 'manual' : 'pick');
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
        .filter(person => defaultShot.has(person.characterId) && hasPortrait(person))
        .map(person => person.characterId),
    );
    setLikeness(withPortrait);
    setPhase('cast');
  };

  const chooseExcerpt = (excerpt: string): void => {
    chooseEvent({ title: passageTitle(excerpt, storyTitle), oneLine: '', excerpt });
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
          shot,
          angle,
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
              <div className="story-image-actions">
                <button type="button" className="ghost-btn" onClick={() => setPhase('manual')}>
                  None of these - pick a passage myself
                </button>
              </div>
            </>
          )}

          {phase === 'manual' && (
            <>
              <p className="story-image-lead">
                {events.length > 0
                  ? 'Pick any passage of the story instead.'
                  : 'Nothing was proposed for you. Pick the passage to illustrate.'}
              </p>
              <ul className="arc-picker">
                {passages.map(passage => (
                  <li key={passage.slice(0, 60)}>
                    <button
                      type="button"
                      className="story-image-event"
                      onClick={() => chooseExcerpt(passage)}
                    >
                      <span className="arc-picker-meta">{passage}</span>
                    </button>
                  </li>
                ))}
              </ul>
              <textarea
                className="arc-textarea"
                value={custom}
                onChange={event => setCustom(event.target.value)}
                placeholder="...or describe the moment in your own words"
                rows={3}
              />
              <div className="story-image-actions">
                {events.length > 0 && (
                  <button type="button" className="ghost-btn" onClick={() => setPhase('pick')}>
                    Back
                  </button>
                )}
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={custom.trim() === ''}
                  onClick={() => chooseExcerpt(custom.trim())}
                >
                  Use this text
                </button>
              </div>
            </>
          )}

          {phase === 'cast' && picked && (
            <>
              <p className="story-image-lead">
                {picked.title}. Who is in this shot? Likeness uses a stored
                portrait; everyone else is described in the prompt.
              </p>
              {([['Player characters', pcs], ['NPCs', npcs]] as const)
                .filter(([, group]) => group.length > 0)
                .map(([heading, group]) => (
                  <React.Fragment key={heading}>
                    <p className="story-image-group">{heading}</p>
                    <ul className="arc-picker">
                      {group.map(person => (
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
                          </label>
                          {inShot.has(person.characterId) && (
                            hasPortrait(person)
                              ? (
                                <label className="story-image-likeness">
                                  <input
                                    type="checkbox"
                                    checked={likeness.has(person.characterId)}
                                    onChange={() => toggle(likeness, setLikeness, person.characterId)}
                                  />
                                  Use likeness
                                </label>
                              )
                              : (
                                <span className="story-image-likeness story-image-likeness--none">
                                  No portrait - described in the prompt only
                                </span>
                              )
                          )}
                        </li>
                      ))}
                    </ul>
                  </React.Fragment>
                ))}
              <p className="story-image-group">Framing</p>
              <div className="story-image-framing">
                <label>
                  Shot
                  <select
                    className="arc-select"
                    value={shot}
                    onChange={event => setShot(event.target.value)}
                  >
                    {SHOT_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Camera
                  <select
                    className="arc-select"
                    value={angle}
                    onChange={event => setAngle(event.target.value)}
                  >
                    {ANGLE_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>
              {angle === 'behind' && likeness.size > 0 && (
                <p className="story-image-likeness--none">
                  Faces are not visible from behind, so no likeness will apply.
                </p>
              )}
              <div className="story-image-actions">
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => setPhase(events.length > 0 ? 'pick' : 'manual')}
                >
                  Back
                </button>
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
                {likenessSummary(candidate)}{' '}
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
