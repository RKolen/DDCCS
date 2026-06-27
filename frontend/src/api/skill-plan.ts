import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Return a character's class + species/subspecies skill plan (granted skills
 * and choice groups) from the sidecar, so the wizard's skills step can present
 * rules-aware, restricted selections. Background grants are layered on client
 * side from the resolved background.
 */

interface SkillPlanBody {
  className:   string;
  level:       number;
  species?:    string;
  subspecies?: string | null;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as SkillPlanBody;
  if (!body?.className?.trim()) {
    res.status(400).json({ error: 'className is required' });
    return;
  }

  const base = sidecarBaseUrl();
  if (!base) {
    res.status(500).json({ error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let sidecarRes: Response;
  try {
    sidecarRes = await fetch(`${base}/character/skill-plan`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        class_name: body.className.trim(),
        level:      body.level,
        race:       body.species ?? 'Human',
        subspecies: body.subspecies ?? null,
      }),
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

  res.status(200).json(await sidecarRes.json());
}
