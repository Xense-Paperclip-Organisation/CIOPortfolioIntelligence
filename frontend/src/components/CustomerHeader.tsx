import { fmtAed, fmtPct } from '@/lib/api';
import type { PortfolioBundle, MacroSnapshot, RiskMetrics, Pulse } from '@/types/api';

type Props = {
  bundle: PortfolioBundle & { risk: RiskMetrics; pulse: Pulse };
  macro: MacroSnapshot | null;
};

export function CustomerHeader({ bundle, macro }: Props) {
  const dayPnlPct = bundle.revalued.day_pnl_pct;
  const holdingsCount = bundle.positions.length;
  const assetClasses = Array.from(new Set(bundle.positions.map((p) => p.asset_class)));
  const currencies = Array.from(new Set(bundle.positions.map((p) => p.currency)));
  return (
    <section className="card flex flex-col gap-4 p-6 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-4">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-accent-gold/80 to-amber-200/40 font-display text-xl font-bold text-ink-950">
          AA
        </div>
        <div>
          <div className="font-display text-xl font-bold tracking-tight text-token-fg">Ahmed Al-Mansouri</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-token-fg-muted">
            <span className="pill border-token-accent/40 bg-token-accent/10 text-token-accent">Balanced — Moderate Growth</span>
            <span>· Dubai, UAE · Senior engineering manager</span>
          </div>
          <div className="mt-1 text-[11px] text-token-fg-muted/80">
            Goal: retirement at 60 + children&apos;s education in 8 years · Horizon 10–15Y · Liability currencies AED + USD
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-right md:grid-cols-4">
        <Metric label="Portfolio (AED)" value={fmtAed(bundle.revalued.total_value_aed, { compact: true })} />
        <Metric label="Day P&L" value={fmtPct(dayPnlPct)} tone={dayPnlPct >= 0 ? 'pos' : 'neg'} />
        <Metric label="Holdings" value={String(holdingsCount)} />
        <Metric label="USD/AED" value={macro?.fx_usd_aed?.toFixed(4) ?? '—'} />
        <Metric label="UST 10Y" value={macro?.us_treasury_yield_curve?.['10Y']?.toFixed(2) ?? '—'} suffix="%" />
        <Metric label="US CPI YoY" value={macro?.us_cpi_yoy_pct?.toFixed(1) ?? '—'} suffix="%" />
        <Metric label="Asset classes" value={String(assetClasses.length)} />
        <Metric label="Currencies" value={String(currencies.length)} />
      </div>
    </section>
  );
}

function Metric({ label, value, suffix, tone }: { label: string; value: string; suffix?: string; tone?: 'pos' | 'neg' }) {
  const toneClass = tone === 'pos' ? 'text-positive' : tone === 'neg' ? 'text-negative' : 'text-token-fg';
  return (
    <div className="text-left">
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-token-fg-muted">{label}</div>
      <div className={`metric-num text-base font-semibold ${toneClass}`}>{value}{suffix ?? ''}</div>
    </div>
  );
}
