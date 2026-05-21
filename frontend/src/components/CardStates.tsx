'use client';

import { RefreshCw, AlertTriangle, InboxIcon } from 'lucide-react';

export function CardError({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <section className="card p-6">
      <div className="flex flex-col items-center gap-3 py-4 text-center">
        <AlertTriangle size={20} className="text-negative/80" />
        <p className="text-sm font-medium text-token-fg">Failed to load</p>
        {message && (
          <p className="max-w-sm text-[11px] text-token-fg-muted">{message}</p>
        )}
        {onRetry ? (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 rounded-md border border-token-border bg-token-surface-elevated px-3 py-1.5 text-[12px] text-token-fg-muted hover:text-token-fg"
          >
            <RefreshCw size={12} /> Retry
          </button>
        ) : (
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center gap-1.5 rounded-md border border-token-border bg-token-surface-elevated px-3 py-1.5 text-[12px] text-token-fg-muted hover:text-token-fg"
          >
            <RefreshCw size={12} /> Reload page
          </button>
        )}
      </div>
    </section>
  );
}

export function CardEmpty({ message }: { message: string }) {
  return (
    <section className="card p-6">
      <div className="flex flex-col items-center gap-2 py-4 text-center">
        <InboxIcon size={18} className="text-token-fg-muted/50" />
        <p className="text-sm text-token-fg-muted">{message}</p>
      </div>
    </section>
  );
}

export function CardLoading({ label }: { label: string }) {
  return (
    <section className="card p-6">
      <div className="flex items-center gap-2 text-[12px] text-token-fg-muted">
        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-token-fg-muted/30 border-t-token-fg-muted" />
        {label}
      </div>
    </section>
  );
}
