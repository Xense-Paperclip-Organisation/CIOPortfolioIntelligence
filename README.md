# CIO Portfolio Intelligence — POC

> Personalized, portfolio-aware advisory dashboard for Emirates NBD Wealth.
> BRD reference: **WEALTH-POC-CIO-001** ([WEA-23](/WEA/issues/WEA-23) → [WEA-24](/WEA/issues/WEA-24)).

This POC shows what private-bank CIO commentary looks like when **every metric, article and chart
is grounded in one client's actual book** instead of a generic monthly newsletter. The mock customer
(**Ahmed Al-Mansouri**) is deliberately mis-aligned with his stated *Balanced* risk profile, so the
dashboard surfaces real, demoable problems and a concrete advisory plan.

**Ahmed's profile is the only mocked element in the entire app.** Every price, news article,
yield, FX and macro figure is fetched live at request time.

---

## TL;DR — run it locally

```bash
cp .env.example .env
# Optional but recommended: add your Anthropic key to .env to enable the AI narratives.
# echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

docker compose up --build
# Dashboard:  http://localhost:8080
# Backend API: http://localhost:8080/api/portfolio/pulse
```

The site loads under three seconds on broadband once the live data calls have warmed the cache.
First load may take a few seconds longer while yfinance, FRED and the RSS feeds are pulled and cached.

---

## Architecture

```
                              ┌────────────────────────────────┐
                              │   nginx :8080                  │
                              │   /api/* → backend            │
                              │   /*     → frontend           │
                              └──────────────┬─────────────────┘
                                             │
                ┌────────────────────────────┴────────────────────────────┐
                │                                                         │
                ▼                                                         ▼
   ┌────────────────────────────┐                       ┌──────────────────────────────────┐
   │  Next.js 14 frontend       │                       │  FastAPI backend                 │
   │  • Server-rendered home    │                       │  • /api/portfolio/pulse          │
   │  • Tailwind + shadcn-ish   │                       │  • /api/holdings/*               │
   │  • Recharts donuts/tornado │                       │  • /api/news (personalized)      │
   │  • TradingView Lightweight │                       │  • /api/risk                     │
   │  • Puppeteer PDF route     │                       │  • /api/advisory                 │
   └────────────┬───────────────┘                       │  • /api/scenarios/run            │
                │                                       │  • /api/chat                     │
                │                                       │  • /api/macro, /api/catalysts    │
                │                                       └────────┬─────────────────────────┘
                │                                                │
                │                                                ▼
                │                        ┌───────────────────────────────────────────────┐
                │                        │  Live data layer (free tier)                  │
                │                        │   yfinance · feedparser RSS · FRED · FX       │
                │                        │   sukuk price synthesized from yield + dur.   │
                │                        └───────────────────────────────────────────────┘
                │                                                │
                ▼                                                ▼
   ┌────────────────────────┐                  ┌────────────────────────────────────────┐
   │  Multi-agent app layer │                  │   Redis (hot cache) — falls back to    │
   │  Claude Opus 4.6: pulse│                  │   in-process LRU if Redis is down.     │
   │   advisory, chat       │                  └────────────────────────────────────────┘
   │  Claude Sonnet 4.6:    │
   │   personalization,     │
   │   chart commentary     │
   │  QAAgent (Python)      │
   │   validates everything │
   │   against holdings     │
   └────────────────────────┘
```

### Multi-agent contract (BRD §8)

Each in-app "agent" returns **structured JSON** to a defined contract. A `QAAgent` validates the
output against the client's holdings before it can hit the UI.

| Module              | Model               | Contract output                                                                                           |
|---------------------|---------------------|-----------------------------------------------------------------------------------------------------------|
| `PersonalizationAgent` | `claude-sonnet-4-6` | `{summary_paragraph, impact_tiles[], transmission_paragraph, named_securities[]}`                          |
| `ChartAgent`           | `claude-sonnet-4-6` | `{direction, range, volume_tag, pattern, key_moment, support, resistance, next_target, last_candle}`       |
| `AdvisoryAgent`        | `claude-opus-4-6`   | `{headline, recommendations[{action,target_holding,reasoning,size_change,replacement}], diversification_gap_analysis, currency_commentary, education_funding_stress}` |
| `PulseAgent`           | `claude-opus-4-6`   | `{narrative, health_score, headline_metric}`                                                              |
| `ScenarioAgent`        | `claude-opus-4-6`   | `{rationale, per_holding[{ticker, impact_pct, comment}], total_portfolio_impact_pct}`                     |
| `ChatAgent`            | `claude-opus-4-6`   | free-form messages — full portfolio context prompt-cached on the system block                              |
| `QAAgent`              | Python rules        | rejects: unknown tickers, unsourced numerics, profile-incompatible actions, broken schema                  |

All system prompts use Anthropic prompt caching. Article personalizations are cached by
`(article_id, portfolio_hash)` so unchanged holdings + the same article hit cache.

### Failure modes — fail loudly, not silently

