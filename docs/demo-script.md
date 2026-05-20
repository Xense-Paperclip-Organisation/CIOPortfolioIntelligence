# 5-minute demo walkthrough — CIO Portfolio Intelligence POC

> Audience: senior wealth-tribe leadership, RM enablement leads, CIO office.
> Setup: `docker compose up -d`, `.env` populated with `ANTHROPIC_API_KEY`, browser on
> `http://localhost:8080`. Dark theme on by default.

## Cold-open (0:00 – 0:30)

> *"This is what our CIO Corner would look like if it knew the client.
> The mock customer is Ahmed Al-Mansouri — a 42-year-old engineering manager in Dubai,
> AED 3.2M AUM. He says Balanced. His actual book is anything but. The dashboard's job is to
> surface that, and to make the next conversation with his RM concrete."*

Show the header: live USD/AED, UST 10Y, US CPI. Stress that **only Ahmed's profile is mocked** —
every number on screen is currently being pulled from yfinance, FRED, exchangerate.host or
public RSS.

## Portfolio Pulse (0:30 – 1:15)

- Live revaluation.
- Health score (rule-driven, 0–100) + AI-generated narrative naming the actual movers.
- Click "Top movers" — these are computed from current quotes, not pre-baked.

Call out: *the model is over-weight US tech today; that's not commentary, that's a measurement.*

## Alignment Alerts (1:15 – 2:00) — **the hook**

Six structured alerts:

1. Equity 75% vs target 50%
2. Fixed income 7% vs floor 25%
3. Cash 15% vs ceiling 8%
4. USA 62% vs target 30%
5. US-tech cluster (AAPL/NVDA/TSLA/MSFT/META) > 25%
6. AAPL/NVDA/TSLA each over the 10% single-name cap

> *"Every alert is the seed of an advisory recommendation. Every recommendation can be discussed
> with the RM. Compare this to the current monthly newsletter, which doesn't know any of this."*

## Allocation vs Target donuts (2:00 – 2:30)

Walk through asset / geography / sector / currency. Numerical gap table beneath each pair.
Geography is the clearest visual — current donut is dominated by USA, target shows MENA and
Europe equal weight.

## Holding detail — NVDA (2:30 – 3:30)

Click NVDA. Show:

- TradingView Lightweight Charts candle (1d default).
- Switch to **1m**, **5m**, **1h**, **1mo**, **1yr** — all six BRD timeframes work.
- AI chart-explanation panel on the right: direction, range, volume tag, pattern, key moment,
  support, resistance, next target, last candle.
- Recent NVDA headlines below the chart (live RSS, filtered to NVDA).

## Personalized Articles Feed (3:30 – 4:00)

4–6 live articles, each with:

- *"What This Means For Your Portfolio"* paragraph naming specific tickers in Ahmed's book.
- Impact tiles (1–4) per article: ticker, direction badge, confidence %, rationale.
- Transmission paragraph on the macro mechanism.

Call out the **Personalized** badge top-right and the QA gate. Mention that personalizations are
cached by `(article_id, portfolio_hash)` so this stays affordable.

## Risk Lens (4:00 – 4:15)

- Portfolio beta, vol, Sharpe, max DD.
- Correlation heatmap — the AAPL / NVDA / MSFT block is visibly red.
- Per-symbol table for the equity sleeve.

## CIO Advisory Card (4:15 – 4:45)

Five action-tagged recommendations:

- **Trim** NVDA 16 → 8% · suggested replacement: VGK.
- **Trim** AAPL 18 → 8% · GCC sukuk.
- **Trim** TSLA 12 → 5% · cash sleeve / FI ladder.
- **Add** to KSA-SUKUK-5.6-2030 — bring FI to the 25% floor.
- **Diversify** into VGK + EWJ + VWO for ~15% non-US equity.
- **Rebalance** cash 15 → 8% into the above.

Diversification gap analysis · currency commentary · education-funding stress paragraphs below.

> *"Each recommendation has a `Discuss with RM` CTA — in production this is a workflow trigger.
> Today it's a mock."*

## Scenario simulator (4:45 – 5:00)

- *"US tech 20% correction"* → tornado chart, ~10–14% portfolio hit.
- *"Fed cuts 50bps"* → modestly positive, gold rallies, FI rallies.
- *"AED de-peg risk"* → highlights EMAAR drawdown vs USD-denominated holdings rallying.

## Ask-the-CIO (bonus)

> *"What's my biggest concentration risk right now?"*

The model is given the full portfolio state in a prompt-cached system block. The answer cites
NVDA, TSLA, and the broader US-tech cluster by name.

## PDF Export

Click `Print to PDF` — print pipeline captures the full briefing for handout. The `Headless PDF`
button drives the same render via Puppeteer for batch generation.

---

## Talking points

- *AI-generated commentary is everywhere, but every output is structured JSON gated by the
  QAAgent — no free-form text leaves the agent layer.*
- *No hallucinated tickers — the QA rule rejects any ticker not in `user_holdings` and falls back
  to the deterministic recommendation set if the LLM strays.*
- *Caching is per-agent: 5m for prices, 15m for news, 1d for personalizations keyed by
  `(article_id, portfolio_hash)`.*
- *Single command to run.  Single env file.  Replaces a department's worth of generic
  newsletters with one personalised brief per client.*
