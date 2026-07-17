import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Read a character's stored analysis off the character_analysis node.
 *
 * POST `{ campaignId, characterId }` -> `{ storyNumbers, storyAnalyses, summary }`.
 * `storyNumbers` is the resume signal (the console skips stories already
 * persisted); `storyAnalyses` (per-story prose) and `summary` back the arc
 * screen's stored-analysis display.
 */
import { htmlToText, readProcessed } from '../utils/aiSummary';

interface Body {
  campaignId:  string;
  characterId: string;
}

interface AnalysisNode {
  campaign:        { id: string } | null;
  character:       { id: string } | null;
  storyAnalyses:   Array<{
    storyNumber: number | null;
    // field_text is cardinality -1, so graphql_compose exposes `text` as a list.
    text:        Array<{ processed: string }> | null;
  }> | null;
  analysisSummary: { processed: string } | null;
}

const QUERY = `
  query {
    nodeCharacterAnalysis(first: 100) {
      nodes {
        campaign { ... on TermCampaign { id } }
        character { ... on NodeCharacter { id } }
        storyAnalyses {
          ... on ParagraphSessionSummary { storyNumber text { processed } }
        }
        analysisSummary { processed }
      }
    }
  }
`;

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const body = req.body as Body;
  if (!body?.characterId) {
    res.status(400).json({ error: 'characterId is required' });
    return;
  }

  const drupalUrl = (
    process.env.GATSBY_DRUPAL_BASE_URL ?? process.env.DRUPAL_BASE_URL ?? ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  if (!drupalUrl || !token) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const drupalRes = await fetch(`${drupalUrl}/graphql`, {
      method:  'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept:         'application/json',
      },
      body: JSON.stringify({ query: QUERY }),
    });
    const payload = (await drupalRes.json()) as {
      data?: { nodeCharacterAnalysis: { nodes: AnalysisNode[] } };
    };
    // Keyed by character: a character has one analysis record (campaign is
    // optional metadata and may not match the ambient campaign context).
    const node = (payload.data?.nodeCharacterAnalysis.nodes ?? []).find(
      n => n.character?.id === body.characterId,
    );
    const analyses = (node?.storyAnalyses ?? [])
      .slice()
      .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0));
    const storyNumbers = analyses
      .map(s => s.storyNumber)
      .filter((n): n is number => typeof n === 'number');
    const storyAnalyses = analyses.map(s => ({
      storyNumber: s.storyNumber,
      text:        htmlToText(readProcessed(s.text)),
    }));
    const summary = htmlToText(node?.analysisSummary?.processed ?? '');
    res.status(200).json({ storyNumbers, storyAnalyses, summary });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to read analysis: ${message}` });
  }
}