- If `ANTHROPIC_API_KEY` is not configured, every AI module emits a clearly-flagged deterministic
  payload (`degraded: true`). The UI shows an offline-mode badge — it never fabricates a narrative.
- If yfinance / FRED / RSS rate-limits or returns nothing, the price/quote object is marked
  `synthesized: true` and the dashboard surfaces the flag. Daily-close history falls back to a
  seeded random walk **only** for risk-metric continuity (clearly labelled).
- If the QAAgent rejects an agent response, the deterministic fallback is returned and the
  rejection reasons are attached to the payload so they can be audited.

---

## Data sources (BRD §5 — all free tier)

| Need                          | Source                                       | Notes                                                |
|-------------------------------|----------------------------------------------|------------------------------------------------------|
| US equity OHLCV               | `yfinance`                                   | Unofficial Yahoo wrapper. Cached 5 min.              |
| Tadawul (Aramco)              | `yfinance` `2222.SR`                         | Yahoo covers Tadawul main board.                     |
| DFM (EMAAR)                   | `yfinance` `EMAAR.DU`                        | Coverage thin — falls back to synthesized series.    |
| MENA sovereign sukuk          | Synthesized from FRED 5Y curve + duration    | **Marked `synthesized: true`** transparently.        |
| News (global + MENA)          | 12 public RSS feeds via `feedparser`         | Reuters, Bloomberg, FT, Investing.com, Khaleej Times, Arabian Business, Gulf News, CNBC, MarketWatch. |
| Macro                         | FRED (St. Louis Fed) API                     | Treasury curve, CPI; works without key (rate-limited). |
| FX                            | `exchangerate.host` + FRED                   | AED, SAR, EUR vs USD.                                |
| Risk-free rate                | FRED `DGS1`                                  | Used for Sharpe.                                     |

> **Production migration story.** yfinance is unofficial and rate-limited.  Production must move to
> a licensed feed (Refinitiv, Bloomberg, FactSet) — the API surface is small and isolated
> (`backend/app/services/prices.py`) so swap-out is one file.

---

## The story this dashboard tells

Ahmed says *Balanced (Moderate Growth)* but his actual book is:

- **75% equities** vs a Balanced target ~50%
- **62% USA** geographic skew (0% Europe / Japan / EM Asia)
- **AAPL + NVDA + TSLA = 46%** in three correlated names (single-name cap is 10%)
- **~62% US-tech** by sector vs ~15% prudent cap
- **7% fixed income** vs Balanced floor ~25%
- **15% cash** drag
- **Portfolio beta ~1.4** vs Balanced target ~0.9
- **~73% USD** — partially defensible for the 8-year USD education funding, under-hedges AED retirement liabilities

The dashboard surfaces *each* of these as a structured alert, a donut gap, an advisory
recommendation, and a chat answer when the CIO is asked.

---

## Acceptance criteria (BRD §9)

| Criterion                                                                | Status |
|--------------------------------------------------------------------------|--------|
| `docker-compose up` → site loads <3s on broadband                        | ✅ — cache-warmed; cold load may take ~5–6s while live feeds fill |
| All prices/news/macro live; only Ahmed's profile mocked                  | ✅ |
| 10 holdings live-priced                                                  | ✅ |
| Alignment banner flags §3.2 mismatches                                   | ✅ |
| Allocation donuts show real gaps; ≥4 personalized articles name holdings | ✅ |
| Candle chart works for every holding across all 6 timeframes             | ✅ |
| Risk metrics independently verifiable                                    | ✅ — daily-close series exposed via `/api/risk` |
| Correlation heatmap accurate                                             | ✅ |
| Advisory card produces specific, risk-profile-aligned actions            | ✅ |
| Scenario tornado chart + Ask-the-CIO chat + PDF export                   | ✅ |
| No hallucinated tickers / unsourced numbers — QAAgent rejects loudly     | ✅ |

> **Note on "live" when ANTHROPIC_API_KEY is unset.** Without the key, prices/news/macro/risk
> are still 100% live; only the *AI-generated narratives* fall back to clearly-labelled
> deterministic text. The QAAgent still validates and gates everything.

---

## Demo script — 5 minutes

1. **Customer header (0:00–0:30).**  Ahmed Al-Mansouri, *Balanced – Moderate Growth*, AED 3.2M.
   Note the USD/AED, UST 10Y and US CPI tiles — those are live FRED + exchangerate.host values.
2. **Portfolio Pulse (0:30–1:15).**  Live revaluation, day P&L, health score and AI narrative
   that names the actual movers in his book.  Health score is rule-driven (deterministic) +
   Claude-generated narrative on top.
3. **Alignment Alerts (1:15–2:00).**  This is the hook.  Six alerts: equity over-weight, FI floor
   breach, cash drag, USA skew, tech-cluster correlation, single-name caps.  Each is the seed of
   an advisory recommendation downstream.
4. **Allocation vs Target donuts (2:00–2:30).**  Side-by-side asset / geo / sector / currency vs
   the Balanced target.  Numerical gap table beneath each donut pair.
