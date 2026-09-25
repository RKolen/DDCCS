/**
 * Wizard for the story Generate image button.
 *
 * Extract events, pick one, confirm who is in the shot, queue the render,
 * then accept or discard. All heavy work is a queued job.
 */

import * as React from 'react';
import { AiTag, Icon, Spinner } from './atoms';
import StagingCanvas from './StagingCanvas';
import {
  enqueueJob, fetchJob, isFinished, jobResult, resolveJob, useJobPolling, JOB_TYPES,
  type AiJob,
} from '../../utils/aiJobs';
import {
  ANGLE_OPTIONS, DEFAULT_ANGLE, DEFAULT_MOOD, DEFAULT_SETTING, DEFAULT_SHOT,
  DEFAULT_TOWARD, FACING_OPTIONS, MAX_ACTION_CHARS, MOOD_OPTIONS,
  POSE_OPTIONS, prefersRegions, reorderTo, TOWARD_OPTIONS,
  SETTING_OPTIONS, SHOT_OPTIONS, type StagePlacement, toPlacementsPayload,
  eventsFromResult, passageTitle, passagesFromBody, toPeoplePayload, toRosterPayload,
  type StoryEventChoice, type StoryEventsJobResult,
  type StoryIllustrationJobResult, type StoryImageRosterPerson,
} from '../../utils/storyImage';
import {
  clearSetup, loadSetup, saveSetup, setupSummary, type StoryImageSetup,
} from '../../utils/storyImageSetup';

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
  // Region mode renders each character on their own canvas from their own
  // portrait: there is no two-lead cap and nothing is swapped. Describing it
  // in the whole-scene vocabulary named two people as favoured and told the
  // operator four faces were swapped in when none were.
  if (candidate.regions) {
    return `Each of the ${leads.length} rendered from their own portrait: ${leads.join(', ')}.`;
  }
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

interface PersonSelectProps {
  label: string;
  value: string;
  options: ReadonlyArray<{ value: string; label: string }>;
  onPick: (value: string) => void;
}

/**
 * One labelled select in a character's row of staging controls.
 *
 * @param props Label, current value, the options, and what to do with a pick.
 * @returns The labelled select.
 */
