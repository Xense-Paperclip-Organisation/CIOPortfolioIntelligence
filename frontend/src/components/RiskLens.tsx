'use client';
import type { Position, RiskMetrics } from '@/types/api';

function corrCellColor(v: number): string {
  // Diverging blue/red palette around 0
  if (v > 0.7) return 'rgba(229,72,77,0.9)';
  if (v > 0.4) return 'rgba(229,72,77,0.55)';
  if (v > 0.1) return 'rgba(229,72,77,0.25)';
  if (v > -0.1) return 'rgba(255,255,255,0.05)';
  if (v > -0.4) return 'rgba(25,184,158,0.3)';
  if (v > -0.7) return 'rgba(25,184,158,0.55)';
  return 'rgba(25,184,158,0.85)';
}

export function RiskLens({ risk, positions }: { risk: RiskMetrics; positions: Position[] }) {
  const port = risk.portfolio || {};
  const corr = risk.correlation || { symbols: [], matrix: [] };
  return (
    <section className="card p-6">
      <h2 className="mb-3 font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Risk Lens · independently computable from daily closes</h2>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Metric label="Portfolio beta" value={port.beta?.toFixed(2) ?? '—'} accent />
        <Metric label="Vol (annualised)" value={port.vol_annualised_pct ? `${port.vol_annualised_pct}%` : '—'} />
        <Metric label="Sharpe 1Y" value={port.sharpe_1y?.toFixed(2) ?? '—'} />
        <Metric label="Max DD 1Y" value={port.max_drawdown_1y_pct ? `${port.max_drawdown_1y_pct}%` : '—'} />
        <Metric label="Expected ret 1Y" value={port.expected_return_annualised_pct ? `${port.expected_return_annualised_pct}%` : '—'} />
      </div>

      {corr.symbols.length > 1 && (
        <div className="mt-6">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Correlation heatmap</div>
          <div className="mt-2 inline-block overflow-hidden rounded-md border border-token-border">
            <table className="text-[10px]">
              <thead>
                <tr>
                  <th className="bg-token-surface px-2 py-1"> </th>
                  {corr.symbols.map((s) => (
                    <th key={s} className="bg-token-surface px-2 py-1 font-mono uppercase tracking-wider text-token-fg-muted">{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {corr.symbols.map((s, i) => (
                  <tr key={s}>
                    <th className="bg-token-surface px-2 py-1 text-right font-mono uppercase tracking-wider text-token-fg-muted">{s}</th>
                    {corr.matrix[i].map((v, j) => (
                      <td key={j} style={{ background: corrCellColor(v) }} className="px-2 py-1 text-center metric-num">{v.toFixed(2)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-[12px]">
          <thead className="text-left font-mono text-[10px] uppercase tracking-wider text-token-fg-muted/80">
            <tr>
              <th className="py-2">Holding</th>
              <th className="py-2 text-right">Beta</th>
              <th className="py-2 text-right">30d Vol (ann.)</th>
              <th className="py-2 text-right">Max DD 1Y</th>
              <th className="py-2 text-right">Sharpe 1Y</th>
            </tr>
          </thead>
          <tbody>
            {positions.filter((p) => p.asset_class === 'Equity' || p.asset_class === 'Commodity').map((p) => {
              const m = risk.per_symbol?.[p.ticker] || {};
              return (
                <tr key={p.ticker} className="border-t border-token-border">
                  <td className="py-2"><span className="font-semibold">{p.ticker}</span> <span className="text-token-fg-muted">{p.name}</span></td>
                  <td className="py-2 text-right metric-num">{m.beta?.toFixed(2) ?? '—'}</td>
                  <td className="py-2 text-right metric-num">{m.vol_30d_annualised ? `${m.vol_30d_annualised}%` : '—'}</td>
                  <td className="py-2 text-right metric-num">{m.max_drawdown_1y_pct ? `${m.max_drawdown_1y_pct}%` : '—'}</td>
                  <td className="py-2 text-right metric-num">{m.sharpe_1y?.toFixed(2) ?? '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-lg border border-token-border bg-token-surface-elevated p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">{label}</div>
      <div className={`metric-num mt-1 text-lg font-semibold ${accent ? 'text-accent' : ''}`}>{value}</div>
    </div>
  );
}
