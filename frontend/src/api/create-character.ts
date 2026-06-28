import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { sidecarBaseUrl } from '../utils/sidecar';

/**
 * Create a source character and attach a campaign clone.
 *
 * Flow:
 *   1. POST the wizard input to the Python sidecar, which derives the full
 *      character sheet (HP, proficiency, saves, class features, spell slots).
 *   2. Persist the derived sheet as a source character via the Drupal
 *      createCharacter GraphQL mutation.
 *   3. When a campaign id is supplied, clone the source into that campaign via
 *      addCharacterToCampaign (the clone is registered in field_current_party).
 */

interface AbilityScores {
  strength:     number;
  dexterity:    number;
  constitution: number;
  intelligence: number;
  wisdom:       number;
  charisma:     number;
}

interface CreateCharacterBody {
  name:           string;
  firstName?:     string;
  lastName?:      string | null;
  nickname?:      string | null;
  className:      string;
  level:          number;
  abilityScores:  AbilityScores;
  skills?:        string[];
  tools?:         string[];
  background?:    string;
  backgroundDefinition?: {
    abilities:        string[];
    skills:           string[];
    tools:            string[];
    feat:             string;
    feat_description?: string;
    gold:             number;
    equipment:        string[];
  } | null;
  /** Final item names the character takes (resolved class + background A/B choices). */
  equipment?:     string[];
  /** Total gold from any A/B groups where the player took gold instead of items. */
  gold?:          number;
  species?:       string;
  subspecies?:    string | null;
  subclass?:      string | null;
  campaignId?:    string | null;
  backstory?:          string;
  personalityTraits?:  string[];
  ideals?:             string[];
  bonds?:              string[];
  flaws?:              string[];
  /** When true, derive and return the sheet without persisting to Drupal. */
  dryRun?:        boolean;
}

interface BuiltCharacterResponse {
  character?: Record<string, unknown>;
  error?:     string;
  detail?:    string;
}

interface CreatedCharacter {
  id:    string;
  title: string;
}

interface GraphQlResponse<T> {
  data?:   T;
  errors?: Array<{ message: string }>;
}

const CREATE_CHARACTER_MUTATION = `
  mutation CreateCharacter($payload: String!) {
    createCharacter(payload: $payload) {
      id
      title
    }
  }
`;

const ADD_TO_CAMPAIGN_MUTATION = `
  mutation AddCharacterToCampaign($campaignId: ID!, $characterId: ID!) {
    addCharacterToCampaign(campaignId: $campaignId, characterId: $characterId) {
      id
      currentParty {
        ... on NodeCharacter { id title }
      }
    }
  }
`;

function drupalEndpoint(): { url: string; token: string } {
  const url = (
    process.env.GATSBY_DRUPAL_BASE_URL ??
    process.env.DRUPAL_BASE_URL ??
    ''
  ).replace(/\/$/, '');
  const token = process.env.DRUPAL_GRAPHQL_TOKEN ?? '';
  return { url, token };
}

