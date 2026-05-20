'use client';
import { useState, useRef, useEffect } from 'react';
import { apiFetch } from '@/lib/api';
import { Send, Sparkles } from 'lucide-react';

type Msg = { role: 'user' | 'assistant'; content: string };

export function AskTheCIO() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'assistant', content: "I'm your CIO, briefed on your holdings, allocation alerts and live risk metrics. Ask me anything — e.g. 'what's our biggest concentration risk?' or 'walk me through your rebalance proposal'." }
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => { ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' }); }, [messages]);

  const send = async () => {
    if (!input.trim()) return;
    const user: Msg = { role: 'user', content: input.trim() };
    setInput('');
    setMessages((m) => [...m, user]);
    setBusy(true);
    try {
      const res = await apiFetch<{ reply: Msg }>('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ messages: [...messages, user] })
      });
      setMessages((m) => [...m, res.reply]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: 'assistant', content: `Chat error: ${e?.message ?? 'unknown'}` }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card p-5">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Ask the CIO</h2>
        <span className="pill border-accent-gold/40 bg-accent-gold/10 text-accent-gold"><Sparkles size={11} /> Claude Opus · portfolio-aware</span>
      </div>
      <div ref={ref} className="max-h-72 space-y-3 overflow-y-auto pr-1 text-sm">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[88%] rounded-md px-3 py-2 leading-relaxed ${m.role === 'user' ? 'ml-auto bg-accent-gold/15 text-accent-gold/90' : 'border border-white/[0.06] bg-white/[0.03]'}`}>
            {m.content}
          </div>
        ))}
        {busy && <div className="text-[11px] text-accent-steel">Thinking…</div>}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <input
          className="flex-1 rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-2 text-sm outline-none focus:border-accent-gold/60"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about risk, rebalancing, hedges, scenarios…"
        />
        <button
          onClick={send}
          disabled={busy}
          className="inline-flex items-center gap-1 rounded-md border border-accent-gold/40 bg-accent-gold/10 px-3 py-2 text-xs font-semibold text-accent-gold disabled:opacity-50"
        >
          <Send size={12} /> Send
        </button>
      </div>
    </section>
  );
}
