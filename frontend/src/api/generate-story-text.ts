import type { GatsbyFunctionRequest, GatsbyFunctionResponse } from 'gatsby';
import { buildPrompt, targetWords } from '../utils/storyPrompt';
import type { GenerateStoryBody } from '../utils/storyPrompt';

/**
 * Generate a story in one non-streaming call, for the queued story job.
 *
 * POST the same body `generate-story.ts` takes -> `{ text }`. The streaming
 * endpoint exists for the console watching a run live; a queued job has no
 * browser attached, so the Drupal worker calls this and stores the finished
 * text on the job for review when you come back.
 *
 * The prompt comes from the shared `storyPrompt` helper, so a queued story and
 * a streamed one are generated identically.
 */

interface ChatCompletion {
  choices?: Array<{ message?: { content?: string; reasoning_content?: string } }>;
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

  const words = targetWords(body.length);
  // Same 3.5x budget as the streaming path: headroom for residual thinking
  // tokens and to avoid a mid-sentence cutoff on longer stories.
  const maxTokens = Math.ceil(words * 3.5);

  let llmRes: Response;
  try {
    llmRes = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        max_tokens: maxTokens,
        num_ctx:    16384,
        stream:     false,
        think:      false,
        messages:   [{ role: 'user', content: buildPrompt(body) }],
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `LLM unreachable: ${message}` });
    return;
  }

  if (!llmRes.ok) {
    const text = await llmRes.text();
    res.status(llmRes.status).json({ error: `LLM error ${llmRes.status}: ${text}` });
    return;
  }

  let completion: ChatCompletion;
  try {
    completion = (await llmRes.json()) as ChatCompletion;
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    res.status(502).json({ error: `Unreadable response from Drupal: ${detail}` });
    return;
  }
  const message = completion.choices?.[0]?.message;
  // Fall back to reasoning_content if the model ignored /no_think and routed
  // everything through thinking tokens - same tolerance as the stream reader.
  const text = (message?.content || message?.reasoning_content || '').trim();
  if (!text) {
    res.status(502).json({ error: 'The model returned no story text' });
    return;
  }

  res.status(200).json({ text, words });
}
