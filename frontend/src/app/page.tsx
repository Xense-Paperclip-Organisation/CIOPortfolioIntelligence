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
import { apiFetch } from '@/lib/api';
import type { PortfolioBundle, Pulse, RiskMetrics, Article, AdvisoryOutput, MacroSnapshot } from '@/types/api';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

async function loadDashboard() {
  // Run in parallel — each call is independently cached server-side.
  const [pulse, news, advisory, macro] = await Promise.allSettled([
    apiFetch<PortfolioBundle & { risk: RiskMetrics; pulse: Pulse }>('/api/portfolio/pulse'),
    apiFetch<{ articles: Article[]; portfolio_hash: string }>('/api/news?limit=8'),
    apiFetch<{ advisory: AdvisoryOutput; risk: RiskMetrics }>('/api/advisory'),
    apiFetch<MacroSnapshot>('/api/macro')
  ]);
  return {
    pulse: pulse.status === 'fulfilled' ? pulse.value : null,
    pulseError: pulse.status === 'rejected' ? (pulse.reason as Error).message : null,
    news: news.status === 'fulfilled' ? news.value : null,
    newsError: news.status === 'rejected' ? (news.reason as Error).message : null,
    advisory: advisory.status === 'fulfilled' ? advisory.value : null,
    advisoryError: advisory.status === 'rejected' ? (advisory.reason as Error).message : null,
    macro: macro.status === 'fulfilled' ? macro.value : null,
    macroError: macro.status === 'rejected' ? (macro.reason as Error).message : null
  };
}

export default async function HomePage() {
  const data = await loadDashboard();
  if (!data.pulse) {
    return (
      <div className="card mt-6 p-8 text-sm text-accent-steel">
        <h1 className="font-display text-lg text-rose-300">Backend unreachable</h1>
        <p className="mt-2">
          The dashboard server cannot reach the FastAPI backend. Confirm <code>docker-compose up</code>
          {' '}is running and the backend container reports healthy.
        </p>
        {data.pulseError && <pre className="mt-3 max-w-full overflow-x-auto rounded bg-black/40 p-3 text-[11px]">{data.pulseError}</pre>}
      </div>
    );
  }
  const { pulse, news, newsError, advisory, advisoryError, macro } = data;
  return (
    <div className="space-y-6 pb-8">
      <CustomerHeader bundle={pulse} macro={macro} />
      <PortfolioPulse bundle={pulse} />
      <AlignmentBanner alerts={pulse.alerts} />
      <AllocationVsTarget allocation={pulse.allocation} target={pulse.target} positions={pulse.positions} />
      <HoldingsGrid positions={pulse.positions} />
      <ArticlesFeed articles={news?.articles ?? []} error={newsError ?? undefined} />
      <RiskLens risk={pulse.risk} positions={pulse.positions} />
      <AdvisoryCard advisory={advisory?.advisory ?? null} error={advisoryError ?? undefined} />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CatalystsList />
        <ScenarioSimulator />
      </div>
      <AskTheCIO />
      <ExportButton />
    </div>
  );
}
