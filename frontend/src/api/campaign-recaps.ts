import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';
import { htmlToText, readProcessed, type SessionSummary } from '../utils/aiSummary';

/**
 * Read a campaign's stored session recaps and overview.
 *
 * POST `{ campaignId }` -> `{ recaps: [{ storyNumber, summary }], overview }`.
 * No model call: these were written by the session-summary pipeline. The arc
 * backfill starts here so it only pays to summarise the sessions that have
 * never been summarised.
 */

interface CampaignRecapsBody {
  campaignId: string;
}

interface CampaignTerm {
  name:              string;
  campaignOverview:  { text?: Array<{ processed: string }> | { processed: string } | null } | null;
  sessionSummaries:  Array<{
    storyNumber: number | null;
    text?:       Array<{ processed: string }> | { processed: string } | null;
  }> | null;
}

const RECAPS_QUERY = `
  query CampaignRecaps($id: ID!) {
    term(id: $id) {
      ... on TermCampaign {
        name
        campaignOverview { ... on ParagraphWysiwyg { text { processed } } }
        sessionSummaries {
          ... on ParagraphSessionSummary {
            storyNumber
            text { processed }
          }
        }
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

  const body = req.body as CampaignRecapsBody;
  if (!body?.campaignId?.trim()) {
    res.status(400).json({ error: 'campaignId is required' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ term: CampaignTerm | null }>(
      creds,
      RECAPS_QUERY,
      { id: body.campaignId.trim() },
    );
    const term = data.term;
    if (!term) {
      res.status(404).json({ error: 'Campaign not found' });
      return;
    }

    const recaps: SessionSummary[] = (term.sessionSummaries ?? [])
      .filter((row): row is { storyNumber: number; text?: typeof row.text } => (
        row.storyNumber !== null
      ))
      .map(row => ({
        storyNumber: row.storyNumber,
        summary:     htmlToText(readProcessed(row.text)),
      }))
      .filter(row => row.summary !== '')
      .sort((a, b) => a.storyNumber - b.storyNumber);

    res.status(200).json({
      campaignName: term.name,
      recaps,
      overview:     htmlToText(readProcessed(term.campaignOverview?.text)),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
