import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';
import { sidecarFetch } from '../utils/sidecarFetch';

/**
 * Describe an existing portrait into a prompt (image->prompt).
 *
 * POST `{ imageUrl }` -> sidecar `/character/describe-image`, which runs the
 * local Ollama vision model (IMAGE_TO_PROMPT_MODEL) and returns a comma-
 * separated visual descriptor as `positive`. Uses `sidecarFetch` because CPU
 * vision inference is slow. 503 when the vision model/Ollama is unconfigured.
 */

interface DescribeBody {
  imageUrl: string;
  /** Known character facts (species/lineage/class) to prime the vision model. */
  profile?: Record<string, unknown>;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as DescribeBody;
  if (!body?.imageUrl?.trim()) {
    res.status(400).json({ error: 'imageUrl is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(503).json({ error: 'Vision sidecar is not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let sidecarRes: Awaited<ReturnType<typeof sidecarFetch>>;
  try {
    sidecarRes = await sidecarFetch(`${sidecarUrl}/character/describe-image`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ image_url: body.imageUrl, profile: body.profile ?? {} }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Vision sidecar unreachable: ${message}` });
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
