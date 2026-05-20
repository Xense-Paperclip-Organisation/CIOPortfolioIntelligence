import type { AdvisoryOutput } from '@/types/api';
import { Sparkles, ArrowDown, ArrowUp, ArrowLeftRight, Shield, Plus } from 'lucide-react';

const ACTION_META: Record<string, { icon: any; cls: string; label: string }> = {
  Rebalance: { icon: ArrowLeftRight, cls: 'border-amber-400/40 bg-amber-400/10 text-amber-200', label: 'Rebalance' },
  Diversify: { icon: ArrowLeftRight, cls: 'border-sky-400/40 bg-sky-400/10 text-sky-200', label: 'Diversify' },
  Hold: { icon: Shield, cls: 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200', label: 'Hold' },
  Trim: { icon: ArrowDown, cls: 'border-rose-400/40 bg-rose-400/10 text-rose-200', label: 'Trim' },
  Add: { icon: Plus, cls: 'border-accent-gold/40 bg-accent-gold/10 text-accent-gold', label: 'Add' }
};

export function AdvisoryCard({ advisory }: { advisory: AdvisoryOutput | null }) {
  if (!advisory) return null;
  return (
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
              <button className="self-start rounded-md border border-white/[0.08] bg-white/[0.04] px-2 py-1 text-[11px] font-medium text-accent-steel hover:border-accent-gold/40 hover:text-accent-gold">Discuss with RM</button>
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