function PersonSelect({ label, value, options, onPick }: PersonSelectProps): React.ReactElement {
  return (
    <label className="story-image-action">
      {label}
      <select
        className="arc-select"
        value={value}
        onChange={event => onPick(event.target.value)}
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}

/** Turns with a left and a right. Front and away read the same either way. */
const HANDED = new Set(['three_quarter', 'side']);

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
  const [setting, setSetting] = React.useState(DEFAULT_SETTING);
  const [mood, setMood] = React.useState(DEFAULT_MOOD);
  // Per character, keyed by Drupal id. Absent means "whatever the shot
  // analysis wrote", so an operator types only where they disagree.
  const [actions, setActions] = React.useState<Map<string, string>>(new Map());
  // null means "follow the cast size". Region mode is the right default for
  // more than two people and the wrong one for a portrait-ish two-hander, so
  // it tracks the cast until the operator says otherwise.
  const [regionsChoice, setRegionsChoice] = React.useState<boolean | null>(null);
  const regions = regionsChoice ?? prefersRegions(inShot.size);
  // Per character. The Camera select above is where the lens is; this is
  // which way each person is turned, which is the half that was missing.
  const [facings, setFacings] = React.useState<Map<string, string>>(new Map());
  // The stance itself. "Doing" only ever reached the prompt, and a skeleton
  // drawn standing beats the word "walking": ControlNet obeys geometry.
  const [poses, setPoses] = React.useState<Map<string, string>>(new Map());
  // Which way a turned figure points. Facing says how far, not which way, so
  // a cast all set to profile faced the same way.
  const [towards, setTowards] = React.useState<Map<string, string>>(new Map());
  // Where everyone stands. Seeded evenly, then dragged on the skeleton.
  const [placements, setPlacements] = React.useState<StagePlacement[]>([]);
  // Front to back, by character id. Who wins an overlap is its own control:
  // depth also sets apparent size, so dragging a small character forward to
  // stop them being swallowed made everyone else's distance wrong.
  const [order, setOrder] = React.useState<string[]>([]);
  // The setup the last render was queued with. Read after mount, never during
  // render: Gatsby builds these pages in Node, where there is no localStorage.
  const [saved, setSaved] = React.useState<StoryImageSetup | null>(null);

  React.useEffect(() => { setSaved(loadSetup(storyId)); }, [storyId]);

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

  /* Straight to the passage list. Extraction is a minutes-long Ollama job,
     and an operator who already knows which paragraph they want dismisses it
     with "None of these" the moment it finishes. */
  const startPassages = (): void => {
    setError(null);
    setCandidate(null);
    setPicked(null);
    setEvents([]);
    setOpen(true);
    setPhase('manual');
  };

  /* Reinstate the last queued setup and land on the cast step, so a second
     attempt at the same scene is two clicks rather than a refilled form. */
  const repeatLast = (): void => {
    if (saved == null) return;
    setError(null);
    setCandidate(null);
    setEvents([]);
    setPicked({ title: saved.title, oneLine: '', excerpt: saved.excerpt });
    setInShot(new Set(saved.inShot));
    setLikeness(new Set(saved.likeness));
    setFacings(new Map(saved.facings));
    setPoses(new Map(saved.poses));
    setTowards(new Map(saved.towards));
    setOrder(saved.order);
    setActions(new Map(saved.actions));
    setShot(saved.shot);
    setAngle(saved.angle);
    setSetting(saved.setting);
    setMood(saved.mood);
    setRegionsChoice(saved.regionsChoice);
    setPlacements(saved.placements);
    setOpen(true);
    setPhase('cast');
  };

  const forgetLast = (): void => {
    clearSetup(storyId);
    setSaved(null);
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

  const setFor = (
    setter: React.Dispatch<React.SetStateAction<Map<string, string>>>,
    id: string,
    value: string,
  ): void => {
    setter(previous => {
      const next = new Map(previous);
      next.set(id, value);
      return next;
    });
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
    const setup: StoryImageSetup = {
      title: picked.title,
      excerpt: picked.excerpt,
      inShot: selected.map(person => person.characterId),
      likeness: [...likeness],
      facings: [...facings],
      poses: [...poses],
      towards: [...towards],
      order,
      actions: [...actions],
      shot, angle, setting, mood, regionsChoice, placements,
    };
    saveSetup(storyId, setup);
    setSaved(setup);
    try {
      const job = await enqueueJob(
        JOB_TYPES.illustration,
        `Scene: ${picked.title}`,
        {
          storyId,
          title: picked.title,
          excerpt: picked.excerpt,
          roster: toRosterPayload(roster),
          people: toPeoplePayload(selected, likeness, actions),
          placements,
          shot,
          angle,
          setting,
          mood,
          regions,
        },
      );
      setRenderJobId(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not queue the illustration.');
      setPhase('cast');
    }
  };

  // Re-seed when the cast changes, but keep where anyone already standing
  // was put: losing a staging because one more person was ticked would make
  // the editor useless for exactly the casts that need it.
  const castKey = roster
    .filter(person => inShot.has(person.characterId))
    .map(person => person.characterId).join(',');
  React.useEffect(() => {
    const selected = roster.filter(person => inShot.has(person.characterId));
    const ids = selected.map(person => person.characterId);
    // Keep the order anyone already has; newcomers join at the back.
    setOrder(previous => [
      ...previous.filter(id => ids.includes(id)),
      ...ids.filter(id => !previous.includes(id)),
    ]);
    setPlacements(previous => {
      const held = new Map(previous.map(row => [row.name, row]));
      return toPlacementsPayload(selected, facings, poses, towards, order).map(row => {
        const before = held.get(row.name);
        // Only where somebody stands is kept: pose, facing and direction are
        // owned by the selects above, so a rebuild must not restore the
        // values they have just replaced.
        return before == null
          ? row
          : { ...row, lateral: before.lateral, depth: before.depth };
      });
    });
    // castKey and the per-character maps are the inputs; roster identity
    // is not.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [castKey, facings, poses, towards, order]);

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

      {!running && phase !== 'review' && (
        <div className="story-image-quick">
          <button type="button" className="story-image-shortcut" onClick={startPassages}>
            Pick a passage
          </button>
          {saved !== null && (
            <>
              <button
                type="button"
                className="story-image-shortcut"
                title={setupSummary(saved)}
                onClick={repeatLast}
              >
                Repeat last setup
              </button>
              <button
                type="button"
                className="story-image-shortcut story-image-shortcut--muted"
                title="Forget the stored setup for this story"
                onClick={forgetLast}
              >
                Forget
              </button>
            </>
          )}
        </div>
      )}

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
                          {inShot.has(person.characterId) && (
                            <label className="story-image-action">
                              In front
                              <input
                                type="number"
                                className="arc-input story-image-order"
                                min={1}
                                max={inShot.size}
                                value={order.indexOf(person.characterId) + 1}
                                onChange={event => setOrder(previous => reorderTo(
                                  previous, person.characterId,
                                  Number(event.target.value),
                                ))}
                              />
                            </label>
                          )}
                          {inShot.has(person.characterId) && (
                            <PersonSelect
                              label="Pose"
                              value={poses.get(person.characterId) ?? ''}
                              options={POSE_OPTIONS}
                              onPick={value => setFor(setPoses, person.characterId, value)}
                            />
                          )}
                          {inShot.has(person.characterId) && (
                            <PersonSelect
                              label="Facing"
                              value={facings.get(person.characterId) ?? ''}
                              options={FACING_OPTIONS}
                              onPick={value => setFor(setFacings, person.characterId, value)}
                            />
                          )}
                          {inShot.has(person.characterId)
                            && HANDED.has(facings.get(person.characterId) ?? '') && (
                            <PersonSelect
                              label="Turned"
                              value={towards.get(person.characterId) ?? DEFAULT_TOWARD}
                              options={TOWARD_OPTIONS}
                              onPick={value => setFor(setTowards, person.characterId, value)}
                            />
                          )}
                          {inShot.has(person.characterId) && (
                            <label className="story-image-action">
                              Doing
                              <input
                                type="text"
                                className="arc-input"
                                maxLength={MAX_ACTION_CHARS}
                                placeholder="from the story"
                                value={actions.get(person.characterId) ?? ''}
                                onChange={event => setActions(previous => {
                                  const next = new Map(previous);
                                  next.set(person.characterId, event.target.value);
                                  return next;
                                })}
                              />
                            </label>
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
              <p className="story-image-group">Staging</p>
              <div className="story-image-framing">
                <label>
                  Setting
                  <select
                    className="arc-select"
                    value={setting}
                    onChange={event => setSetting(event.target.value)}
                  >
                    {SETTING_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Mood
                  <select
                    className="arc-select"
                    value={mood}
                    onChange={event => setMood(event.target.value)}
                  >
                    {MOOD_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              </div>
              <StagingCanvas
                people={roster
                  .filter(person => inShot.has(person.characterId))
                  .map(person => ({ name: person.name, characterId: person.characterId }))}
                shot={shot}
                placements={placements}
                onChange={setPlacements}
              />
              <label className="story-image-regions">
                <input
                  type="checkbox"
                  checked={regions}
                  onChange={event => setRegionsChoice(event.target.checked)}
                />
                Paint each character separately
              </label>
              <p className="story-image-likeness--none story-image-regions-note">
                {regions
                  ? 'Each character gets their own prompt and pass. Slower, and the only way a large cast all appear.'
                  : 'One prompt for everyone, likeness for at most two. Fine for one or two characters.'}
              </p>
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
