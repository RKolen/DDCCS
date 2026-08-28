import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';
import type { ArcRelationsPayload } from '../utils/arcPayload';

/**
 * Replace a story arc's relationship collections.
 *
 * POST `{ id, relations: { party?, npc? } }` -> `{ id, title, partySaved, npcSaved }`.
 *
 * Only the sides present are replaced, so "suggest party relations" and
 * "suggest NPC relations" can each save without clearing the other. Within a
 * side the replacement is wholesale: the console sends the set that survived
 * accept/reject, not a diff.
 *
 * The saved counts come back from Drupal rather than being echoed from the
 * request, because a pair whose source or target does not resolve is skipped —
 * so the caller can tell the operator that 12 of 13 suggestions landed.
 */

interface SaveArcRelationsBody {
  id:        string;
  relations: ArcRelationsPayload;
}

interface RelationsResult {
  id:                 string;
  title:              string;
  arcPartyRelations:  Array<Record<string, unknown>> | null;
  arcNpcRelations:    Array<Record<string, unknown>> | null;
}

const SAVE_ARC_RELATIONS_MUTATION = `
  mutation SaveStoryArcRelations($id: ID!, $payload: String!) {
    saveStoryArcRelations(id: $id, payload: $payload) {
      id
      title
      arcPartyRelations { __typename }
      arcNpcRelations   { __typename }
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

  const body = req.body as SaveArcRelationsBody;
  const relations = body?.relations;
  if (!body?.id || !relations || typeof relations !== 'object') {
    res.status(400).json({ error: 'id and relations are required' });
    return;
  }
  if (!Array.isArray(relations.party) && !Array.isArray(relations.npc)) {
    res.status(400).json({ error: 'relations must contain a party or npc list' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ saveStoryArcRelations: RelationsResult | null }>(
      creds,
      SAVE_ARC_RELATIONS_MUTATION,
      { id: body.id, payload: JSON.stringify(relations) },
    );
    const arc = data.saveStoryArcRelations;
    if (!arc) {
      res.status(502).json({ error: 'Drupal did not return the updated arc.' });
      return;
    }
    res.status(200).json({
      id:         arc.id,
      title:      arc.title,
      partySaved: arc.arcPartyRelations?.length ?? 0,
      npcSaved:   arc.arcNpcRelations?.length ?? 0,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