async function drupalGraphQl<T>(
  query: string,
  variables: Record<string, unknown>,
): Promise<GraphQlResponse<T>> {
  const { url, token } = drupalEndpoint();
  const drupalRes = await fetch(`${url}/graphql`, {
    method:  'POST',
    headers: {
      Authorization:  `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept:         'application/json',
    },
    body: JSON.stringify({ query, variables }),
  });
  return (await drupalRes.json()) as GraphQlResponse<T>;
}

interface EquipmentItemInfo {
  description: string;
  item_type:  string;
}

interface EquipmentDescribeResponse {
  items: Record<string, EquipmentItemInfo>;
}

/**
 * Resolve descriptions and item types for an equipment list via the sidecar.
 * Returns an empty map on any failure so character creation still proceeds.
 */
async function describeEquipment(
  sidecarUrl: string,
  names: string[],
): Promise<Record<string, EquipmentItemInfo>> {
  try {
    const describeRes = await fetch(`${sidecarUrl}/character/equipment/describe`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ names }),
    });
    if (!describeRes.ok) return {};
    const payload = (await describeRes.json()) as EquipmentDescribeResponse;
    return payload.items ?? {};
  } catch {
    return {};
  }
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const body = req.body as CreateCharacterBody;
  if (!body?.name?.trim() || !body?.className?.trim() || !body?.abilityScores) {
    res.status(400).json({ error: 'name, className, and abilityScores are required' });
    return;
  }

  const { url, token } = drupalEndpoint();
  if (!url || !token) {
    res.status(500).json({ error: 'Drupal credentials not configured' });
    return;
  }

  // 1. Derive the character sheet via the sidecar.
  const sidecarUrl = sidecarBaseUrl();
  if (!sidecarUrl) {
    res.status(500).json({ error: 'Sidecar not configured (set SIDECAR_HOST and SIDECAR_PORT)' });
    return;
  }

  let builtRes: Response;
  try {
    builtRes = await fetch(`${sidecarUrl}/character/build-from-template`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name:           body.name.trim(),
        class_name:     body.className.trim(),
        level:          body.level,
        ability_scores: body.abilityScores,
        skills:         body.skills ?? [],
        background:     body.background ?? '',
        race:           body.species ?? 'Human',
        subspecies:     body.subspecies ?? null,
        subclass:       body.subclass ?? null,
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Could not reach the character sidecar: ${message}` });
    return;
  }

  const built = (await builtRes.json()) as BuiltCharacterResponse;
  if (!builtRes.ok || !built.character) {
    res.status(builtRes.status === 200 ? 502 : builtRes.status)
      .json({ error: built.detail ?? built.error ?? 'Character derivation failed' });
    return;
  }

  // Merge user-supplied roleplay fields onto the derived sheet.
  const character: Record<string, unknown> = { ...built.character };
  if (body.firstName) character.first_name = body.firstName;
  if (body.lastName) character.last_name = body.lastName;
  if (body.nickname) character.nickname = body.nickname;
  if (body.tools) character.tools = body.tools;
  if (body.backgroundDefinition) character.background_definition = body.backgroundDefinition;
  if (body.backstory) character.backstory = body.backstory;
  if (body.personalityTraits) character.personality_traits = body.personalityTraits;
  if (body.ideals) character.ideals = body.ideals;
  if (body.bonds) character.bonds = body.bonds;
  if (body.flaws) character.flaws = body.flaws;

  // The character's final equipment is the resolved A/B selections (class +
  // background); fall back to the background package when no explicit selection
  // was made. Enrich it with rules-wiki descriptions and item types so the
  // created item nodes get an accurate field_description and field_item_type.
  const equipment = body.equipment ?? body.backgroundDefinition?.equipment ?? [];
  character.equipment = equipment;
  character.gold = body.gold ?? 0;
  if (equipment.length > 0) {
    const descriptions = await describeEquipment(sidecarUrl, equipment);
    if (Object.keys(descriptions).length > 0) {
      character.equipment_descriptions = descriptions;
    }
  }

  // Preview only: return the derived sheet without persisting.
  if (body.dryRun) {
    res.status(200).json({ character });
    return;
  }

  // 2. Persist the source character.
  let sourcePayload: GraphQlResponse<{ createCharacter: CreatedCharacter | null }>;
  try {
    sourcePayload = await drupalGraphQl(CREATE_CHARACTER_MUTATION, {
      payload: JSON.stringify(character),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Failed to reach Drupal: ${message}` });
    return;
  }

  if (sourcePayload.errors && sourcePayload.errors.length > 0) {
    res.status(400).json({ error: sourcePayload.errors[0].message });
    return;
  }

  const source = sourcePayload.data?.createCharacter ?? null;
  if (!source) {
    res.status(500).json({ error: 'Character creation returned no data' });
    return;
  }

  // 3. Optionally clone into the active campaign. addCharacterToCampaign
  //    returns the updated campaign term, so success is signalled as a flag
  //    rather than a clone node id.
  let attached = false;
  if (body.campaignId) {
    const clonePayload = await drupalGraphQl<{
      addCharacterToCampaign: { id: string } | null;
    }>(ADD_TO_CAMPAIGN_MUTATION, {
      campaignId:  body.campaignId,
      characterId: source.id,
    });
    if (clonePayload.errors && clonePayload.errors.length > 0) {
      res.status(207).json({
        sourceId: source.id,
        title:    source.title,
        attached: false,
        warning:  `Character created but campaign attach failed: ${clonePayload.errors[0].message}`,
      });
      return;
    }
    attached = clonePayload.data?.addCharacterToCampaign != null;
  }

  res.status(201).json({ sourceId: source.id, title: source.title, attached });
}
