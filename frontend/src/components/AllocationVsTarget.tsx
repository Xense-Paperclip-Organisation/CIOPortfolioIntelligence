'use client';
import { Fragment, useCallback, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { AllocationBuckets, Position } from '@/types/api';
import { fmtUsd } from '@/lib/api';

type BucketDim = 'asset_class' | 'geography' | 'sector' | 'currency';

function holdingsInBucket(positions: Position[], dim: BucketDim, key: string): Position[] {
  return positions
    .filter((p) => {
      const v = (p as any)[dim];
      if (v == null) return key === '—';
      return String(v) === key;
    })
    .sort((a, b) => b.weight_pct - a.weight_pct);
}

const PALETTE = ['#C8A95A', '#19B89E', '#7DA9FF', '#E5484D', '#F1A33F', '#9C6FE5', '#5C6BC0', '#26C6DA', '#FF7043'];

function toSeries(record: Record<string, number>) {
  return Object.entries(record).map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }));
}

const TOOLTIP_WRAPPER_STYLE: React.CSSProperties = {
  zIndex: 50,
  outline: 'none',
};

const TOOLTIP_CONTENT_STYLE: React.CSSProperties = {
  background: 'var(--surface-elevated)',
  border: '1px solid var(--border-strong)',
  borderRadius: 8,
  color: 'var(--fg)',
  fontSize: 12,
  padding: '6px 10px',
  boxShadow: '0 8px 24px rgba(0,0,0,0.28)',
  opacity: 1,
};

const TOOLTIP_ITEM_STYLE: React.CSSProperties = {
  color: 'var(--fg)',
};

const TOOLTIP_LABEL_STYLE: React.CSSProperties = {
  color: 'var(--fg-muted)',
  fontSize: 11,
};

const LEGEND_WRAPPER_STYLE: React.CSSProperties = {
  fontSize: 10,
  color: 'var(--fg-muted)',
  paddingTop: 4,
  lineHeight: 1.3,
};

// Recharts margin gives the pie inner padding so the outer ring is never clipped
// by the SVG viewport at narrow card widths.
const PIE_CHART_MARGIN = { top: 8, right: 12, bottom: 8, left: 12 };

