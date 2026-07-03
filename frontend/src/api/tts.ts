import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Text-to-speech proxy.
 *
 * Forwards text to the Python sidecar's Piper endpoint and streams the
 * synthesised WAV audio back to the browser, so credentials/host stay
 * server-side.
 */

interface TtsBody {
  text:     string;
  voiceId?: string;
  speed?:   number;
  pitch?:   number;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as TtsBody;
  if (!body?.text?.trim()) {
    res.status(400).json({ error: 'text is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(500).json({ error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let ttsRes: Response;
  try {
    ttsRes = await fetch(`${sidecarUrl}/tts/speak`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        text:     body.text.trim(),
        voice_id: body.voiceId ?? '',
        speed:    body.speed ?? 1.0,
        pitch:    body.pitch ?? 0.0,
      }),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the TTS sidecar: ${msg}` });
    return;
  }

  if (!ttsRes.ok) {
    const detail = await ttsRes.text();
    res.status(ttsRes.status).json({ error: detail || 'TTS synthesis failed' });
    return;
  }

  const audio = Buffer.from(await ttsRes.arrayBuffer());
  res.setHeader('Content-Type', 'audio/wav');
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).send(audio);
}
