import type { Article } from '@/types/api';
import { Sparkles, ExternalLink } from 'lucide-react';
import { CardError } from '@/components/CardStates';

const DIRECTION_CLS: Record<string, string> = {
  positive: 'pill-pos',
  negative: 'pill-neg',
  neutral:  'pill-neu'
};

export function ArticlesFeed({ articles, error }: { articles: Article[]; error?: string }) {
  if (error) {
    return <CardError message={`News feed unavailable: ${error}`} />;
  }
  const list = articles.slice(0, 6);
  if (!list.length) {
    return (
      <section className="card p-6 text-sm text-token-fg-muted">
        News feed is empty — RSS providers may be rate-limiting. The dashboard will retry on next reload.
      </section>
    );
  }
  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-token-fg-muted">Personalized articles — what this means for your portfolio</h2>
        <span className="pill border-token-accent/40 bg-token-accent/10 text-accent">Personalized · QA-validated</span>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {list.map((art) => {
          const p = art.personalization;
          return (
            <article key={art.id} className="card relative flex flex-col gap-3 p-5">
              {p && (
                <span className="absolute right-4 top-4 pill border-token-accent/40 bg-token-accent/10 text-accent">Personalized</span>
              )}
              <div>
                <a href={art.link} target="_blank" rel="noreferrer" className="text-base font-semibold leading-snug text-token-fg hover:text-token-accent">{art.title}</a>
                <div className="mt-1 flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-token-fg-muted">
                  <span>{art.source}</span>
                  {art.published && <span>· {new Date(art.published).toLocaleDateString()}</span>}
                  {!!art.matched_tickers.length && <span>· {art.matched_tickers.slice(0, 3).join(', ')}</span>}
                  <a href={art.link} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-token-fg-muted hover:text-token-accent"><ExternalLink size={11} /> source</a>
                </div>
              </div>
              {p && (
                <>
                  <div className="rounded-md border border-token-accent/20 bg-token-accent/[0.04] p-3 text-sm leading-relaxed">
                    <div className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.15em] text-accent">
                      <Sparkles size={11} /> What this means for your portfolio
                    </div>
                    <p className="mt-1 text-token-fg">{p.summary_paragraph}</p>
                  </div>
                  {!!p.impact_tiles.length && (
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {p.impact_tiles.map((tile) => (
                        <div key={tile.ticker} className="rounded-md border border-token-border bg-token-surface-elevated p-2">
                          <div className="flex items-center justify-between">
                            <div className="text-sm font-semibold text-token-fg">{tile.ticker}</div>
                            <span className={`pill ${DIRECTION_CLS[tile.direction]}`}>{tile.direction}</span>
                          </div>
                          <div className="mt-0.5 text-[11px] leading-tight text-token-fg-muted">{tile.name}</div>
                          {tile.rationale && <div className="mt-1 text-[11px] leading-snug text-token-fg-muted">{tile.rationale}</div>}
                          <div className="mt-1 text-[10px] text-token-fg-muted/80">Confidence {tile.confidence}%</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {p.transmission_paragraph && (
                    <p className="text-[12px] leading-relaxed text-token-fg-muted">{p.transmission_paragraph}</p>
                  )}
                  {p.degraded && (
                    <div className="font-mono text-[10px] uppercase tracking-wider text-warning">Offline-mode summary — set ANTHROPIC_API_KEY for AI voice.</div>
                  )}
                </>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
