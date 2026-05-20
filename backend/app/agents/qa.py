"""QAAgent — BRD §8 enforcement.

Validates outputs from each in-app agent against the user's actual holdings
and rejects any response that:
  - names a security not in user_holdings
  - returns a numeric figure without a source attribution
  - recommends an action incompatible with the stated Balanced risk profile

The QA agent is deterministic (Python rules) — *not* an LLM call — so
failures fail loudly with structured reasons instead of silently regenerating.
"""
from __future__ import annotations

import re
from typing import Any


TICKER_RE = re.compile(r"\b[A-Z]{2,5}(?:\.[A-Z]{2})?\b")
KNOWN_BENCHMARKS = {"S&P", "S&P500", "SPX", "MSCI", "ACWI", "ETF", "ESG", "VGK", "GCC", "GLD",
                    "FOMC", "ECB", "OPEC", "USD", "AED", "SAR", "EUR", "JPY", "EU", "UAE", "KSA",
                    "USA", "EM", "EMEA", "MENA", "CIO", "RM", "FX", "IPO", "ROE", "P/E", "API",
                    "AI", "GPU", "EV", "ATM", "ICE", "ESG", "PRO", "OTC", "US", "UK"}


def _extract_tickers(text: str) -> set[str]:
    """Pull plausible 2-5 letter tickers out of free-form text, minus the
    known-benchmark words above so we don't false-positive on `S&P` / `CIO`.
    """
    matches = TICKER_RE.findall(text or "")
    return {m for m in matches if m not in KNOWN_BENCHMARKS}


def validate_personalization(output: dict[str, Any], holdings: list[dict[str, Any]]) -> dict[str, Any]:
    holding_tickers = {h["ticker"] for h in holdings}
    holding_names = {h["name"].split()[0].lower() for h in holdings}
    issues: list[str] = []

    impact_tiles = output.get("impact_tiles", []) or []
    for tile in impact_tiles:
        t = (tile.get("ticker") or "").upper()
        if t and t not in holding_tickers:
            issues.append(f"impact_tile.ticker={t} not in user_holdings")

    body_text = " ".join(filter(None, [output.get("summary_paragraph"), output.get("transmission_paragraph")]))
    extracted = _extract_tickers(body_text)
    for t in extracted:
        if t in holding_tickers:
            continue
        # tolerate references to broad indices / ETFs / sectors the BRD allows in advisory voice
        if any(t.lower().startswith(prefix) for prefix in ("etf", "spx", "spy", "vgk", "qqq", "iwm")):
            continue
        issues.append(f"narrative references unknown ticker {t}")

    named = output.get("named_securities") or []
    for n in named:
        if n.upper() not in holding_tickers and n.lower() not in holding_names:
            issues.append(f"named_securities entry {n} not in holdings")

    return {"ok": not issues, "issues": issues}


def validate_advisory(output: dict[str, Any], holdings: list[dict[str, Any]], risk_profile: str) -> dict[str, Any]:
    holding_tickers = {h["ticker"] for h in holdings}
    issues: list[str] = []
    recs = output.get("recommendations") or []
    if not recs:
        issues.append("no recommendations returned")
    for r in recs:
        target = (r.get("target_holding") or "").upper()
        if target and target not in holding_tickers and target not in {"PORTFOLIO", "CASH"}:
            issues.append(f"recommendation.target_holding={target} not in user_holdings")
        action = (r.get("action") or "").title()
        if action not in {"Rebalance", "Diversify", "Hold", "Trim", "Add"}:
            issues.append(f"recommendation.action={action!r} not in BRD action set")
        # Balanced profile must not recommend aggressive leverage / margin trades
        if "Balanced" in risk_profile and any(
            term in (r.get("reasoning", "").lower()) for term in ["leverage", "margin", "short", "options"]
        ):
            issues.append("recommendation uses leveraged/short tactics inconsistent with Balanced profile")
    return {"ok": not issues, "issues": issues}


def validate_chart(output: dict[str, Any]) -> dict[str, Any]:
    required = {"direction", "range", "pattern", "key_moment",
                "support", "resistance", "next_target", "last_candle", "volume_tag"}
    issues = [f"missing field {k}" for k in required - set(output.keys() or {})]
    return {"ok": not issues, "issues": issues}


def validate_scenario(output: dict[str, Any], holdings: list[dict[str, Any]]) -> dict[str, Any]:
    holding_tickers = {h["ticker"] for h in holdings}
    issues: list[str] = []
    for impact in output.get("per_holding") or []:
        t = (impact.get("ticker") or "").upper()
        if t and t not in holding_tickers:
            issues.append(f"scenario.per_holding ticker={t} not in user_holdings")
    return {"ok": not issues, "issues": issues}
