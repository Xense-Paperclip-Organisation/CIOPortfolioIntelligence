"""Portfolio pulse — health score + AI narrative (BRD §4.2)."""
from __future__ import annotations

import json
from typing import Any

from . import client as ai
from ..cache import cache_get, cache_set
from ..config import get_settings


SYSTEM = (
    "You write the daily Portfolio Pulse for one private-bank client.\n"
    "Tone: senior CIO, concise, advisory. No retail-trader language.\n"
    "Hard rules: only name securities present in the supplied holdings; cite real metrics.\n"
    "Output JSON:\n"
    '{\n'
    '  "narrative": string,                 // 3-5 sentences\n'
    '  "health_score": 0-100,\n'
    '  "headline_metric": string\n'
    '}\n'
)


def health_score(allocation: dict[str, Any], target: dict[str, Any], risk: dict[str, Any]) -> int:
    """Quick rule-based health score 0-100."""
    score = 100
    eq = allocation["asset_class"].get("Equity", 0)
    fi = allocation["asset_class"].get("Fixed Income", 0)
    cash = allocation["asset_class"].get("Cash", 0)
    target_eq = target["asset_class"].get("Equity", 50)
    target_fi_floor = target.get("fixed_income_floor_pct", 25)
    target_cash_ceiling = target.get("cash_ceiling_pct", 8)
    score -= int(min(40, max(0, abs(eq - target_eq) * 1.5)))
    if fi < target_fi_floor:
        score -= int(min(20, (target_fi_floor - fi) * 1.5))
    if cash > target_cash_ceiling:
        score -= int(min(15, (cash - target_cash_ceiling) * 1.0))
    portfolio_beta = (risk.get("portfolio") or {}).get("beta")
    if portfolio_beta and portfolio_beta > target.get("target_beta", 0.9) + 0.3:
        score -= 10
    return max(15, min(100, score))


def narrative(positions: list[dict[str, Any]], allocation: dict[str, Any],
              risk: dict[str, Any], target: dict[str, Any],
              day_pnl_pct: float) -> dict[str, Any]:
    cache_key = f"pulse:{round(day_pnl_pct, 2)}:{hash(json.dumps(allocation, sort_keys=True)) & 0xffffffff}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    deterministic_score = health_score(allocation, target, risk)
    payload = {
        "user_holdings": [
            {"ticker": p["ticker"], "weight_pct": round(p["weight_pct"], 2),
             "day_change_pct": (p.get("quote") or {}).get("day_change_pct"),
             "sector": p.get("sector"), "geography": p["geography"]}
            for p in positions
        ],
        "allocation": allocation,
        "risk_metrics": risk.get("portfolio", {}),
        "day_pnl_pct": round(day_pnl_pct, 2),
        "target_allocation": target,
        "deterministic_health_score": deterministic_score,
    }
    raw = ai.call_json(
        system=SYSTEM,
        user="Write the Portfolio Pulse narrative. Return JSON only.\n\n" + json.dumps(payload),
        model=get_settings().claude_advisory_model,
        max_tokens=600,
        temperature=0.3,
    )
    if raw is None:
        top_movers = sorted(
            [(p["ticker"], (p.get("quote") or {}).get("day_change_pct", 0)) for p in positions if p["asset_class"] == "Equity"],
            key=lambda x: abs(x[1] or 0), reverse=True,
        )[:2]
        names = ", ".join(t for t, _ in top_movers) or "core US-tech holdings"
        usa_pct = allocation["geography"].get("USA", 0)
        narr = (
            f"Portfolio moved {day_pnl_pct:+.2f}% intraday with {names} driving the change. "
            f"US-tech weighting sits at {usa_pct:.0f}% of the geographic mix — well above the "
            f"{target['geography'].get('USA', 30):.0f}% target for a Balanced profile. "
            "The Alignment Alert section below details the specific mismatches."
        )
        out = {
            "narrative": narr,
            "health_score": deterministic_score,
            "headline_metric": f"Day P&L {day_pnl_pct:+.2f}%",
            "degraded": True,
        }
    else:
        raw.setdefault("health_score", deterministic_score)
        raw.setdefault("headline_metric", f"Day P&L {day_pnl_pct:+.2f}%")
        out = raw

    cache_set(cache_key, out, ttl_seconds=300)
    return out
