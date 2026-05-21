'use client';

import { useState } from 'react';
import type { AdvisoryOutput } from '@/types/api';
import { Sparkles, ArrowDown, ArrowLeftRight, Shield, Plus, X, CheckCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { CardError, CardEmpty } from '@/components/CardStates';

const ACTION_META: Record<string, { icon: any; cls: string; label: string }> = {
  Rebalance: { icon: ArrowLeftRight, cls: 'border-token-warning/40 bg-token-warning/10 text-warning',   label: 'Rebalance' },
  Diversify: { icon: ArrowLeftRight, cls: 'border-token-info/40 bg-token-info/10 text-info',            label: 'Diversify' },
  Hold:      { icon: Shield,         cls: 'border-token-positive/40 bg-token-positive/10 text-positive', label: 'Hold'      },
  Trim:      { icon: ArrowDown,      cls: 'border-token-negative/40 bg-token-negative/10 text-negative', label: 'Trim'      },
  Add:       { icon: Plus,           cls: 'border-token-accent/40 bg-token-accent/10 text-accent',       label: 'Add'       }
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
        body: JSON.stringify({ holding: rec.target_holding, action: rec.action, reasoning: rec.reasoning, note }),
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="relative w-full max-w-md rounded-xl border border-token-border bg-token-surface p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} className="absolute right-4 top-4 rounded-md p-1 text-token-fg-muted hover:text-token-fg" aria-label="Close">
          <X size={16} />
        </button>
        <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Route to Relationship Manager</h3>
        <p className="mt-2 text-sm font-semibold text-token-fg">{rec.target_holding}</p>
        <p className="mt-1 text-[12px] text-token-fg-muted">{rec.reasoning}</p>
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-token-fg-muted">
              Note to RM (optional)
            </label>
            <textarea
              className="w-full resize-none rounded-md border border-token-border bg-token-surface-elevated px-3 py-2 text-[13px] text-token-fg outline-none placeholder:text-token-fg-muted/50 focus:border-token-accent/50"
              rows={3}
              placeholder="Add context or instructions for the RM…"
              value={note}
              onChange={e => setNote(e.target.value)}
            />
          </div>
          {error && <p className="text-[12px] text-negative">{error}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-md border border-token-border bg-token-surface-elevated px-3 py-1.5 text-[12px] text-token-fg-muted hover:text-token-fg">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="rounded-md border border-token-accent/40 bg-token-accent/10 px-4 py-1.5 text-[12px] font-medium text-accent hover:bg-token-accent/20 disabled:opacity-50">
              {submitting ? 'Sending…' : 'Send to RM'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useState(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  });
  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg border border-token-positive/30 bg-token-surface px-4 py-3 text-[13px] text-positive shadow-xl backdrop-blur-sm">
      <CheckCircle size={15} className="shrink-0" />
      {message}
    </div>
  );
}

export function AdvisoryCard({ advisory, error }: { advisory: AdvisoryOutput | null; error?: string }) {
  const [modalRec, setModalRec] = useState<Rec | null>(null);
  const [toast, setToast] = useState('');

  if (error) return <CardError message={`Advisory unavailable: ${error}`} />;
  if (!advisory) return <CardEmpty message="No advisory data available for this portfolio." />;

  return (
    <>
      <section className="card p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">CIO advisory — what to do</h2>
          <span className="pill border-token-accent/40 bg-token-accent/10 text-accent"><Sparkles size={11} /> Claude Opus · QA-validated</span>
        </div>
        {advisory.headline && <p className="text-base leading-relaxed text-token-fg">{advisory.headline}</p>}
        <div className="mt-3 space-y-3">
          {advisory.recommendations.map((r, i) => {
            const meta = ACTION_META[r.action] ?? ACTION_META.Diversify;
            const Icon = meta.icon;
            return (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-token-border bg-token-surface-elevated p-3">
                <div className={`flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-mono uppercase tracking-wider ${meta.cls}`}>
                  <Icon size={11} /> {meta.label}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-token-fg">{r.target_holding}{typeof r.suggested_size_change === 'number' ? <span className="ml-2 font-mono text-[11px] text-token-fg-muted">size change: {r.suggested_size_change > 0 ? '+' : ''}{r.suggested_size_change.toFixed(1)}%</span> : null}</div>
                  <p className="mt-1 text-[12px] leading-relaxed text-token-fg-muted">{r.reasoning}</p>
                  {r.suggested_replacement && (
                    <div className="mt-1 text-[11px] text-token-fg-muted">Suggested replacement: <span className="text-accent">{r.suggested_replacement}</span></div>
                  )}
                </div>
                <button
                  onClick={() => setModalRec(r)}
                  className="self-start rounded-md border border-token-border bg-token-surface px-2 py-1 text-[11px] font-medium text-token-fg-muted hover:border-token-accent/40 hover:text-accent"
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
          <div className="mt-3 font-mono text-[10px] uppercase tracking-wider text-warning">Offline-mode advisory — set ANTHROPIC_API_KEY for AI voice.</div>
        )}
      </section>

      {modalRec && (
        <DiscussModal rec={modalRec} onClose={() => setModalRec(null)} onSent={() => setToast(`Routed ${modalRec.target_holding} advisory to your RM.`)} />
      )}

      {toast && <Toast message={toast} onDone={() => setToast('')} />}
    </>
  );
}

function Block({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-token-border bg-token-surface-elevated p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-token-fg-muted">{title}</div>
      <p className="mt-1 text-[12px] leading-relaxed text-token-fg">{body}</p>
    </div>
  );
}
