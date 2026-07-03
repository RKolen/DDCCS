/**
 * ConsultScreen — `characters / consult`.
 *
 * Live in-character chat: the message is sent to /api/consult (which streams the
 * character's reply from the creative LLM), and each reply can be spoken aloud
 * through Piper TTS via /api/tts. Character selected from ConsoleContext.
 */

import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import { Icon, AiTag } from '../atoms';

type PlayerCharacter = ReturnType<typeof playerCharacters>[number];

interface VoiceQuery {
  drupal: { termVoiceIds: { nodes: Array<{ name: string }> } };
}

interface ChatMessage {
  role: 'user' | 'char';
  text: string;
}

function charLabel(c: PlayerCharacter): string {
  if (c.sourceCharacter === true)  return `${c.title} · Source`;
  if (c.campaign != null)          return `${c.title} · ${c.campaign}`;
  return c.title;
}

function consultPayload(c: PlayerCharacter, message: string, history: ChatMessage[]): string {
  return JSON.stringify({
    character: {
      name:              c.title,
      species:           c.species,
      lineage:           c.lineage,
      background:        c.background,
      personalityTraits: c.personalityTraits,
      bonds:             c.bonds,
      ideals:            c.ideals,
      flaws:             c.flaws,
    },
    message,
    history: history.map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text })),
  });
}

