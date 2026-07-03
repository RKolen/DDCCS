import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';

/**
 * Character consultation chat.
 *
 * Builds an in-character system prompt from the character's profile and streams
 * the reply from the creative LLM as Server-Sent Events (`data: {text}` chunks,
 * terminated by `data: [DONE]`), mirroring generate-story.ts.
 */

interface ConsultCharacter {
  name:              string;
  characterClass?:   string | null;
  species?:          string | null;
  lineage?:          string | null;
  pronouns?:         string | null;
  background?:       string | null;
  personalityTraits?: string[];
  bonds?:            string[];
  ideals?:           string[];
  flaws?:            string[];
  backstory?:        string | null;
}

interface ConsultMessage {
  role:    'user' | 'assistant';
  content: string;
}

interface ConsultBody {
  character: ConsultCharacter;
  message:   string;
  history?:  ConsultMessage[];
}

function bulletLine(label: string, values?: string[]): string {
  return values && values.length > 0 ? `${label}: ${values.join('; ')}.` : '';
}

function buildSystemPrompt(c: ConsultCharacter): string {
  const descriptor = [c.lineage, c.species, c.characterClass].filter(Boolean).join(' ');
  const lines = [
    `You are ${c.name}${descriptor ? `, a ${descriptor}` : ''}.`,
    c.pronouns ? `Your pronouns are ${c.pronouns}.` : '',
    c.background ? `Background: ${c.background}.` : '',
    bulletLine('Personality', c.personalityTraits),
    bulletLine('Ideals', c.ideals),
    bulletLine('Bonds', c.bonds),
    bulletLine('Flaws', c.flaws),
    c.backstory?.trim() ? `Backstory: ${c.backstory.trim()}` : '',
    '',
    `Stay fully in character as ${c.name}. Reply in the first person, in your own`,
    'voice, drawing on your personality, ideals, bonds, and flaws. Keep replies',
    'conversational — one to three short paragraphs. Never break character, never',
    'mention being an AI, and never describe yourself in the third person.',
  ];
  return lines.filter(Boolean).join('\n');
}

export default async function handler(
  req: GatsbyFunctionRequest,
  res: GatsbyFunctionResponse,
): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  // Prefer the fast model: a chat reply must be snappy, and the large creative
  // model spends its whole budget on extended thinking before answering.
  const baseUrl = process.env.AI_FAST_BASE_URL || process.env.AI_CREATIVE_BASE_URL;
  const model = process.env.AI_FAST_MODEL || process.env.AI_CREATIVE_MODEL;
  const apiKey = process.env.OLLAMA_API_KEY;
  if (!baseUrl || !model || !apiKey) {
    res.status(500).json({ error: 'AI_FAST_BASE_URL, AI_FAST_MODEL, and OLLAMA_API_KEY must be set in the root .env' });
    return;
  }

  const body = req.body as ConsultBody;
  if (!body?.character?.name || !body?.message?.trim()) {
    res.status(400).json({ error: 'character.name and message are required' });
    return;
  }

  const messages = [
    // /no_think discourages qwen3 extended thinking (belt-and-suspenders with
    // think:false); the token budget still allows for any residual thinking.
    { role: 'system', content: `${buildSystemPrompt(body.character)}\n\n/no_think` },
    ...(body.history ?? []).slice(-12),
    { role: 'user', content: body.message.trim() },
  ];

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  let llmRes: Response;
  try {
    llmRes = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        // Budget covers residual thinking tokens plus the spoken reply so the
        // answer is not cut off before `content` starts streaming.
        model,
        max_tokens: 1600,
        num_ctx: 16384,
        stream: true,
        think: false,
        messages,
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
            choices?: Array<{ delta?: { content?: string; reasoning_content?: string } }>;
          };
          const delta = event.choices?.[0]?.delta;
          const text = delta?.content || delta?.reasoning_content;
          if (text) res.write(`data: ${JSON.stringify({ text })}\n\n`);
        } catch {
          // skip malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  res.write('data: [DONE]\n\n');
  res.end();
}
