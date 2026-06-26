import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

interface SpotlightRequestBody {
  campaignName: string;
  characterNames: string[];
}

interface SidecarEntry {
  name: string;
  score: number;
}

interface SidecarResponse {
  campaign_name: string;
  entries: SidecarEntry[];
}

export interface SpotlightScores {
  campaignName: string;
  scores: Record<string, number>;
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as SpotlightRequestBody;
  if (!body?.campaignName) {
    res.status(400).json({ error: 'campaignName is required' });
    return;
  }

  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    // Sidecar not configured — degrade to zero scores like an unreachable one.
    res.status(200).json({
      campaignName: body.campaignName,
      scores: Object.fromEntries((body.characterNames ?? []).map(n => [n, 0])),
    });
    return;
  }

  let sidecarRes: Response;
  try {
    sidecarRes = await fetch(`${sidecarUrl}/spotlight`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_name:   body.campaignName,
        character_names: body.characterNames ?? [],
      }),
    });
  } catch {
    // Sidecar not running — return zero scores so the picker degrades gracefully
    const fallback: SpotlightScores = {
      campaignName: body.campaignName,
      scores: Object.fromEntries((body.characterNames ?? []).map(n => [n, 0])),
    };
    res.status(200).json(fallback);
    return;
  }

  if (!sidecarRes.ok) {
    const fallback: SpotlightScores = {
      campaignName: body.campaignName,
      scores: Object.fromEntries((body.characterNames ?? []).map(n => [n, 0])),
    };
    res.status(200).json(fallback);
    return;
  }

  const data = (await sidecarRes.json()) as SidecarResponse;
  const scores: Record<string, number> = {};
  for (const entry of data.entries) {
    scores[entry.name] = entry.score;
  }

  const result: SpotlightScores = { campaignName: body.campaignName, scores };
  res.status(200).json(result);
}
