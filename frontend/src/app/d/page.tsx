// Public demo entry. Renders the same dashboard composition as `/`, but with
// Next.js ISR caching enabled (120s) so the Paperclip plugin dev-proxy
// (10-second abort window on the Paperclip host) doesn't time out on cold
// yfinance/RSS/FRED renders. Cached fetches mean cold load happens once, then
// every public viewer gets the cached HTML for 2 minutes.
import { CustomerHeader } from '@/components/CustomerHeader';
import { PortfolioPulse } from '@/components/PortfolioPulse';
import { AlignmentBanner } from '@/components/AlignmentBanner';
import { AllocationVsTarget } from '@/components/AllocationVsTarget';
import { HoldingsGrid } from '@/components/HoldingsGrid';
import { ArticlesFeed } from '@/components/ArticlesFeed';
import { RiskLens } from '@/components/RiskLens';
import { AdvisoryCard } from '@/components/AdvisoryCard';
import { CatalystsList } from '@/components/CatalystsList';
import { ScenarioSimulator } from '@/components/ScenarioSimulator';
import { AskTheCIO } from '@/components/AskTheCIO';
import { ExportButton } from '@/components/ExportButton';
import type { PortfolioBundle, Pulse, RiskMetrics, Article, AdvisoryOutput, MacroSnapshot } from '@/types/api';

export const revalidate = 120;

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

async function ssrCachedFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, {
      next: { revalidate: 120 },
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function loadDashboard() {
  const [pulse, news, advisory, macro] = await Promise.all([
    ssrCachedFetch<PortfolioBundle & { risk: RiskMetrics; pulse: Pulse }>('/api/portfolio/pulse'),
    ssrCachedFetch<{ articles: Article[]; portfolio_hash: string }>('/api/news?limit=8'),
    ssrCachedFetch<{ advisory: AdvisoryOutput; risk: RiskMetrics }>('/api/advisory'),
    ssrCachedFetch<MacroSnapshot>('/api/macro')
  ]);
  return { pulse, news, advisory, macro };
}

export default async function DemoPage() {
  const data = await loadDashboard();
  if (!data.pulse) {
    return (
      <div className="card mt-6 p-8 text-sm text-accent-steel">
        <h1 className="font-display text-lg text-rose-300">Backend warming up</h1>
        <p className="mt-2">
          The demo backend is still booting. Reload in a few seconds — first cold render
          can take ~15 s while yfinance / RSS / FRED prime their caches.
        </p>
      </div>
    );
  }
  const { pulse, news, advisory, macro } = data;
  return (
    <div className="space-y-6 pb-8">
      <CustomerHeader bundle={pulse} macro={macro} />
      <PortfolioPulse bundle={pulse} />
      <AlignmentBanner alerts={pulse.alerts} />
      <AllocationVsTarget allocation={pulse.allocation} target={pulse.target} positions={pulse.positions} />
      <HoldingsGrid positions={pulse.positions} />
      <ArticlesFeed articles={news?.articles ?? []} />
      <RiskLens risk={pulse.risk} positions={pulse.positions} />
      <AdvisoryCard advisory={advisory?.advisory ?? null} />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CatalystsList />
        <ScenarioSimulator />
      </div>
      <AskTheCIO />
      <ExportButton />
    </div>
  );
}
