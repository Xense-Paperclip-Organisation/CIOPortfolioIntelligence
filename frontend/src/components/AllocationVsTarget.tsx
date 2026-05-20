'use client';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { AllocationBuckets } from '@/types/api';

const PALETTE = ['#C8A95A', '#19B89E', '#7DA9FF', '#E5484D', '#F1A33F', '#9C6FE5', '#5C6BC0', '#26C6DA', '#FF7043'];

function toSeries(record: Record<string, number>) {
  return Object.entries(record).map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }));
}

function Donut({ title, current, target }: { title: string; current: Record<string, number>; target?: Record<string, number> }) {
  const a = toSeries(current);
  const b = target ? toSeries(target) : null;
  return (
    <div className="card p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">{title}</div>
      <div className="mt-1 grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="h-56">
          <div className="text-[11px] text-accent-steel/80">Current</div>
          <ResponsiveContainer>
            <PieChart>
              <Pie data={a} dataKey="value" innerRadius={50} outerRadius={80} stroke="none" paddingAngle={1}>
                {a.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0F1620', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6 }}
                formatter={(v) => `${v}%`}
              />
              <Legend wrapperStyle={{ fontSize: 10, color: '#A3B0C5' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {b && (
          <div className="h-56">
            <div className="text-[11px] text-accent-steel/80">Balanced target</div>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={b} dataKey="value" innerRadius={50} outerRadius={80} stroke="none" paddingAngle={1}>
                  {b.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} opacity={0.55} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0F1620', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6 }}
                  formatter={(v) => `${v}%`}
                />
                <Legend wrapperStyle={{ fontSize: 10, color: '#A3B0C5' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      {b && (
        <table className="mt-2 w-full text-[11px]">
          <thead className="text-accent-steel/80">
            <tr><th className="text-left">Category</th><th>Current</th><th>Target</th><th>Gap</th></tr>
          </thead>
          <tbody>
            {Array.from(new Set([...Object.keys(current), ...Object.keys(target ?? {})])).sort().map((cat) => {
              const c = current[cat] ?? 0;
              const t = target?.[cat] ?? 0;
              const gap = c - t;
              return (
                <tr key={cat} className="border-t border-white/[0.05]">
                  <td className="py-1 text-ink-100">{cat}</td>
                  <td className="metric-num text-right">{c.toFixed(1)}%</td>
                  <td className="metric-num text-right">{t.toFixed(1)}%</td>
                  <td className={`metric-num text-right ${gap > 5 ? 'text-rose-300' : gap < -5 ? 'text-amber-300' : 'text-emerald-300'}`}>{gap >= 0 ? '+' : ''}{gap.toFixed(1)}%</td>
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
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Allocation vs target</h2>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-4">
        <Donut title="Asset class" current={allocation.asset_class} target={target.asset_class} />
        <Donut title="Geography" current={allocation.geography} target={target.geography} />
        <Donut title="Sector" current={allocation.sector} />
        <Donut title="Currency" current={allocation.currency} target={target.currency} />
      </div>
    </section>
  );
}
