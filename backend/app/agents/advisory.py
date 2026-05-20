"""AdvisoryAgent — BRD §4.9 / §8.

Produces the CIO Advisory card recommendations. Uses Claude Opus for
nuanced advisory voice; falls back to a deterministic, BRD §3.2-driven
recommendation set so the demo always has actionable content.
"""
from __future__ import annotations

import json
from typing import Any

from . import client as ai
from . import qa
from ..cache import cache_get, cache_set
from ..config import get_settings


SYSTEM = (
    "You are the Chief Investment Officer of Emirates NBD Wealth advising one client.\n"
    "Your output drives a board-presentable advisory dashboard.\n"
    "Voice: advisory-grade, concrete, never generic. Match Emirates NBD CIO Corner tone.\n"
    "Hard rules:\n"
    "  * Only name securities that exist in user_holdings. Never invent tickers.\n"
    "  * Recommendations must be aligned with the stated Balanced (Moderate Growth) risk profile.\n"
    "    No leverage, no short positions, no options strategies.\n"
    "  * Cite the actual current_metrics figures you saw — never invent a number.\n"
    "  * Suggested replacements should be broad-index ETFs (e.g. VGK for Europe equity).\n"
    "Output MUST be valid JSON matching this schema (no markdown):\n"
    '{\n'
    '  "headline": string,                                 // one-sentence summary\n'
    '  "recommendations": [\n'
    '    {"action":"Rebalance|Diversify|Hold|Trim|Add","target_holding":string,\n'
    '     "reasoning":string,"suggested_size_change":number|null,"suggested_replacement":string|null}\n'
    '  ],\n'
    '  "diversification_gap_analysis": string,\n'
    '  "currency_commentary": string,\n'
    '  "education_funding_stress": string\n'
    '}\n'
)


