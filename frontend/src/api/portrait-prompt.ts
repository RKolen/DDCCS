import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Build (or AI-enhance) a portrait prompt from a character profile.
 *
 * POST `{ profile, positive?, enhance? }` -> sidecar `/character/portrait/prompt`.
 * With no `positive` it builds the template prompt from the profile; with
 * `positive` set and `enhance: true` it enriches the given (edited) text. Uses
 * `sidecarFetch` because the enhance path is a model call.
 */

interface PromptBody {
  profile:   Record<string, unknown>;
  positive?: string;
  enhance?:  boolean;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as PromptBody;
  if (!body?.profile || Object.keys(body.profile).length === 0) {
    res.status(400).json({ error: 'profile is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Prompt sidecar is not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/character/portrait/prompt`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profile:  body.profile,
        positive: body.positive ?? null,
        enhance:  body.enhance ?? false,
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Prompt sidecar unreachable: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    const text = await sidecarRes.text();
    res.status(sidecarRes.status).json({ error: text });
    return;
  }

  const data = await sidecarRes.json();
  res.status(200).json(data);
}
