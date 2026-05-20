import type { Article } from '@/types/api';
import { Sparkles, ExternalLink } from 'lucide-react';

const DIRECTION_CLS: Record<string, string> = {
  positive: 'pill-pos',
  negative: 'pill-neg',
  neutral: 'pill-neu'
};

export function ArticlesFeed({ articles }: { articles: Article[] }) {
  const list = articles.slice(0, 6);
  if (!list.length) {
    return (
      <section className="card p-6 text-sm text-accent-steel">
        News feed is empty — RSS providers may be rate-limiting. The dashboard will retry on next reload.
      </section>
    );
  }
  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">Personalized articles — what this means for your portfolio</h2>
        <span className="pill border-accent-gold/40 bg-accent-gold/10 text-accent-gold">Personalized · QA-validated</span>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {list.map((art) => {
          const p = art.personalization;
          return (
            <article key={art.id} className="card relative flex flex-col gap-3 p-5">
              {p && (
                <span className="absolute right-4 top-4 pill border-accent-gold/40 bg-accent-gold/10 text-accent-gold">Personalized</span>
              )}
              <div>
                <a href={art.link} target="_blank" rel="noreferrer" className="text-base font-semibold leading-snug hover:text-accent-gold">{art.title}</a>
                <div className="mt-1 flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-accent-steel/80">
                  <span>{art.source}</span>
                  {art.published && <span>· {new Date(art.published).toLocaleDateString()}</span>}
                  {!!art.matched_tickers.length && <span>· {art.matched_tickers.slice(0, 3).join(', ')}</span>}
                  <a href={art.link} target="_blank" rel="noreferrer" className="ml-auto inline-flex items-center gap-1 text-accent-steel hover:text-accent-gold"><ExternalLink size={11} /> source</a>
                </div>
              </div>
              {p && (
                <>
                  <div className="rounded-md border border-accent-gold/20 bg-accent-gold/[0.04] p-3 text-sm leading-relaxed">
                    <div className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-[0.15em] text-accent-gold">
                      <Sparkles size={11} /> What this means for your portfolio
                    </div>
                    <p className="mt-1">{p.summary_paragraph}</p>
                  </div>
                  {!!p.impact_tiles.length && (
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {p.impact_tiles.map((tile) => (
                        <div key={tile.ticker} className="rounded-md border border-white/[0.05] bg-white/[0.02] p-2">
                          <div className="flex items-center justify-between">
                            <div className="text-sm font-semibold">{tile.ticker}</div>
                            <span className={`pill ${DIRECTION_CLS[tile.direction]}`}>{tile.direction}</span>
                          </div>
                          <div className="mt-0.5 text-[11px] leading-tight text-accent-steel">{tile.name}</div>
                          {tile.rationale && <div className="mt-1 text-[11px] leading-snug text-accent-steel/90">{tile.rationale}</div>}
                          <div className="mt-1 text-[10px] text-accent-steel/80">Confidence {tile.confidence}%</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {p.transmission_paragraph && (
                    <p className="text-[12px] leading-relaxed text-accent-steel">{p.transmission_paragraph}</p>
                  )}
                  {p.degraded && (
                    <div className="font-mono text-[10px] uppercase tracking-wider text-amber-300">Offline-mode summary — set ANTHROPIC_API_KEY for AI voice.</div>
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
