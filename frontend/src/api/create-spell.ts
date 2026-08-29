import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { drupalCredentials, runDrupalMutation } from '../utils/drupalMutation';

/**
 * Create a spell node (homebrew or an official import).
 *
 * POST the Drupal field set. Creating a title that already exists returns
 * the existing node, so an import rerun cannot duplicate the vault.
 */

interface CreateSpellBody {
  title: string;
  level?: number | null;
  school?: string | null;
  castingTime?: string | null;
  spellRange?: string | null;
  components?: string | null;
  duration?: string | null;
  concentration?: boolean | null;
  ritual?: boolean | null;
  description?: string | null;
}

interface SpellResult {
  id: string;
  title: string;
  path: string | null;
}

const CREATE_SPELL_MUTATION = `
  mutation CreateSpell(
    $title: String!
    $level: Int
    $school: String
    $castingTime: String
    $spellRange: String
    $components: String
    $duration: String
    $concentration: Boolean
    $ritual: Boolean
    $description: String
  ) {
    createSpell(
      title: $title
      level: $level
      school: $school
      castingTime: $castingTime
      spellRange: $spellRange
      components: $components
      duration: $duration
      concentration: $concentration
      ritual: $ritual
      description: $description
    ) {
      id
      title
      path
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

  const body = req.body as CreateSpellBody;
  if (!body?.title?.trim()) {
    res.status(400).json({ error: 'title is required' });
    return;
  }

  const creds = drupalCredentials();
  if (!creds) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  try {
    const data = await runDrupalMutation<{ createSpell: SpellResult | null }>(
      creds,
      CREATE_SPELL_MUTATION,
      {
        title: body.title.trim(),
        level: body.level ?? 0,
        school: body.school?.trim() || null,
        castingTime: body.castingTime?.trim() || null,
        spellRange: body.spellRange?.trim() || null,
        components: body.components?.trim() || null,
        duration: body.duration?.trim() || null,
        concentration: body.concentration ?? false,
        ritual: body.ritual ?? false,
        description: body.description?.trim() || null,
      },
    );
    if (!data.createSpell) {
      res.status(502).json({ error: 'Drupal did not return the created spell.' });
      return;
    }
    res.status(200).json(data.createSpell);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: message });
  }
}
