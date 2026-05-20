'use client';
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { apiFetch } from '@/lib/api';
import type { ScenarioResult } from '@/types/api';

export function ScenarioSimulator() {
  const [scenarios, setScenarios] = useState<{ id: string; label: string; description: string }[]>([]);
  const [activeId, setActiveId] = useState<string>('us-tech-drawdown');
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<{ scenarios: any[] }>('/api/scenarios').then((d) => setScenarios(d.scenarios)).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    // Use GET so the request works through GET-only reverse-proxies (e.g. xense.dev plugin proxy).
    apiFetch<ScenarioResult>(`/api/scenarios/run?scenario_id=${encodeURIComponent(activeId)}`)
      .then((r) => { if (!cancelled) { setResult(r); setError(null); } })
      .catch((e) => { if (!cancelled) { setResult(null); setError(e?.message ?? 'Scenario unavailable'); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [activeId]);

  const tornadoData = result?.per_holding
    ?.slice()
    .sort((a, b) => Math.abs(b.impact_pct) - Math.abs(a.impact_pct))
    .map((p) => ({ ticker: p.ticker, impact: p.impact_pct }));

  return (
    <section className="card p-5">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Scenario simulator</h2>
        {result && (
          <span className={`pill ${result.total_portfolio_impact_pct >= 0 ? 'pill-pos' : 'pill-neg'}`}>
            portfolio {result.total_portfolio_impact_pct.toFixed(1)}%
          </span>
        )}
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveId(s.id)}
            className={`pill ${activeId === s.id ? 'border-accent-gold/60 bg-accent-gold/10 text-accent-gold' : 'pill-neu'}`}
          >
            {s.label}
          </button>
        ))}
      </div>
      {loading && <div className="text-[11px] text-accent-steel">Running scenario…</div>}
      {!loading && error && <div className="text-[11px] text-red-400">Error: {error}</div>}
      {result && (
        <>
          <p className="text-[12px] leading-relaxed text-ink-100/90">{result.rationale}</p>
          <div className="mt-3 h-60">
            <ResponsiveContainer>
              <BarChart layout="vertical" data={tornadoData} margin={{ left: 30, right: 16 }}>
                <XAxis type="number" stroke="#A3B0C5" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="ticker" stroke="#A3B0C5" tick={{ fontSize: 10 }} width={70} />
                <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                <Tooltip
                  contentStyle={{ background: '#0F1620', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, fontSize: 11 }}
                  formatter={(v: number) => `${v}%`}
                />
                <Bar dataKey="impact">
                  {tornadoData?.map((d, i) => (
                    <Cell key={i} fill={d.impact >= 0 ? '#19B89E' : '#E5484D'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </section>
  );
}