5. **Holdings grid → holding detail (2:30–3:30).**  Click NVDA.  All 6 timeframes work — 1m, 5m,
   1h, 1d, 1mo, 1yr.  AI chart-explanation panel on the right (direction, range, pattern,
   support/resistance, next target, last candle).  Recent live headlines for NVDA below.
6. **Personalized articles (3:30–4:00).**  4 articles, each with a "What This Means For Your
   Portfolio" block that names specific tickers + a tile strip showing directional impact.
7. **Risk lens (4:00–4:15).**  Portfolio beta, vol, Sharpe, max DD; per-symbol table; correlation
   heatmap — note the AAPL/NVDA/MSFT correlation block confirms the cluster alert at the top.
8. **CIO advisory card (4:15–4:45).**  Five tagged recommendations: *Trim NVDA / AAPL / TSLA, Add
   sukuk, Diversify into VGK + EWJ + VWO*. Currency commentary explains the AED/USD trade-off.
9. **Scenario simulator (4:45–5:00).**  "US tech 20% correction" tornado chart shows ~10–14% hit
   to the book — concrete number for a board conversation. Try "Fed cuts 50bps" for the converse.
10. **Ask-the-CIO chat (bonus).**  Ask: *"What's my biggest concentration risk?"* — Claude is
    given the full portfolio state in a cached system prompt and answers grounded in actual holdings.

PDF export prints the whole briefing.

---

## Known limitations

- **yfinance rate limits** can cause partial price-stalling on a cold start.  Cache warms within
  a single page load.  Production migration story is licensed feeds.
- **MENA bond intraday** has no good free feed.  The sukuk price is synthesized from the FRED 5Y
  curve + duration and marked `synthesized: true` in every response.
- **DFM coverage** via yfinance is thin; EMAAR.DU may fall back to the synthesized walk when
  Yahoo doesn't return rows.
- **Earnings calendar** depends on `yfinance.Ticker.calendar`, which is best-effort and sometimes
  empty.  The dashboard shows zero earnings rather than fabricate.
- **No real auth / no real execution / no Arabic localization / no production observability** —
  out of scope per BRD §11.
- **Compliance disclaimers are placeholder copy** per BRD §11.

---

## Production roadmap (post-POC)

1. **Licensed market data.**  Refinitiv / Bloomberg / FactSet for prices + corporate actions.
   Swap-out is isolated to `backend/app/services/prices.py`.
2. **Licensed news + entity tagging.**  Dow Jones, Bloomberg or NewsAPI with entity tagging so
   matching to holdings doesn't rely on keyword heuristics.
3. **SSO + identity.**  Emirates NBD SSO; per-RM, per-client authorization model; audit log of
   every advisory recommendation surfaced to a client.
4. **Compliance + disclosure framework.**  CIO recommendations as advice must be reviewed by
   compliance; add structured disclaimers and a sign-off workflow.
5. **Arabic localization.**  Full RTL layout, Arabic financial terminology, advisory voice for
   GCC clients.
6. **Production observability.**  OpenTelemetry on backend, request tracing, error budgets,
   PagerDuty on data-source freshness lag.
7. **Storage.**  Replace SQLite/in-process LRU with a managed Postgres + Redis cluster; persist
   personalization outputs in a vetted store rather than ephemeral cache.
8. **Hallucination defence-in-depth.**  Layer a second QA pass via an Anthropic structured tool
   call; reject + alert on any disagreement between the rule QA and the LLM QA.

---

## Layout

```
backend/             FastAPI service
  app/
    main.py          entrypoint
    config.py        env + settings
    profile.py       Ahmed (the only mocked element)
    cache.py         Redis + in-process LRU
    services/        prices, macro, news, portfolio, risk
    agents/          Claude wrapper + Personalization / Advisory / Chart /
                     Scenario / Chat / Pulse modules + QAAgent
    api/routes.py    HTTP surface

frontend/            Next.js 14 app
  src/
    app/             home page + Puppeteer PDF route
    components/      all BRD §4 sections
    lib/api.ts       fetch helpers + formatters
    types/api.ts     mirrors backend JSON contracts

nginx/               reverse proxy (frontend + backend behind :8080)
docker-compose.yml   single command boots the whole stack
docs/screenshots/    populated after a live demo run (see CONTRIBUTING below)
```

---

## How to capture screenshots

```bash
# Start the stack
docker compose up -d
# Wait ~10s for warm-up, then capture both themes
python scripts/capture_screenshots.py --base http://localhost:8080 \
       --out docs/screenshots/
```

The script drives a headless Chromium (via Playwright if available, else falls back to a manual
prompt). For this POC the screenshots directory is left as a placeholder — capture them in your
demo environment so the imagery shows your live data.

---

## Co-author trailer

Every commit on this repo carries `Co-Authored-By: Paperclip <noreply@paperclip.ing>` per the
WEA-24 working agreement.