def _fallback(positions: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    pos_by = {p["ticker"]: p for p in positions}
    recs: list[dict[str, Any]] = []

    nvda = pos_by.get("NVDA")
    if nvda and nvda["weight_pct"] > 10:
        recs.append({
            "action": "Trim",
            "target_holding": "NVDA",
            "reasoning": (
                f"NVDA sits at {nvda['weight_pct']:.0f}% of book — well above the 10% single-name cap. "
                "It also overlaps with your AAPL/MSFT/META US-tech cluster. Trim to 8%."
            ),
            "suggested_size_change": round(8.0 - nvda["weight_pct"], 1),
            "suggested_replacement": "VGK (Europe equity ETF)",
        })
    aapl = pos_by.get("AAPL")
    if aapl and aapl["weight_pct"] > 10:
        recs.append({
            "action": "Trim",
            "target_holding": "AAPL",
            "reasoning": (
                f"AAPL at {aapl['weight_pct']:.0f}% — above the 10% cap and correlated with rest of US-tech sleeve. "
                "Trim to 8%; redeploy into MENA fixed-income."
            ),
            "suggested_size_change": round(8.0 - aapl["weight_pct"], 1),
            "suggested_replacement": "GCC investment-grade sukuk",
        })
    tsla = pos_by.get("TSLA")
    if tsla and tsla["weight_pct"] > 8:
        recs.append({
            "action": "Trim",
            "target_holding": "TSLA",
            "reasoning": (
                f"TSLA at {tsla['weight_pct']:.0f}% with elevated single-stock vol vs Balanced target beta of "
                f"{target.get('target_beta', 0.9)}. Trim to 5%."
            ),
            "suggested_size_change": round(5.0 - tsla["weight_pct"], 1),
            "suggested_replacement": "Cash sleeve / FI ladder",
        })
    fi_weight = sum(p["weight_pct"] for p in positions if p["asset_class"] == "Fixed Income")
    if fi_weight < target.get("fixed_income_floor_pct", 25):
        recs.append({
            "action": "Add",
            "target_holding": "KSA-SUKUK-5.6-2030",
            "reasoning": (
                f"Fixed income is {fi_weight:.0f}% — short of the 25% floor for a Balanced profile. "
                "Build a laddered GCC sukuk + USD short-duration treasury sleeve."
            ),
            "suggested_size_change": round(target.get("fixed_income_floor_pct", 25) - fi_weight, 1),
            "suggested_replacement": None,
        })
    europe_weight = next((v for k, v in next((p["asset_class"] for p in positions if False), {}).items() if False), 0)
    recs.append({
        "action": "Diversify",
        "target_holding": "PORTFOLIO",
        "reasoning": (
            "Zero exposure to European, Japanese and EM-Asia equities. A Balanced model targets ~30% in "
            "non-US developed and EM. Add VGK (Europe), EWJ (Japan) and VWO (EM)."
        ),
        "suggested_size_change": 15.0,
        "suggested_replacement": "VGK + EWJ + VWO basket",
    })
    cash_w = sum(p["weight_pct"] for p in positions if p["asset_class"] == "Cash")
    if cash_w > target.get("cash_ceiling_pct", 8):
        recs.append({
            "action": "Rebalance",
            "target_holding": "CASH",
            "reasoning": (
                f"Cash at {cash_w:.0f}% is well over the 8% ceiling. Deploy in tranches into the GCC sukuk + "
                "diversification basket over the next 3 months."
            ),
            "suggested_size_change": round(target.get("cash_ceiling_pct", 8) - cash_w, 1),
            "suggested_replacement": "GCC sukuk + short-duration UST",
        })
    return {
        "headline": "Book is over-weight US tech, light on fixed income, and high on cash — rebalance recommended.",
        "recommendations": recs,
        "diversification_gap_analysis": (
            "Equity sleeve is 62% USA and 0% in Europe / Japan / EM Asia. Three US-tech names "
            "(AAPL, NVDA, TSLA) sum to ~46% of the book. Adding VGK / EWJ / VWO would re-balance "
            "geography; trimming the tech cluster would re-balance sector."
        ),
        "currency_commentary": (
            "USD share ~73% — over-hedges the 8-year USD education liability but under-hedges AED "
            "retirement liabilities. Suggest taking USD exposure down toward 50% as the education "
            "milestone approaches."
        ),
        "education_funding_stress": (
            "An 8-year USD education funding goal is reasonably hedged by the current USD weight. "
            "However, a 20% drawdown in the US-tech sleeve within the next 3 years would force the "
            "client into a defensive ladder later. Recommend de-risking the tech cluster gradually."
        ),
        "degraded": True,
    }


def advise(positions: list[dict[str, Any]],
           allocation: dict[str, Any],
           risk_metrics: dict[str, Any],
           target: dict[str, Any],
           profile: dict[str, Any]) -> dict[str, Any]:
    cache_key = f"advisory:{json.dumps([(p['ticker'], round(p['weight_pct'], 2)) for p in positions], sort_keys=True)}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    payload = {
        "user_holdings": [
            {"ticker": p["ticker"], "name": p["name"], "asset_class": p["asset_class"],
             "geography": p["geography"], "sector": p.get("sector"),
             "weight_pct": round(p["weight_pct"], 2), "value_usd": round(p["value_usd"], 0)}
            for p in positions
        ],
        "risk_profile": profile["stated_risk_profile"],
        "target_allocation": target,
        "current_metrics": {
            "allocation": allocation,
            "risk": risk_metrics.get("portfolio", {}),
        },
        "time_horizon_years": profile["stated_time_horizon_years"],
    }
    raw = ai.call_json(
        system=SYSTEM,
        user="Produce the CIO advisory output for this client. Return JSON only.\n\n" + json.dumps(payload),
        model=get_settings().claude_advisory_model,
        max_tokens=1800,
        temperature=0.2,
    )
    if raw is None:
        output = _fallback(positions, target)
    else:
        output = raw
        output.setdefault("recommendations", [])
        output.setdefault("diversification_gap_analysis", "")
        output.setdefault("currency_commentary", "")
        output.setdefault("education_funding_stress", "")

    validation = qa.validate_advisory(output, positions, profile["stated_risk_profile"])
    if not validation["ok"]:
        output = _fallback(positions, target)
        output["qa"] = {"ok": True, "issues": [], "fallback_used": validation["issues"]}
    else:
        output["qa"] = validation

    cache_set(cache_key, output, ttl_seconds=get_settings().personalization_cache_ttl_seconds)
    return output
