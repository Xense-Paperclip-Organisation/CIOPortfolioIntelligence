'use client';
import { useEffect, useState, type KeyboardEvent } from 'react';
import { apiFetch } from '@/lib/api';
import { ExternalLink } from 'lucide-react';
import { focusHolding } from '@/lib/dashboard-events';

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

  function rowProps(ticker?: string | null) {
    if (!ticker) return { interactive: false as const };
    const open = () => focusHolding(ticker);
    return {
      interactive: true as const,
      role: 'button' as const,
      tabIndex: 0,
      'aria-label': `Open ${ticker} in holdings`,
      onClick: open,
      onKeyDown: (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          open();
        }
      }
    };
  }

  return (
    <section className="card p-5">
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Upcoming catalysts</h2>
      <div className="space-y-2 text-sm">
        {(data?.items ?? []).slice(0, 6).map((it, i) => {
          const props = rowProps(it.ticker);
          const { interactive, ...rest } = props;
          return (
            <div
              key={i}
              className={`flex items-center justify-between rounded-md border border-token-border bg-token-surface-elevated px-3 py-2 outline-none ${interactive ? 'cursor-pointer transition-colors hover:border-token-accent/40 hover:bg-token-surface focus-visible:border-token-accent/60' : ''}`}
              {...rest}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-1 font-semibold text-token-fg">
                  <span>{it.ticker} · {it.label}</span>
                  {interactive && <ExternalLink size={11} className="text-token-fg-muted/70" aria-hidden />}
                </div>
                <div className="text-[11px] text-token-fg-muted">{it.name} · source: {it.source}</div>
              </div>
              <div className="font-mono text-[11px] text-token-fg-muted">
                {formatCatalystDate(it.value) ?? '—'}
              </div>
            </div>
          );
        })}
        {(data?.macro ?? []).slice(0, 4).map((it, i) => (
          <div key={`m-${i}`} className="flex items-center justify-between rounded-md border border-token-border bg-token-surface-elevated px-3 py-2">
            <div>
              <div className="font-semibold">Macro · {it.label}</div>
              <div className="text-[11px] text-token-fg-muted">{it.source}{it.note ? ` — ${it.note}` : ''}</div>
            </div>
            <span className="pill pill-warn">macro</span>
          </div>
        ))}
        {!data && <div className="text-[11px] text-token-fg-muted">Loading catalyst calendar…</div>}
        {data && !data.items.length && (
          <div className="text-[11px] text-token-fg-muted">
            No live earnings dates returned by yfinance for the current holdings.
            Macro tags below reference public central-bank calendars.
          </div>
        )}
      </div>
    </section>
  );
}
