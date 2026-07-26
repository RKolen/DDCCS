import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { buildPrompt, targetWords } from '../utils/storyPrompt';
import type { GenerateStoryBody } from '../utils/storyPrompt';

/**
 * Stream an AI-generated story to the console (SSE).
 *
 * The prompt is built by the shared `storyPrompt` helper so the queued,
 * non-streaming path (`generate-story-text.ts`) produces the same story.
 */

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
