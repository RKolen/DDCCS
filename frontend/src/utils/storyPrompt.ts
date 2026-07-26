/**
 * Story-generation prompt building, shared by the streaming and queued paths.
 *
 * `generate-story.ts` streams a story to the console; `generate-story-text.ts`
 * produces the same story in one non-streaming call for the queued job, which
 * has no browser to stream to. Both must build the identical prompt, so it
 * lives here rather than in either endpoint.
 */

export interface PartyMember {
  name: string;
  characterClass: string | null;
  role: string | null;
  pronouns: string | null;
  species: string | null;
  lineage: string | null;
  background: string | null;
  bonds: string[];
  personalityTraits: string[];
  majorPlotActions: string[];
}

export interface GenerateStoryBody {
  campaignName: string;
  campaignId: string;
  beats: string;
  length: string;
  pov: string;
  storyNumber: number;
  partyNames: string[];
  partyMembers?: PartyMember[];
  location?: string;
  recentStoryTitles: string[];
}

export function targetWords(length: string): number {
  if (length.includes('800')) return 800;
  if (length.includes('1600')) return 1600;
  return 3000;
}

function buildMemberBlock(m: PartyMember): string {
  const speciesPart = [m.lineage, m.species].filter(Boolean).join(' ');
  const classPart = [speciesPart || null, m.characterClass].filter(Boolean).join(' ');
  const header = [m.name, classPart || null, m.role || null, m.pronouns ? `(${m.pronouns})` : null]
    .filter(Boolean).join(' · ');

  const lines = [header];
  if (m.background) lines.push(`  Background: ${m.background}`);
  if (m.personalityTraits.length > 0) lines.push(`  Traits: ${m.personalityTraits.join(', ')}`);
  if (m.bonds.length > 0) lines.push(`  Bonds: ${m.bonds.join(', ')}`);
  if (m.majorPlotActions.length > 0) lines.push(`  Current goals: ${m.majorPlotActions.join(', ')}`);
  return lines.join('\n');
}

function buildPartyLine(body: GenerateStoryBody): string {
  if (body.partyMembers && body.partyMembers.length > 0) {
    const blocks = body.partyMembers.map(buildMemberBlock).join('\n\n');
    return `Characters featured this session (${body.partyMembers.length}):\n\n${blocks}`;
  }
  if (body.partyNames.length > 0) {
    return `Characters featured this session: ${body.partyNames.join(', ')}.`;
  }
  return 'Party composition unknown.';
}

export function buildPrompt(body: GenerateStoryBody): string {
  const words = targetWords(body.length);
  const partyLine = buildPartyLine(body);
  const locationLine = body.location?.trim()
    ? `Setting for this session: ${body.location.trim()}.`
    : '';
  const contextLine = body.recentStoryTitles.length > 0
    ? `Previous sessions in this campaign: ${body.recentStoryTitles.join('; ')}.`
    : '';
  const povLine =
    body.pov === 'Per-character' ? 'Write from a rotating close third-person perspective, one character per scene.' :
      body.pov === 'DM voice' ? 'Write in DM voice — present tense, directed at the players as "you".' :
        'Write in omniscient third-person narrator voice.';

  const lines = [
    `You are a D&D session narrative writer. Write a ${words}-word story for session ${body.storyNumber} of the campaign "${body.campaignName}".`,
    '',
    partyLine,
  ];
  if (locationLine) lines.push(locationLine);
  if (contextLine) lines.push(contextLine);
  lines.push('', povLine, '');
  lines.push(
    'Use the following story beats as your structure (cover all of them):',
    body.beats,
    '',
    'Write a compelling, immersive narrative in the style of high fantasy literary fiction. ' +
    'Use markdown headers (### Heading) to separate major scene breaks. ' +
    'Bold character names on first appearance in each scene (**Name**). ' +
    'Italicise in-world proper nouns (*name*). ' +
    'Do not include a title at the top — begin the narrative directly with the first scene. ' +
    `Target approximately ${words} words. Do not cut off mid-sentence.`,
    '/no_think',
  );

  return lines.join('\n');
}
