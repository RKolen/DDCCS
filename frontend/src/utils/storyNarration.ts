/**
 * Multi-voice story narration for the public story reader.
 *
 * Segments story text via `/api/tts-segment` (Python dialogue detector), then
 * plays each clip through `/api/tts` with the matching Piper voice.
 */

export interface CharacterVoiceSource {
  title:      string;
  firstName?: string | null;
  nickname?:  string | null;
  voiceId?:   string | null;
  voicePitch?: number | null;
  voiceSpeed?: number | null;
}

export interface NarrationVoiceEntry {
  voiceId: string;
  speed:   number;
  pitch:   number;
}

export interface NarrationSegment {
  text:    string;
  speaker: string;
  voiceId: string;
  speed:   number;
  pitch:   number;
}

export interface PlayStoryNarrationOptions {
  text:        string;
  onProgress?: (index: number, total: number, speaker: string) => void;
  signal?:     AbortSignal;
}

const PAUSE_SAME_SPEAKER_MS = 500;
const PAUSE_SPEAKER_CHANGE_MS = 750;

/**
 * Turn Drupal story HTML (or plain text) into paragraph-aware prose for the
 * dialogue detector. Without ``\\n\\n`` breaks the detector sees one blob and
 * drops all narrator prose — only quoted lines survive.
 */
export function toNarrationText(raw: string): string {
  let text = raw.replace(/^\uFEFF/, '');
  const looksHtml = /<\/?(p|br|div|h[1-6]|li|blockquote)\b/i.test(text);
  if (looksHtml) {
    text = text
      .replace(/\r\n?/g, '\n')
      .replace(/<\/(p|div|h[1-6]|li|blockquote)>/gi, '\n\n')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/?[^>]+>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>')
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/gi, "'")
      .replace(/&apos;/gi, "'");
  }
  // Normalise curly quotes so the dialogue detector's "..." patterns match.
  text = text
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
  return text;
}

/** Build a name -> voice entry map from Drupal character nodes. */
export function buildVoiceMap(
  characters: CharacterVoiceSource[],
): Record<string, NarrationVoiceEntry> {
  const map: Record<string, NarrationVoiceEntry> = {};
  const assign = (name: string | null | undefined, entry: NarrationVoiceEntry): void => {
    const key = name?.trim();
    // First wins: list-character-voices can return duplicate titles (source +
    // campaign clones) and a later bad speed/pitch must not overwrite a good one.
    if (!key || key in map) return;
    map[key] = entry;
  };
  for (const c of characters) {
    const voiceId = c.voiceId?.trim();
    if (!voiceId) continue;
    const entry: NarrationVoiceEntry = {
      voiceId,
      speed: c.voiceSpeed ?? 1.0,
      pitch: c.voicePitch ?? 0.0,
    };
    assign(c.title, entry);
    assign(c.firstName, entry);
    assign(c.nickname, entry);
  }
  return map;
}

/** Collect unique known names (title / first / nickname) for dialogue detection. */
export function buildKnownNames(characters: CharacterVoiceSource[]): string[] {
  const names = new Set<string>();
  for (const c of characters) {
    if (c.title.trim()) names.add(c.title.trim());
    const first = c.firstName?.trim();
    if (first) names.add(first);
    const nick = c.nickname?.trim();
    if (nick) names.add(nick);
  }
  return [...names];
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (ms <= 0) return Promise.resolve();
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    const onAbort = (): void => {
      clearTimeout(timer);
      reject(new DOMException('Aborted', 'AbortError'));
    };
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

async function fetchCharacterVoices(
  signal?: AbortSignal,
): Promise<CharacterVoiceSource[]> {
  // Pages past graphql_compose's 100-cap via /api/list-character-voices
  // (same cursor pattern as list-portrait-media).
  const res = await fetch('/api/list-character-voices', { method: 'GET', signal });
  if (!res.ok) {
    const detail = (await res.json().catch(() => null)) as { error?: string } | null;
    throw new Error(detail?.error ?? `Voice roster failed (${res.status})`);
  }
  const data = (await res.json()) as { characters: CharacterVoiceSource[] };
  return data.characters ?? [];
}

async function fetchSegments(
  text: string,
  voiceMap: Record<string, NarrationVoiceEntry>,
  knownNames: string[],
  signal?: AbortSignal,
): Promise<NarrationSegment[]> {
  const res = await fetch('/api/tts-segment', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      text,
      characterVoices: voiceMap,
      knownCharacters: knownNames,
      knownNpcs:       knownNames,
    }),
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => null)) as { error?: string } | null;
    throw new Error(detail?.error ?? `Segmentation failed (${res.status})`);
  }
  const data = (await res.json()) as { segments: NarrationSegment[] };
  return data.segments ?? [];
}