function PieBlock({ label, data, dim }: { label: string; data: { name: string; value: number }[]; dim?: boolean }) {
  return (
    <div className="flex h-64 flex-col">
      <div className="text-[11px] text-token-fg-muted">{label}</div>
      <div className="min-h-0 flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={PIE_CHART_MARGIN}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="46%"
              innerRadius="48%"
              outerRadius="78%"
              stroke="none"
              paddingAngle={1}
              isAnimationActive={false}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} opacity={dim ? 0.55 : 1} />
              ))}
            </Pie>
            <Tooltip
              wrapperStyle={TOOLTIP_WRAPPER_STYLE}
              contentStyle={TOOLTIP_CONTENT_STYLE}
              itemStyle={TOOLTIP_ITEM_STYLE}
              labelStyle={TOOLTIP_LABEL_STYLE}
              cursor={{ fill: 'var(--border)' }}
              formatter={(v: number, name: string) => [`${v}%`, name]}
            />
            <Legend
              verticalAlign="bottom"
              align="center"
              iconSize={8}
              iconType="circle"
              wrapperStyle={LEGEND_WRAPPER_STYLE}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function Donut({
  title,
  dim,
  current,
  target,
  positions
}: {
  title: string;
  dim: BucketDim;
  current: Record<string, number>;
  target?: Record<string, number>;
  positions: Position[];
}) {
  const a = toSeries(current);
  const b = target ? toSeries(target) : null;

  const categories = useMemo(
    () => Array.from(new Set([...Object.keys(current), ...Object.keys(target ?? {})])).sort(),
    [current, target]
  );

  // Only categories with actual holdings get a drill-in (avoid dead clicks).
  const drillable = useMemo(() => {
    const m = new Map<string, Position[]>();
    for (const cat of categories) {
      const list = holdingsInBucket(positions, dim, cat);
      if (list.length) m.set(cat, list);
    }
    return m;
  }, [categories, dim, positions]);

  const navigable = useMemo(() => categories.filter((c) => drillable.has(c)), [categories, drillable]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const rowRefs = useRef<Map<string, HTMLTableRowElement>>(new Map());

  const focusRow = useCallback((cat: string | null) => {
    if (!cat) return;
    rowRefs.current.get(cat)?.focus();
  }, []);

  const onKey = useCallback(
    (e: KeyboardEvent<HTMLTableRowElement>, cat: string) => {
      const i = navigable.indexOf(cat);
      if (i < 0) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        focusRow(navigable[Math.min(i + 1, navigable.length - 1)]);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        focusRow(navigable[Math.max(i - 1, 0)]);
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        setExpanded((cur) => (cur === cat ? null : cat));
      } else if (e.key === 'Escape' && expanded === cat) {
        e.preventDefault();
        setExpanded(null);
      }
    },
    [navigable, focusRow, expanded]
  );

  const colCount = b ? 5 : 4;

  return (
    <div className="card p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">{title}</div>
      <div className="mt-2 grid grid-cols-1 gap-3">
        <PieBlock label="Current" data={a} />
        {b && <PieBlock label="Balanced target" data={b} dim />}
      </div>
      <table
        className="mt-3 w-full text-[11px]"
        role="grid"
        aria-label={`${title} buckets — click a row to see the holdings`}
      >
        <thead className="text-token-fg-muted">
          <tr>
            <th className="w-4"></th>
            <th className="text-left">Category</th>
            <th>Current</th>
            {b && <th>Target</th>}
            {b && <th>Gap</th>}
          </tr>
        </thead>
        <tbody>
          {categories.map((cat) => {
            const c = current[cat] ?? 0;
            const t = target?.[cat] ?? 0;
            const gap = c - t;
            const list = drillable.get(cat);
            const canDrill = !!list;
            const isOpen = expanded === cat;
            const interactive = canDrill
              ? {
                  role: 'button' as const,
                  tabIndex: 0,
                  'aria-expanded': isOpen,
                  'aria-label': `${cat}: ${c?.toFixed(1) ?? '0'}% of portfolio. ${isOpen ? 'Collapse' : 'Expand'} to see ${list?.length ?? 0} holding${list?.length === 1 ? '' : 's'}.`,
                  onClick: () => setExpanded(isOpen ? null : cat),
                  onKeyDown: (e: KeyboardEvent<HTMLTableRowElement>) => onKey(e, cat),
                  ref: (el: HTMLTableRowElement | null) => {
                    if (el) rowRefs.current.set(cat, el);
                    else rowRefs.current.delete(cat);
                  }
                }
              : {};
            return (
              <Fragment key={cat}>
                <tr
                  className={`border-t border-token-border outline-none ${canDrill ? 'cursor-pointer hover:bg-token-surface-elevated focus-visible:bg-token-surface-elevated' : ''} ${isOpen ? 'bg-token-surface-elevated' : ''}`}
                  {...interactive}
                >
                  <td className="py-1 pr-1 text-token-fg-muted">
                    {canDrill ? (isOpen ? <ChevronDown size={11} /> : <ChevronRight size={11} />) : null}
                  </td>
                  <td className="py-1 text-token-fg">{cat}</td>
                  <td className="metric-num text-right text-token-fg">{c?.toFixed(1) ?? '—'}%</td>
                  {b && <td className="metric-num text-right text-token-fg">{t?.toFixed(1) ?? '—'}%</td>}
                  {b && (
                    <td className={`metric-num text-right ${gap > 5 ? 'text-negative' : gap < -5 ? 'text-warning' : 'text-positive'}`}>
                      {gap >= 0 ? '+' : ''}
                      {gap?.toFixed(1) ?? '—'}%
                    </td>
                  )}
                </tr>
                {isOpen && list && (
                  <tr>
                    <td colSpan={colCount} className="bg-token-bg px-2 py-2">
                      <div className="font-mono text-[10px] uppercase tracking-wider text-token-fg-muted">
                        Holdings in “{cat}”
                      </div>
                      <ul className="mt-1 space-y-1">
                        {list.map((p) => (
                          <li
                            key={p.ticker}
                            className="flex items-center justify-between gap-2 rounded-md border border-token-border bg-token-surface px-2 py-1"
                          >
                            <div className="min-w-0">
                              <div className="truncate font-semibold text-token-fg">{p.ticker}</div>
                              <div className="truncate text-[10px] text-token-fg-muted">{p.name}</div>
                            </div>
                            <div className="text-right">
                              <div className="metric-num text-token-fg">{p.weight_pct?.toFixed(1) ?? '—'}%</div>
                              <div className="metric-num text-[10px] text-token-fg-muted">
                                {fmtUsd(p.value_usd, { compact: true })}
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function AllocationVsTarget({
  allocation,
  target,
  positions
}: {
  allocation: AllocationBuckets;
  target: any;
  positions: Position[];
}) {
  return (
    <section>
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Allocation vs target</h2>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-4">
        <Donut title="Asset class" dim="asset_class" current={allocation.asset_class} target={target?.asset_class} positions={positions} />
        <Donut title="Geography"   dim="geography"   current={allocation.geography}   target={target?.geography}   positions={positions} />
        <Donut title="Sector"      dim="sector"      current={allocation.sector}                                                  positions={positions} />
        <Donut title="Currency"    dim="currency"    current={allocation.currency}    target={target?.currency}    positions={positions} />
      </div>
    </section>
  );
}
