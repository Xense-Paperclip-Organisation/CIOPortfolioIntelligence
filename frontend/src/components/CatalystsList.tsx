'use client';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';

/** Format an ISO-8601 date string as "Wed, May 27 2026". Returns null for invalid/leaked values. */
function formatCatalystDate(raw?: string): string | null {
  if (!raw) return null;
  // Defensive: reject any Python repr leaks
  if (raw.includes('datetime.') || raw.startsWith('[')) return null;
  const d = new Date(raw);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

type Item = { ticker?: string | null; name?: string; kind: string; label: string; value?: string; source?: string; note?: string };

export function CatalystsList() {
  const [data, setData] = useState<{ items: Item[]; macro: Item[] } | null>(null);
  useEffect(() => {
    apiFetch<{ items: Item[]; macro: Item[] }>('/api/catalysts').then(setData).catch(() => setData({ items: [], macro: [] }));
  }, []);
  return (
    <section className="card p-5">
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Upcoming catalysts</h2>
      <div className="space-y-2 text-sm">
        {(data?.items ?? []).slice(0, 6).map((it, i) => (
          <div key={i} className="flex items-center justify-between rounded-md border border-white/[0.05] bg-white/[0.02] px-3 py-2">
            <div>
              <div className="font-semibold">{it.ticker} · {it.label}</div>
              <div className="text-[11px] text-accent-steel">{it.name} · source: {it.source}</div>
            </div>
            <div className="font-mono text-[11px] text-accent-steel">
              {formatCatalystDate(it.value) ?? '—'}
            </div>
          </div>
        ))}
        {(data?.macro ?? []).slice(0, 4).map((it, i) => (
          <div key={`m-${i}`} className="flex items-center justify-between rounded-md border border-white/[0.05] bg-white/[0.02] px-3 py-2">
            <div>
              <div className="font-semibold">Macro · {it.label}</div>
              <div className="text-[11px] text-accent-steel">{it.source}</div>
            </div>
            <span className="pill pill-warn">macro</span>
          </div>
        ))}
        {!data && <div className="text-[11px] text-accent-steel">Loading catalyst calendar…</div>}
        {data && !data.items.length && (
          <div className="text-[11px] text-accent-steel">
            No live earnings dates returned by yfinance for the current holdings.
            Macro tags below reference public central-bank calendars.
          </div>
        )}
      </div>
    </section>
  );
}
