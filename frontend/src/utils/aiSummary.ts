/**
 * Server-only session-summary helpers.
 *
 * Reads AI credentials from `process.env` and is imported exclusively by the
 * `src/api/` serverless functions (create-story, summarize-session,
 * campaign-overview). NEVER import this into a browser component — it would leak
 * the LLM credentials and pull node-only code into the bundle.
 *
 * The fast model is used deliberately: summaries must be quick and the large
 * creative model spends its whole token budget on extended thinking. `/no_think`
 * plus `think: false` discourages qwen3 reasoning; `stripThink` removes any
 * residual `<think>` block that still leaks through.
 */

/** A single per-session recap keyed by its story number. */
export interface SessionSummary {
  storyNumber: number;
  summary:     string;
}

interface ChatResponse {
  choices?: Array<{ message?: { content?: string } }>;
}

/** Collapse HTML (Drupal `processed` output) or markup into plain prose. */
export function htmlToText(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Read a Drupal text field's `processed` HTML, tolerating both shapes.
 *
 * graphql_compose exposes a cardinality-1 text field as a single object and a
 * cardinality > 1 field (e.g. the paragraph `field_text`, cardinality -1) as a
 * list. This returns the first item's `processed` either way.
 */
export function readProcessed(
  text?: Array<{ processed: string }> | { processed: string } | null,
): string {
  if (Array.isArray(text)) {
    return text[0]?.processed ?? '';
  }
  return text?.processed ?? '';
}

/** Remove any `<think>...</think>` block a thinking model may still emit. */
function stripThink(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
}

async function completeText(system: string, user: string, maxTokens: number): Promise<string> {
  const baseUrl = process.env.AI_FAST_BASE_URL || process.env.AI_CREATIVE_BASE_URL;
  const model = process.env.AI_FAST_MODEL || process.env.AI_CREATIVE_MODEL;
  const apiKey = process.env.OLLAMA_API_KEY;
  if (!baseUrl || !model || !apiKey) {
    throw new Error('AI_FAST_BASE_URL, AI_FAST_MODEL, and OLLAMA_API_KEY must be set in the root .env');
  }

  const res = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      num_ctx:    16384,
      stream:     false,
      think:      false,
      messages: [
        { role: 'system', content: `${system}\n\n/no_think` },
        { role: 'user', content: user },
      ],
    }),
  });

  if (!res.ok) {
    throw new Error(`LLM error ${res.status}: ${await res.text()}`);
  }
  const data = (await res.json()) as ChatResponse;
  return stripThink(data.choices?.[0]?.message?.content ?? '');
}

/** Summarise one session (story body) into a concise 2-4 sentence recap. */
export async function summarizeSession(storyBody: string): Promise<string> {
  const system = [
    'You are a D&D campaign scribe. Summarise a single session into a concise recap',
    'of two to four sentences. Focus on what the party did, key decisions, NPCs met,',
    'and unresolved threads. Write in past tense, third person. Output only the recap',
    'as plain prose, with no preamble, headings, or bullet points.',
  ].join(' ');
  // Budget covers qwen3 residual reasoning tokens plus the short recap so the
  // spoken answer is not truncated before `content` starts.
  return completeText(system, `Session text:\n\n${htmlToText(storyBody)}`, 1200);
}

/** Weave per-session recaps into one flowing "story so far" overview. */
export async function synthesizeOverview(summaries: SessionSummary[]): Promise<string> {
  const ordered = [...summaries].sort((a, b) => a.storyNumber - b.storyNumber);
  const joined = ordered
    .map((s) => `Session ${s.storyNumber}: ${htmlToText(s.summary)}`)
    .join('\n');
  const system = [
    'You are a D&D campaign scribe. Given per-session recaps in order, write a single',
    'flowing "story so far" overview of the campaign in one to three short paragraphs.',
    'Weave the sessions into a continuous narrative; do not list them separately or',
    'label sessions. Write in past tense, third person. Output only the overview prose.',
  ].join(' ');
  // Larger budget: the overview is longer and reasoning overhead is fixed.
  return completeText(system, `Session recaps:\n\n${joined}`, 2000);
}
