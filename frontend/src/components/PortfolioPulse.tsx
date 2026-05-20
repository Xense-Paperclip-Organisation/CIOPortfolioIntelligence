import { fmtPct, fmtUsd } from '@/lib/api';
import type { PortfolioBundle, Pulse, RiskMetrics } from '@/types/api';
import { Sparkles } from 'lucide-react';

type Props = { bundle: PortfolioBundle & { risk: RiskMetrics; pulse: Pulse } };

export function PortfolioPulse({ bundle }: Props) {
  const pulse = bundle.pulse;
  const day = bundle.revalued.day_pnl_pct;
  const score = pulse.health_score;
  const toneText = score >= 70 ? 'text-positive' : score >= 45 ? 'text-warning' : 'text-negative';
  const toneBg  = score >= 70 ? 'bg-token-positive' : score >= 45 ? 'bg-token-warning' : 'bg-token-negative';
  const positions = bundle.positions
    .filter((p) => p.asset_class === 'Equity')
    .sort((a, b) => Math.abs((b.quote.day_change_pct || 0)) - Math.abs((a.quote.day_change_pct || 0)))
    .slice(0, 3);

  return (
    <section className="card grid grid-cols-1 gap-6 p-6 lg:grid-cols-[1.6fr_1fr]">
      <div>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Portfolio Pulse</div>
            <div className="metric-num mt-1 font-display text-4xl font-bold text-token-fg">{fmtUsd(bundle.revalued.total_value_usd)}</div>
            <div className={`metric-num mt-1 text-sm ${day >= 0 ? 'text-positive' : 'text-negative'}`}>{fmtPct(day)} today ({fmtUsd(bundle.revalued.day_pnl_usd)})</div>
          </div>
          <div className="text-right">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Health</div>
            <div className={`metric-num mt-1 font-display text-3xl font-bold ${toneText}`}>{score}</div>
            <div className="mt-1 h-1.5 w-32 overflow-hidden rounded-full bg-token-surface-elevated">
              <div className={`h-full ${toneBg}`} style={{ width: `${score}%` }} />
            </div>
          </div>
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-token-fg">{pulse.narrative}</p>
        {pulse.degraded && (
          <div className="mt-2 font-mono text-[10px] uppercase tracking-wider text-warning">
            Narrative running in offline mode — set ANTHROPIC_API_KEY for AI voice.
          </div>
        )}
        <div className="mt-4 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.15em] text-token-fg-muted">
          <Sparkles size={12} className="text-token-accent" /> AI-generated · validated by QAAgent
        </div>
      </div>
      <div className="space-y-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Top movers</div>
        {positions.map((p) => {
          const dp = p.quote.day_change_pct || 0;
          return (
            <div key={p.ticker} className="flex items-center justify-between rounded-lg border border-token-border bg-token-surface-elevated px-3 py-2">
              <div>
                <div className="text-sm font-semibold text-token-fg">{p.ticker}</div>
                <div className="text-[11px] text-token-fg-muted">{p.name}</div>
              </div>
              <div className={`metric-num text-sm ${dp >= 0 ? 'text-positive' : 'text-negative'}`}>{fmtPct(dp)}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
