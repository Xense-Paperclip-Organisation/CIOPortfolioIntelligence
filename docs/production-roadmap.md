# Production roadmap — CIO Portfolio Intelligence

> Post-POC plan. Sized in T-shirts. Owners are placeholders; assignment to come from CEO.

## Phase 1 — Hardening (4–6 weeks)

| # | Workstream                                                                  | Size | Notes |
|---|-----------------------------------------------------------------------------|------|-------|
| 1 | Licensed market data integration (Refinitiv preferred, Bloomberg backup).  | L    | Swap-out is isolated to `backend/app/services/prices.py`. Adds T+0 corporate actions + symbology. |
| 2 | Licensed news + entity-tagged feed (Dow Jones / Bloomberg / NewsAPI Enterprise). | L    | Replaces the keyword heuristic in `services/news.py` with vendor entity tags. |
| 3 | Persistent storage layer — Postgres + Redis cluster.                        | M    | Replace SQLite/in-process LRU; persist personalization outputs in a vetted store. |
| 4 | Production observability — OpenTelemetry on backend, latency budgets, freshness SLOs, PagerDuty on data-source lag. | M    | Day-1 non-negotiable per Founding Engineer's engineering posture. |
| 5 | Hallucination defence-in-depth — second QA pass via Anthropic structured tool call.                                 | M    | Currently the QAAgent is rules-only; layer in an LLM critic that must agree before output ships. |

## Phase 2 — Compliance + Identity (6–8 weeks)

| # | Workstream                                                                  | Size | Notes |
|---|-----------------------------------------------------------------------------|------|-------|
| 6 | SSO + identity — Emirates NBD enterprise SSO, RM↔client authorization, full audit trail. | XL   | Hard gate before any client PII enters the system. |
| 7 | Compliance + disclosure framework — structured disclaimers, advisory sign-off workflow, retention. | L    | Engage compliance owner before production data lands. |
| 8 | Data classification + PII review — what's customer data, what's not, encryption + key management. | M    | Founding Engineer is escalating data-handling review to CEO when this work starts. |

## Phase 3 — Reach + Localization (6–10 weeks)

| #  | Workstream                                                                  | Size | Notes |
|----|-----------------------------------------------------------------------------|------|-------|
| 9  | Arabic localization — RTL, glossary, advisory voice for GCC clients.        | L    | Coordinate with Wealth-tribe content team. |
| 10 | Mobile-first responsive pass + iOS Safari hardening.                        | M    | POC is desktop-optimised; full mobile parity is a P1 follow-up. |
| 11 | Live demo telemetry + product analytics (Mixpanel/Amplitude).               | S    | Required for measuring advisor adoption. |
| 12 | A/B framework for narrative tone and CTA copy.                              | S    | Editorial voice should be tested with real RMs. |

## Phase 4 — Adjacent product (8–12 weeks)

| #  | Workstream                                                                  | Size | Notes |
|----|-----------------------------------------------------------------------------|------|-------|
| 13 | Trade execution wiring — broker-of-record integration, order tickets, confirmations. | XL   | Out of scope for POC; significant compliance + ops work. |
| 14 | Advisor-side dashboard — same data, multiple-client lens for RMs.           | L    | Repurposes most of the backend; new frontend surface. |
| 15 | Goals & glide-paths — formalise the 8-year USD education goal as a constraint on advisory recommendations. | L    | Useful next iteration of the advisory agent. |

## Risk register carry-over (BRD §12)

- **AI hallucination — #1 risk.** Defend-in-depth via QAAgent (rules + LLM critic + structured contracts).
- **MENA bond intraday data gap.** Until licensed feeds land, sukuk pricing remains synthesized
  from the yield curve + duration; clearly labelled in payloads. Production migration story is
  the licensed feed in Phase 1.
- **Claude cost.** Personalization caching by `(article_id, portfolio_hash)` keeps repeat hits at
  zero LLM cost. Per-session budget should be monitored once analytics is live.

## Escalations expected

- **CEO** — vendor selection (data feeds, identity, observability), compliance owner intro,
  initial customer-data approval gate.
- **Security Engineer (to be hired)** — hard gate on Phase 2 #6/#8.
- **UX Designer (to be hired)** — Phase 3 #10 + #12, and the editorial voice direction.
- **QA agent (to be hired)** — when the dashboard moves to staging with real RM users.
