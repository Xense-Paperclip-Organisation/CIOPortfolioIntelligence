'use client';

import { useState } from 'react';
import type { AdvisoryOutput } from '@/types/api';
import { Sparkles, ArrowDown, ArrowUp, ArrowLeftRight, Shield, Plus, X, CheckCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

const ACTION_META: Record<string, { icon: any; cls: string; label: string }> = {
  Rebalance: { icon: ArrowLeftRight, cls: 'border-amber-400/40 bg-amber-400/10 text-amber-200', label: 'Rebalance' },
  Diversify: { icon: ArrowLeftRight, cls: 'border-sky-400/40 bg-sky-400/10 text-sky-200', label: 'Diversify' },
  Hold: { icon: Shield, cls: 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200', label: 'Hold' },
  Trim: { icon: ArrowDown, cls: 'border-rose-400/40 bg-rose-400/10 text-rose-200', label: 'Trim' },
  Add: { icon: Plus, cls: 'border-accent-gold/40 bg-accent-gold/10 text-accent-gold', label: 'Add' }
};

type Rec = AdvisoryOutput['recommendations'][number];

function DiscussModal({ rec, onClose, onSent }: { rec: Rec; onClose: () => void; onSent: () => void }) {
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await apiFetch('/rm-route', {
        method: 'POST',
        body: JSON.stringify({
          holding: rec.target_holding,
          action: rec.action,
          reasoning: rec.reasoning,
          note,
        }),
      });
      onSent();
      onClose();
    } catch (err: any) {
      setError(err?.message ?? 'Failed to route to RM.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md rounded-xl border border-white/[0.08] bg-[#0e1623] p-6 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-md p-1 text-accent-steel hover:text-white"
          aria-label="Close"
        >
          <X size={16} />
        </button>

        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Route to Relationship Manager</h3>
        <p className="mt-2 text-sm font-semibold">{rec.target_holding}</p>
        <p className="mt-1 text-[12px] text-ink-100/80">{rec.reasoning}</p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-accent-steel">
              Note to RM (optional)
            </label>
            <textarea
              className="w-full rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-2 text-[13px] text-white outline-none focus:border-accent-gold/50 focus:ring-0 resize-none"
              rows={3}
              placeholder="Add context or instructions for the RM…"
              value={note}
              onChange={e => setNote(e.target.value)}
            />
          </div>

          {error && (
            <p className="text-[12px] text-rose-400">{error}</p>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-[12px] text-accent-steel hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md border border-accent-gold/40 bg-accent-gold/10 px-4 py-1.5 text-[12px] font-medium text-accent-gold hover:bg-accent-gold/20 disabled:opacity-50"
            >
              {submitting ? 'Sending…' : 'Send to RM'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  // Auto-dismiss after 3 s
  useState(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  });

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-900/80 px-4 py-3 text-[13px] text-emerald-200 shadow-xl backdrop-blur-sm">
      <CheckCircle size={15} className="shrink-0" />
      {message}
    </div>
  );
}

export function AdvisoryCard({ advisory }: { advisory: AdvisoryOutput | null }) {
  const [modalRec, setModalRec] = useState<Rec | null>(null);
  const [toast, setToast] = useState('');

  if (!advisory) return null;

  return (
    <>
      <section className="card p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">CIO advisory — what to do</h2>
          <span className="pill border-accent-gold/40 bg-accent-gold/10 text-accent-gold"><Sparkles size={11} /> Claude Opus · QA-validated</span>
        </div>
        {advisory.headline && <p className="text-base leading-relaxed">{advisory.headline}</p>}
        <div className="mt-3 space-y-3">
          {advisory.recommendations.map((r, i) => {
            const meta = ACTION_META[r.action] ?? ACTION_META.Diversify;
            const Icon = meta.icon;
            return (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-white/[0.05] bg-white/[0.02] p-3">
                <div className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-mono uppercase tracking-wider ${meta.cls}`}>
                  <Icon size={11} /> {meta.label}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">{r.target_holding}{typeof r.suggested_size_change === 'number' ? <span className="ml-2 font-mono text-[11px] text-accent-steel">size change: {r.suggested_size_change > 0 ? '+' : ''}{r.suggested_size_change.toFixed(1)}%</span> : null}</div>
                  <p className="mt-1 text-[12px] leading-relaxed text-ink-100/90">{r.reasoning}</p>
                  {r.suggested_replacement && (
                    <div className="mt-1 text-[11px] text-accent-steel">Suggested replacement: <span className="text-accent-gold">{r.suggested_replacement}</span></div>
                  )}
                </div>
                <button
                  onClick={() => setModalRec(r)}
                  className="self-start rounded-md border border-white/[0.08] bg-white/[0.04] px-2 py-1 text-[11px] font-medium text-accent-steel hover:border-accent-gold/40 hover:text-accent-gold"
                >
                  Discuss with RM
                </button>
              </div>
            );
          })}
        </div>
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Block title="Diversification gap" body={advisory.diversification_gap_analysis} />
          <Block title="Currency exposure" body={advisory.currency_commentary} />
          <Block title="Education-funding stress" body={advisory.education_funding_stress} />
        </div>
        {advisory.degraded && (
          <div className="mt-3 font-mono text-[10px] uppercase tracking-wider text-amber-300">Offline-mode advisory — set ANTHROPIC_API_KEY for AI voice.</div>
        )}
      </section>

      {modalRec && (
        <DiscussModal
          rec={modalRec}
          onClose={() => setModalRec(null)}
          onSent={() => setToast(`Routed ${modalRec.target_holding} advisory to your RM.`)}
        />
      )}

      {toast && <Toast message={toast} onDone={() => setToast('')} />}
    </>
  );
}

function Block({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-white/[0.05] bg-white/[0.02] p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-accent-steel">{title}</div>
      <p className="mt-1 text-[12px] leading-relaxed text-ink-100/90">{body}</p>
    </div>
  );
}
