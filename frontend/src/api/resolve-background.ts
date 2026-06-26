import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Resolve a background's granted data (ability options, feat, skills, tools,
 * gold, equipment) from the Python sidecar, which scrapes the 2024 rules wiki.
 *
 * Called when a background is selected in the creation wizard so the skills
 * step can pre-select granted skills and the term can be populated on create.
 */

interface ResolveBackgroundBody {
  name: string;
}

interface SidecarBackground {
  ability_options: string[];
  feat:            string;
  skills:          string[];
  tools:           string[];
  gold:            number;
  equipment:       string[];
}

interface SidecarResponse {
  background: SidecarBackground | null;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as ResolveBackgroundBody;
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
    sidecarRes = await fetch(`${base}/character/resolve-background`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the character sidecar: ${message}` });
    return;
  }

  if (!sidecarRes.ok) {
    res.status(sidecarRes.status).json({ error: await sidecarRes.text() });
    return;
  }

  const data = (await sidecarRes.json()) as SidecarResponse;
  res.status(200).json({ background: data.background });
}