async function synthesizeSegment(
  segment: NarrationSegment,
  signal?: AbortSignal,
): Promise<Blob> {
  const res = await fetch('/api/tts', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      text:    segment.text,
      voiceId: segment.voiceId,
      speed:   segment.speed,
      pitch:   segment.pitch,
    }),
  });
  if (!res.ok) {
    throw new Error(`TTS failed (${res.status}) for ${segment.speaker}`);
  }
  return res.blob();
}

/**
 * Play blobs on one reused HTMLAudioElement.
 *
 * Creating a new Audio() per clip loses the user-gesture unlock after the first
 * await, so only one speaker is heard. Reusing the same element keeps playback
 * allowed for the whole narration session.
 */
class NarrationPlayer {
  private readonly audio: HTMLAudioElement = new Audio();

  private objectUrl: string | null = null;

  stop(): void {
    this.audio.pause();
    this.audio.removeAttribute('src');
    this.audio.load();
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
  }

  play(blob: Blob, signal?: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      if (signal?.aborted) {
        reject(new DOMException('Aborted', 'AbortError'));
        return;
      }
      if (this.objectUrl) {
        URL.revokeObjectURL(this.objectUrl);
        this.objectUrl = null;
      }
      const url = URL.createObjectURL(blob);
      this.objectUrl = url;
      this.audio.src = url;

      const cleanup = (): void => {
        signal?.removeEventListener('abort', onAbort);
        this.audio.onended = null;
        this.audio.onerror = null;
      };
      const onAbort = (): void => {
        this.audio.pause();
        cleanup();
        reject(new DOMException('Aborted', 'AbortError'));
      };
      this.audio.onended = () => {
        cleanup();
        resolve();
      };
      this.audio.onerror = () => {
        cleanup();
        reject(new Error('Audio playback failed'));
      };
      signal?.addEventListener('abort', onAbort, { once: true });
      void this.audio.play().catch(err => {
        cleanup();
        reject(err instanceof Error ? err : new Error(String(err)));
      });
    });
  }
}

/**
 * Segment a story and play each clip with the matching Piper voice.
 *
 * Loads the full character voice roster via cursor-paginated Drupal GraphQL
 * (graphql_compose caps ``first`` at 100), then segments and synthesises.
 *
 * Abort via `signal` to stop mid-narration (pause current audio and return).
 */
export async function playStoryNarration(
  options: PlayStoryNarrationOptions,
): Promise<void> {
  const { text, onProgress, signal } = options;
  const cleaned = toNarrationText(text);
  if (!cleaned.trim()) {
    throw new Error('No story text to narrate');
  }

  const roster = await fetchCharacterVoices(signal);
  const voiceMap = buildVoiceMap(roster);
  const knownNames = buildKnownNames(roster);
  const segments = await fetchSegments(cleaned, voiceMap, knownNames, signal);
  if (segments.length === 0) {
    throw new Error('No speech segments found');
  }

  const player = new NarrationPlayer();
  try {
    // Prefetch the first clip, then keep one clip synthesising ahead so the
    // reused audio element stays busy (helps autoplay and hides TTS latency).
    let nextBlob = synthesizeSegment(segments[0], signal);
    for (let i = 0; i < segments.length; i += 1) {
      if (signal?.aborted) {
        throw new DOMException('Aborted', 'AbortError');
      }
      const segment = segments[i];
      onProgress?.(i + 1, segments.length, segment.speaker);
      const prefetch = i + 1 < segments.length
        ? synthesizeSegment(segments[i + 1], signal)
        : null;
      const blob = await nextBlob;
      nextBlob = prefetch ?? Promise.resolve(new Blob());
      await player.play(blob, signal);

      if (i < segments.length - 1) {
        const next = segments[i + 1];
        const pauseMs = segment.speaker === next.speaker
          ? PAUSE_SAME_SPEAKER_MS
          : PAUSE_SPEAKER_CHANGE_MS;
        await sleep(pauseMs, signal);
      }
    }
  } finally {
    player.stop();
  }
}

/** True when an error is an intentional narration abort. */
export function isNarrationAbort(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'AbortError';
}
