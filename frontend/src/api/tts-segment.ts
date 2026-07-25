import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Multi-voice TTS segmentation proxy.
 *
 * Forwards story text + character voice map to the Python sidecar's
 * `/tts/segment` endpoint so the browser can play each clip via `/api/tts`.
 */

export interface TtsVoiceEntryBody {
  voiceId: string;
  speed?:  number;
  pitch?:  number;
}

interface TtsSegmentBody {
  text:             string;
  characterVoices?: Record<string, TtsVoiceEntryBody | string>;
  knownCharacters?: string[];
  knownNpcs?:       string[];
  narratorVoiceId?: string;
}

interface SidecarVoiceEntry {
  voice_id: string;
  speed:    number;
  pitch:    number;
}

interface SidecarSegment {
  text:     string;
  speaker:  string;
  voice_id: string;
  speed:    number;
  pitch:    number;
}

function toSidecarVoice(
  entry: TtsVoiceEntryBody | string,
): SidecarVoiceEntry | string {
  if (typeof entry === 'string') return entry;
  return {
    voice_id: entry.voiceId,
    speed:    entry.speed ?? 1.0,
    pitch:    entry.pitch ?? 0.0,
  };
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as TtsSegmentBody;
  if (!body?.text?.trim()) {
    res.status(400).json({ error: 'text is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(500).json({
      error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)',
    });
    return;
  }

  const characterVoices: Record<string, SidecarVoiceEntry | string> = {};
  for (const [name, entry] of Object.entries(body.characterVoices ?? {})) {
    characterVoices[name] = toSidecarVoice(entry);
  }

  let segRes: Response;
  try {
    segRes = await fetch(`${sidecarUrl}/tts/segment`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        text:              body.text.trim(),
        character_voices:  characterVoices,
        known_characters:  body.knownCharacters ?? [],
        known_npcs:        body.knownNpcs ?? [],
        narrator_voice_id: body.narratorVoiceId ?? '',
      }),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the TTS sidecar: ${msg}` });
    return;
  }

  if (!segRes.ok) {
    const detail = await segRes.text();
    res.status(segRes.status).json({ error: detail || 'TTS segmentation failed' });
    return;
  }

  const data = (await segRes.json()) as { segments: SidecarSegment[] };
  res.status(200).json({
    segments: (data.segments ?? []).map(s => ({
      text:    s.text,
      speaker: s.speaker,
      voiceId: s.voice_id,
      speed:   s.speed,
      pitch:   s.pitch,
    })),
  });
}
