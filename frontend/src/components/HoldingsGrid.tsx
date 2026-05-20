'use client';
import { Fragment, useState } from 'react';
import { fmtPct, fmtUsd } from '@/lib/api';
import type { Position } from '@/types/api';
import { HoldingDetail } from './HoldingDetail';
import { ChevronDown, ChevronRight } from 'lucide-react';

function hasIntraday(p: Position): boolean {
  return p.asset_class !== 'Cash';
}

function riskBadge(p: Position) {
  if (p.asset_class === 'Cash') return { label: 'CASH', cls: 'pill-neu' };
  if (p.asset_class === 'Fixed Income') return { label: 'LOW VOL', cls: 'pill-pos' };
  const vol = Math.abs(p.quote.week_change_pct || 0);
  if (vol > 6) return { label: 'HIGH VOL', cls: 'pill-neg' };
  if (vol > 3) return { label: 'MED VOL', cls: 'pill-warn' };
  return { label: 'LOW VOL', cls: 'pill-pos' };
}

export function HoldingsGrid({ positions }: { positions: Position[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  return (
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.05] px-5 py-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Holdings · live prices</div>
        <div className="text-[10px] text-accent-steel/70">Click row to expand chart + AI explanation</div>
      </div>
      <table className="w-full text-sm">
        <thead className="text-left font-mono text-[10px] uppercase tracking-wider text-accent-steel/80">
          <tr>
            <th className="px-5 py-2"> </th>
            <th className="py-2">Holding</th>
            <th className="py-2 text-right">Price</th>
            <th className="py-2 text-right">Day</th>
            <th className="py-2 text-right">Week</th>
            <th className="py-2 text-right">Value (USD)</th>
            <th className="py-2 text-right">Weight</th>
            <th className="py-2 text-right">Risk</th>
            <th className="py-2 text-right pr-5">Source</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => {
            const dp = p.quote.day_change_pct ?? 0;
            const wp = p.quote.week_change_pct ?? 0;
            const badge = riskBadge(p);
            const isOpen = expanded === p.ticker;
            const canExpand = hasIntraday(p);
            return (
              <Fragment key={p.ticker}>
                <tr
                  className={`border-t border-white/[0.04] ${canExpand ? 'cursor-pointer hover:bg-white/[0.03]' : ''} ${isOpen ? 'bg-white/[0.03]' : ''}`}
                  onClick={() => canExpand && setExpanded(isOpen ? null : p.ticker)}
                >
                  <td className="px-5 py-3 text-accent-steel">
                    {canExpand ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <span className="inline-block w-[14px]" />}
                  </td>
                  <td className="py-3">
                    <div className="font-semibold">{p.ticker}</div>
                    <div className="text-[11px] text-accent-steel">{p.name} · {p.geography}{p.sector ? ` · ${p.sector}` : ''}</div>
                  </td>
                  <td className="py-3 text-right metric-num" title={!canExpand ? 'Cash positions do not move intraday' : undefined}>{canExpand ? p.quote.price?.toFixed(2) : '—'}</td>
                  <td className={`py-3 text-right metric-num ${canExpand ? (dp >= 0 ? 'text-emerald-300' : 'text-rose-300') : 'text-accent-steel/50'}`} title={!canExpand ? 'Cash positions do not move intraday' : undefined}>{canExpand ? fmtPct(dp) : '—'}</td>
                  <td className={`py-3 text-right metric-num ${canExpand ? (wp >= 0 ? 'text-emerald-300' : 'text-rose-300') : 'text-accent-steel/50'}`} title={!canExpand ? 'Cash positions do not move intraday' : undefined}>{canExpand ? fmtPct(wp) : '—'}</td>
                  <td className="py-3 text-right metric-num">{fmtUsd(p.value_usd, { compact: true })}</td>
                  <td className="py-3 text-right metric-num">{p.weight_pct.toFixed(1)}%</td>
                  <td className="py-3 text-right"><span className={`pill ${badge.cls}`}>{badge.label}</span></td>
                  <td className="py-3 pr-5 text-right font-mono text-[10px] uppercase tracking-wider text-accent-steel/80">
                    {p.quote.synthesized ? <span className="text-amber-300">synth</span> : 'live'}
                  </td>
                </tr>
                {isOpen && (
                  <tr>
                    <td colSpan={9} className="bg-ink-950/60 px-5 py-4">
                      <HoldingDetail ticker={p.ticker} position={p} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
