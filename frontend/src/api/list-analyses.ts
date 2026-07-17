import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * List every stored character_analysis record in one call.
 *
 * POST (no body needed) -> `{ analyses: [{ characterId, storyCount, hasSummary }] }`.
 * The arc hub uses this to show, per character card, whether stored per-story
 * analyses exist (so a "Synthesize summary" affordance can appear) without a
 * request per character.
 */

interface AnalysisNode {
  character:       { id: string } | null;
  analysisSummary: { processed: string } | null;
  storyAnalyses:   Array<{ storyNumber: number | null }> | null;
}

const QUERY = `
  query {
    nodeCharacterAnalysis(first: 100) {
      nodes {
        character { ... on NodeCharacter { id } }
        analysisSummary { processed }
        storyAnalyses { ... on ParagraphSessionSummary { storyNumber } }
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
    const analyses = (payload.data?.nodeCharacterAnalysis.nodes ?? [])
      .filter(n => n.character?.id)
      .map(n => ({
        characterId: n.character?.id ?? '',
        storyCount:  (n.storyAnalyses ?? []).length,
        hasSummary:  Boolean(n.analysisSummary?.processed?.trim()),
      }));
    res.status(200).json({ analyses });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to list analyses: ${message}` });
  }
}
