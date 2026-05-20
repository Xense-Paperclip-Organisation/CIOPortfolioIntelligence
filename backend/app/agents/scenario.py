"""ScenarioAgent — BRD §4.11.

Estimates directional impact of a stress scenario on the user's actual
holdings. Deterministic stress rules drive a fallback so the tornado chart
always has data; Claude is layered in when ANTHROPIC_API_KEY is configured.
"""
from __future__ import annotations

import json
from typing import Any

from . import client as ai
from . import qa
from ..config import get_settings


SCENARIOS = [
    {"id": "us-tech-drawdown", "label": "US tech 20% correction",
     "description": "AAPL/NVDA/TSLA/MSFT/META all draw down 20% in 30 days."},
    {"id": "fed-cuts-50", "label": "Fed cuts 50bps",
     "description": "Surprise 50bps Fed cut: USD weakens, duration rallies."},
    {"id": "oil-down-15", "label": "Brent down 15%",
     "description": "Oil price collapses 15%: GCC energy exporters under pressure."},
    {"id": "aed-depeg", "label": "AED de-peg risk",
     "description": "Speculative AED de-peg story: AED weakens 5% vs USD."},
    {"id": "vision-2030", "label": "Saudi Vision 2030 acceleration",
     "description": "Major reform push: Aramco + Tadawul rally; oil at marginal cost."},
]


# Deterministic sensitivity table (impact % per holding given each scenario).
SENSITIVITIES = {
    "us-tech-drawdown": {
        "AAPL": -19, "NVDA": -22, "TSLA": -25, "MSFT": -18, "META": -21,
        "EMAAR.DU": -2, "2222.SR": -1, "GLD": +3, "KSA-SUKUK-5.6-2030": +1, "CASH": 0,
    },
    "fed-cuts-50": {
        "AAPL": +5, "NVDA": +8, "TSLA": +9, "MSFT": +5, "META": +6,
        "EMAAR.DU": +3, "2222.SR": +2, "GLD": +6, "KSA-SUKUK-5.6-2030": +3, "CASH": -1,
    },
    "oil-down-15": {
        "AAPL": 0, "NVDA": 0, "TSLA": -1, "MSFT": 0, "META": 0,
        "EMAAR.DU": -4, "2222.SR": -16, "GLD": +2, "KSA-SUKUK-5.6-2030": -2, "CASH": 0,
    },
    "aed-depeg": {
        "AAPL": +4, "NVDA": +4, "TSLA": +4, "MSFT": +4, "META": +4,
        "EMAAR.DU": -5, "2222.SR": -2, "GLD": +3, "KSA-SUKUK-5.6-2030": -1, "CASH": +5,
    },
    "vision-2030": {
        "AAPL": +1, "NVDA": +1, "TSLA": +1, "MSFT": +1, "META": +1,
        "EMAAR.DU": +8, "2222.SR": +12, "GLD": -1, "KSA-SUKUK-5.6-2030": +2, "CASH": 0,
    },
}


SYSTEM = (
    "You are a portfolio strategist running a what-if scenario for a private-bank client.\n"
    "Given a scenario and the client's holdings, return directional impacts grounded in macro logic.\n"
    "Rules:\n"
    "  * Only reference securities present in user_holdings.\n"
    "  * Return percentage moves between -40 and +30. Be conservative.\n"
    "  * Include a one-paragraph rationale for the overall scenario.\n"
    "Output JSON:\n"
    '{\n'
    '  "rationale": string,\n'
    '  "per_holding": [{"ticker": string, "impact_pct": number, "comment": string}],\n'
    '  "total_portfolio_impact_pct": number\n'
    '}\n'
)


def _fallback(scenario_id: str, positions: list[dict[str, Any]]) -> dict[str, Any]:
    table = SENSITIVITIES.get(scenario_id) or {}
    per_holding: list[dict[str, Any]] = []
    total = 0.0
    for p in positions:
        impact = table.get(p["ticker"], 0)
        contribution = p["weight_pct"] / 100.0 * impact
        total += contribution
        per_holding.append({
            "ticker": p["ticker"],
            "impact_pct": impact,
            "comment": f"Sensitivity baseline for {p['ticker']} under this scenario.",
        })
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), SCENARIOS[0])
    return {
        "scenario": scenario,
        "rationale": scenario["description"],
        "per_holding": per_holding,
        "total_portfolio_impact_pct": round(total, 2),
        "degraded": True,
    }


def run(scenario_id: str, positions: list[dict[str, Any]]) -> dict[str, Any]:
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if scenario is None:
        scenario = SCENARIOS[0]
        scenario_id = scenario["id"]
    payload = {
        "scenario": scenario,
        "user_holdings": [
            {"ticker": p["ticker"], "name": p["name"], "sector": p.get("sector"),
             "geography": p["geography"], "weight_pct": round(p["weight_pct"], 2)}
            for p in positions
        ],
    }
    raw = ai.call_json(
        system=SYSTEM,
        user="Run this scenario. Return JSON only.\n\n" + json.dumps(payload),
        model=get_settings().claude_advisory_model,
        max_tokens=900,
        temperature=0.25,
    )
    if raw is None:
        return _fallback(scenario_id, positions)
    raw.setdefault("scenario", scenario)
    raw.setdefault("per_holding", [])
    raw.setdefault("rationale", scenario["description"])
    if not qa.validate_scenario(raw, positions)["ok"]:
        return _fallback(scenario_id, positions)
    raw["qa"] = {"ok": True, "issues": []}
    return raw


def list_scenarios() -> list[dict[str, Any]]:
    return SCENARIOS
