'use client';
import { useEffect, useState } from 'react';
import { Printer } from 'lucide-react';

// Paperclip's plugin reverse-proxy mounts this app at /_plugins/<key>/ui/...
// and strips that prefix before forwarding to upstream. Root-relative hrefs
// like "/api/export/pdf" therefore resolve to https://host/api/... and 404
// outside the proxy mount. Detect the prefix at runtime and prepend it.
function computePdfHref(): string {
  if (typeof window === 'undefined') return '/api/export/pdf';
  const m = window.location.pathname.match(/^(\/_plugins\/[^/]+\/ui)(?=\/|$)/);
  return (m ? m[1] : '') + '/api/export/pdf';
}

export function ExportButton() {
  const [pdfHref, setPdfHref] = useState('/api/export/pdf');
  useEffect(() => { setPdfHref(computePdfHref()); }, []);

  return (
    <section className="card flex items-center justify-between p-5">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Briefing export</div>
        <p className="mt-1 text-sm">
          Export the full briefing as a portrait PDF. Uses the browser's print pipeline (Chrome / Edge → "Save as PDF").
          Server-side PDF via <code>/api/export/pdf</code> — generated from live data (no Chromium required).
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1 rounded-md border border-token-accent/40 bg-token-accent/10 px-3 py-2 text-xs font-semibold text-accent"
        >
          <Printer size={12} /> Print to PDF
        </button>
        <a
          href={pdfHref}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 rounded-md border border-token-border bg-token-surface-elevated px-3 py-2 text-xs font-medium text-token-fg-muted hover:border-token-accent/40 hover:text-accent"
        >
          Headless PDF
        </a>
      </div>
    </section>
  );
}
