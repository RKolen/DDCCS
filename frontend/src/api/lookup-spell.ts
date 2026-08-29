import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Resolve a spell's stat block from the Python sidecar (rules wiki).
 */

interface LookupBody {
  name: string;
}

interface SidecarResponse {
  spell: Record<string, unknown> | null;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as LookupBody;
  const name = body?.name?.trim();
  if (!name) {
    res.status(400).json({ error: 'name is required' });
    return;
  }

  const base = sidecarBaseUrl();
  if (!base) {
    res.status(500).json({ error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let sidecarRes: Response;
  try {
    sidecarRes = await fetch(`${base}/spells/lookup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the sidecar: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    res.status(sidecarRes.status).json({ error: await sidecarRes.text() });
    return;
  }

  const data = (await sidecarRes.json()) as SidecarResponse;
  res.status(200).json({ spell: data.spell });
}
