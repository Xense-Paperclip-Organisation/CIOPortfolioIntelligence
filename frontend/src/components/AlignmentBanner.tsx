import type { AlignmentAlert } from '@/types/api';
import { AlertTriangle, AlertCircle } from 'lucide-react';

const SEV: Record<string, { ring: string; bg: string; icon: typeof AlertTriangle }> = {
  high: { ring: 'border-rose-400/30', bg: 'bg-rose-500/10', icon: AlertTriangle },
  medium: { ring: 'border-amber-400/30', bg: 'bg-amber-500/10', icon: AlertCircle },
  low: { ring: 'border-slate-400/30', bg: 'bg-slate-500/10', icon: AlertCircle }
};

export function AlignmentBanner({ alerts }: { alerts: AlignmentAlert[] }) {
  if (!alerts?.length) return null;
  return (
    <section>
      <h2 className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">
        Alignment alerts — Balanced profile mismatches
      </h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {alerts.map((a, i) => {
          const sev = SEV[a.severity] ?? SEV.low;
          const Icon = sev.icon;
          return (
            <div key={i} className={`card ${sev.bg} ${sev.ring} flex items-start gap-3 p-4`}>
              <Icon size={18} className={a.severity === 'high' ? 'text-rose-300' : 'text-amber-300'} />
              <div>
                <div className="text-sm font-semibold">{a.headline}</div>
                <div className="mt-1 text-[11px] leading-relaxed text-accent-steel">{a.body}</div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
