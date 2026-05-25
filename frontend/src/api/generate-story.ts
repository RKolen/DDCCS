import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

interface PartyMember {
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

interface GenerateStoryBody {
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

function targetWords(length: string): number {
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

function buildPrompt(body: GenerateStoryBody): string {
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
    // /no_think disables qwen3 extended-thinking mode at the message level
    // (belt-and-suspenders with think:false in the API call).
    '/no_think',
  );

  return lines.join('\n');
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const baseUrl = process.env.AI_CREATIVE_BASE_URL;
  const model = process.env.AI_CREATIVE_MODEL;
  const apiKey = process.env.OLLAMA_API_KEY;

  if (!baseUrl || !model || !apiKey) {
    res.status(500).json({ error: 'AI_CREATIVE_BASE_URL, AI_CREATIVE_MODEL, and OLLAMA_API_KEY must be set in the root .env' });
    return;
  }

  const body = req.body as GenerateStoryBody;
  if (!body?.beats?.trim()) {
    res.status(400).json({ error: 'beats are required' });
    return;
  }
  if ((body.partyNames?.length ?? 0) === 0 && (body.partyMembers?.length ?? 0) === 0) {
    res.status(400).json({ error: 'At least one featured character is required' });
    return;
  }

  const prompt = buildPrompt(body);
  const words = targetWords(body.length);
  // 3.5× budget: 2.2 chars/token for the story itself, plus ~1.3× headroom for
  // any residual thinking tokens even when /no_think is set, and to avoid
  // mid-sentence cutoff on longer stories with many characters.
  const maxTokens = Math.ceil(words * 3.5);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  let llmRes: Response;
  try {
    llmRes = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        num_ctx: 16384,
        stream: true,
        think: false,
        messages: [{ role: 'user', content: prompt }],
      }),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.write(`data: ${JSON.stringify({ error: `LLM unreachable: ${msg}` })}\n\n`);
    res.end();
    return;
  }

  if (!llmRes.ok) {
    const text = await llmRes.text();
    res.write(`data: ${JSON.stringify({ error: `LLM error ${llmRes.status}: ${text}` })}\n\n`);
    res.end();
    return;
  }

  const reader = llmRes.body?.getReader();
  if (!reader) {
    res.write(`data: ${JSON.stringify({ error: 'No response body from LLM' })}\n\n`);
    res.end();
    return;
  }

  const decoder = new TextDecoder();
  let contentReceived = false;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') continue;
        try {
          const event = JSON.parse(payload) as {
            choices?: Array<{
              delta?: { content?: string; reasoning_content?: string };
            }>;
          };
          const delta = event.choices?.[0]?.delta;
          // Prefer content; fall back to reasoning_content if the model
          // ignored /no_think and routed all output through thinking tokens.
          const text = delta?.content || delta?.reasoning_content;
          if (text) {
            contentReceived = true;
            res.write(`data: ${JSON.stringify({ text })}\n\n`);
          }
        } catch {
          // skip malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  if (!contentReceived) {
    res.write(`data: ${JSON.stringify({ error: `Model returned no content. Check that "${model}" is loaded in Ollama and that thinking mode is not consuming all tokens.` })}\n\n`);
  }

  res.write('data: [DONE]\n\n');
  res.end();
}
