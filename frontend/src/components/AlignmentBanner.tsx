import type { AlignmentAlert } from '@/types/api';
import { AlertTriangle, AlertCircle } from 'lucide-react';

const SEV: Record<string, { ring: string; bg: string; icon: typeof AlertTriangle; iconCls: string }> = {
  high:   { ring: 'border-token-negative/30',  bg: 'bg-token-negative/10',  icon: AlertTriangle, iconCls: 'text-negative' },
  medium: { ring: 'border-token-warning/30',   bg: 'bg-token-warning/10',   icon: AlertCircle,   iconCls: 'text-warning'  },
  low:    { ring: 'border-token-border',        bg: 'bg-token-surface',      icon: AlertCircle,   iconCls: 'text-info'     }
};

export function AlignmentBanner({ alerts }: { alerts: AlignmentAlert[] }) {
  if (!alerts?.length) return null;
  return (
    <section>
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">
        Alignment alerts — Balanced profile mismatches
      </h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {alerts.map((a, i) => {
          const sev = SEV[a.severity] ?? SEV.low;
          const Icon = sev.icon;
          return (
            <div key={i} className={`card ${sev.bg} ${sev.ring} flex items-start gap-3 p-4`}>
              <Icon size={18} className={sev.iconCls} />
              <div>
                <div className="text-sm font-semibold text-token-fg">{a.headline}</div>
                <div className="mt-1 text-[11px] leading-relaxed text-token-fg-muted">{a.body}</div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
