'use client';
import { Printer } from 'lucide-react';

export function ExportButton() {
  return (
    <section className="card flex items-center justify-between p-5">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Briefing export</div>
        <p className="mt-1 text-sm">
          Export the full briefing as a portrait PDF. Uses the browser's print pipeline (Chrome / Edge → "Save as PDF").
          Server-side PDF via <code>/api/export/pdf</code> — generated from live data (no Chromium required).
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1 rounded-md border border-accent-gold/40 bg-accent-gold/10 px-3 py-2 text-xs font-semibold text-accent-gold"
        >
          <Printer size={12} /> Print to PDF
        </button>
        <a
          href="/api/export/pdf"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 rounded-md border border-white/[0.08] bg-white/[0.04] px-3 py-2 text-xs font-medium text-accent-steel hover:border-accent-gold/40 hover:text-accent-gold"
        >
          Headless PDF
        </a>
      </div>
    </section>
  );
}
