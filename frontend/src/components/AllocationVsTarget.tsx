'use client';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { AllocationBuckets } from '@/types/api';

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

function Donut({ title, current, target }: { title: string; current: Record<string, number>; target?: Record<string, number> }) {
  const a = toSeries(current);
  const b = target ? toSeries(target) : null;
  return (
    <div className="card p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">{title}</div>
      <div className="mt-2 grid grid-cols-1 gap-3">
        <PieBlock label="Current" data={a} />
        {b && <PieBlock label="Balanced target" data={b} dim />}
      </div>
      {b && (
        <table className="mt-3 w-full text-[11px]">
          <thead className="text-token-fg-muted">
            <tr><th className="text-left">Category</th><th>Current</th><th>Target</th><th>Gap</th></tr>
          </thead>
          <tbody>
            {Array.from(new Set([...Object.keys(current), ...Object.keys(target ?? {})])).sort().map((cat) => {
              const c = current[cat] ?? 0;
              const t = target?.[cat] ?? 0;
              const gap = c - t;
              return (
                <tr key={cat} className="border-t border-token-border">
                  <td className="py-1 text-token-fg">{cat}</td>
                  <td className="metric-num text-right text-token-fg">{c.toFixed(1)}%</td>
                  <td className="metric-num text-right text-token-fg">{t.toFixed(1)}%</td>
                  <td className={`metric-num text-right ${gap > 5 ? 'text-negative' : gap < -5 ? 'text-warning' : 'text-positive'}`}>{gap >= 0 ? '+' : ''}{gap.toFixed(1)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

export function AllocationVsTarget({ allocation, target }: { allocation: AllocationBuckets; target: any }) {
  return (
    <section>
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Allocation vs target</h2>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-4">
        <Donut title="Asset class" current={allocation.asset_class} target={target.asset_class} />
        <Donut title="Geography" current={allocation.geography} target={target.geography} />
        <Donut title="Sector" current={allocation.sector} />
        <Donut title="Currency" current={allocation.currency} target={target.currency} />
      </div>
    </section>
  );
}