export function ConsultScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const pcs  = playerCharacters(data);
  const idx  = ctx.charIdx ?? 0;
  const char = pcs[idx] ?? null;

  const voiceData = useStaticQuery<VoiceQuery>(graphql`
    query ConsultVoices { drupal { termVoiceIds(first: 100) { nodes { name } } } }
  `);
  const voiceOptions = React.useMemo(
    () => voiceData.drupal.termVoiceIds.nodes.map(n => n.name).sort((a, b) => a.localeCompare(b)),
    [voiceData],
  );

  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput]       = React.useState('');
  const [sending, setSending]   = React.useState(false);
  const [error, setError]       = React.useState<string | null>(null);
  const [speakingIdx, setSpeakingIdx] = React.useState<number | null>(null);
  const audioRef = React.useRef<HTMLAudioElement | null>(null);
  const threadRef = React.useRef<HTMLDivElement | null>(null);

  const [showVoice, setShowVoice] = React.useState(false);
  const [savingVoice, setSavingVoice] = React.useState(false);
  const [voiceForm, setVoiceForm] = React.useState({ voiceId: '', pitch: 0, speed: 1 });

  // Reset the conversation + voice form when the selected character changes.
  const charId = char?.id ?? '';
  React.useEffect(() => {
    setMessages([]);
    setError(null);
    setShowVoice(false);
    setVoiceForm({
      voiceId: char?.voiceId ?? '',
      pitch:   char?.voicePitch ?? 0,
      speed:   char?.voiceSpeed ?? 1,
    });
  }, [charId, char?.voiceId, char?.voicePitch, char?.voiceSpeed]);

  const previewVoice = async (): Promise<void> => {
    if (!char) return;
    setError(null);
    try {
      const res = await fetch('/api/tts', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          text:    `Greetings. I am ${char.title.split(' ')[0]}.`,
          voiceId: voiceForm.voiceId || char.voiceId || undefined,
          speed:   voiceForm.speed,
          pitch:   voiceForm.pitch,
        }),
      });
      if (!res.ok) throw new Error(`Preview failed (${res.status})`);
      const audio = new Audio(URL.createObjectURL(await res.blob()));
      await audio.play();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const saveVoice = async (): Promise<void> => {
    if (!char) return;
    setSavingVoice(true);
    setError(null);
    try {
      const res = await fetch('/api/update-voice', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          id:         char.id,
          voiceId:    voiceForm.voiceId || null,
          voicePitch: voiceForm.pitch,
          voiceSpeed: voiceForm.speed,
        }),
      });
      if (!res.ok) {
        const payload = (await res.json()) as { error?: string };
        throw new Error(payload.error ?? `Save failed (${res.status})`);
      }
      setShowVoice(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingVoice(false);
    }
  };

  React.useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages]);

  const send = async (): Promise<void> => {
    const message = input.trim();
    if (message === '' || sending || !char) return;
    const history = messages;
    setMessages(prev => [...prev, { role: 'user', text: message }, { role: 'char', text: '' }]);
    setInput('');
    setSending(true);
    setError(null);
    try {
      const res = await fetch('/api/consult', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    consultPayload(char, message, history),
      });
      const reader = res.body?.getReader();
      if (!res.ok || !reader) {
        throw new Error(`Consultation failed (${res.status})`);
      }
      const decoder = new TextDecoder();
      let reply = '';
      let streaming = true;
      while (streaming) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (payload === '[DONE]') { streaming = false; break; }
          try {
            const event = JSON.parse(payload) as { text?: string; error?: string };
            if (event.error) throw new Error(event.error);
            if (event.text) {
              reply += event.text;
              setMessages(prev => {
                const next = [...prev];
                next[next.length - 1] = { role: 'char', text: reply };
                return next;
              });
            }
          } catch (err) {
            if (err instanceof Error && err.message && payload !== '') setError(err.message);
          }
        }
      }
      if (reply.trim() === '') setError('The character had no response.');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const speak = async (text: string, msgIdx: number): Promise<void> => {
    if (speakingIdx !== null) {
      audioRef.current?.pause();
      setSpeakingIdx(null);
      return;
    }
    setSpeakingIdx(msgIdx);
    try {
      const res = await fetch('/api/tts', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          text,
          // Use the live voice-editor values so slider changes are audible
          // immediately (they also persist to Drupal via "Save voice").
          voiceId: voiceForm.voiceId || char?.voiceId || undefined,
          speed:   voiceForm.speed,
          pitch:   voiceForm.pitch,
        }),
      });
      if (!res.ok) throw new Error(`TTS failed (${res.status})`);
      const url = URL.createObjectURL(await res.blob());
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setSpeakingIdx(null); URL.revokeObjectURL(url); };
      await audio.play();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSpeakingIdx(null);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  if (pcs.length === 0) {
    return (
      <div className="screen-consult">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Character consultation <AiTag label="AI" /></span>
            <h2>No characters</h2>
            <p className="screen-blurb">
              No player characters in Drupal. Add Character nodes with Character Type set to on.
            </p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-consult">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Character consultation <AiTag label="AI" /></span>
          <h2>{char?.title ?? 'Select character'}</h2>
          <p className="screen-blurb">
            Speaks in character. Draws on profile, arc state, and recent story appearances.
          </p>
        </div>
        <div className="screen-head-actions">
          {pcs.length > 1 && (
            <select
              className="console-select"
              value={idx}
              onChange={e => setCtx({ ...ctx, charIdx: Number(e.target.value) })}
            >
              {pcs.map((c, i) => <option key={c.id} value={i}>{charLabel(c)}</option>)}
            </select>
          )}
          {char && (
            <button className="ghost-btn" onClick={() => setShowVoice(v => !v)}>
              <Icon name="speaker" size={11} /> Voice
            </button>
          )}
        </div>
      </header>

      {char && showVoice && (
        <div className="voice-editor">
          <div className="voice-field">
            <label className="modal-label" htmlFor="cc-voice">Voice</label>
            <select
              id="cc-voice"
              className="console-select"
              value={voiceForm.voiceId}
              onChange={e => setVoiceForm(f => ({ ...f, voiceId: e.target.value }))}
            >
              <option value="">Default</option>
              {voiceOptions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="voice-field">
            <label className="modal-label" htmlFor="cc-speed">Speed ({voiceForm.speed.toFixed(2)})</label>
            <input id="cc-speed" type="range" min={0.5} max={2} step={0.05}
              value={voiceForm.speed}
              onChange={e => setVoiceForm(f => ({ ...f, speed: Number(e.target.value) }))} />
          </div>
          <div className="voice-field">
            <label className="modal-label" htmlFor="cc-pitch">Pitch ({voiceForm.pitch})</label>
            <input id="cc-pitch" type="range" min={-10} max={10} step={1}
              value={voiceForm.pitch}
              onChange={e => setVoiceForm(f => ({ ...f, pitch: Number(e.target.value) }))} />
          </div>
          <button className="ghost-btn" onClick={() => void previewVoice()}>
            <Icon name="play" size={11} /> Preview
          </button>
          <button className="primary-btn" disabled={savingVoice} onClick={() => void saveVoice()}>
            {savingVoice ? 'Saving…' : 'Save voice'}
          </button>
        </div>
      )}

      {char && (
        <div className="consult-pane">
          <div className="consult-thread" ref={threadRef}>
            {messages.length === 0 && (
              <div className="consult-bubble role-char">
                <span className="bubble-tag">{charLabel(char)} <AiTag /></span>
                <p style={{ fontStyle: 'italic', color: 'var(--ink-dim)' }}>
                  Ask {char.title.split(' ')[0]} anything — they will answer in character.
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`consult-bubble role-${m.role}`}>
                <span className="bubble-tag">
                  {m.role === 'user' ? 'You' : <>{charLabel(char)} <AiTag /></>}
                  {m.role === 'char' && m.text.trim() !== '' && (
                    <button
                      className="tts-btn"
                      title={speakingIdx === i ? 'Stop' : 'Speak'}
                      onClick={() => void speak(m.text, i)}
                    >
                      <Icon name={speakingIdx === i ? 'pause' : 'speaker'} size={11} />
                      {speakingIdx === i ? 'Stop' : 'Speak'}
                    </button>
                  )}
                </span>
                <p style={{ whiteSpace: 'pre-wrap' }}>
                  {m.text || (m.role === 'char' && sending ? '…' : '')}
                </p>
              </div>
            ))}
          </div>

          {error != null && <p className="consult-error">{error}</p>}

          <div className="consult-input">
            <textarea
              placeholder={`Ask ${char.title.split(' ')[0]}...`}
              rows={2}
              value={input}
              disabled={sending}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
            />
            <button className="primary-btn" disabled={sending || input.trim() === ''} onClick={() => void send()}>
              <Icon name="sparkle" size={11} /> {sending ? 'Thinking…' : 'Ask'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
