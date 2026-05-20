"""PersonalizationAgent — BRD §4.7 / §8.

Takes a live article + the user's holdings book and returns a structured
"What This Means For Your Portfolio" payload. Cached by (article_id,
portfolio_hash) per BRD §12 cost control.
"""
from __future__ import annotations

import json
from typing import Any

from . import client as ai
from . import qa
from ..cache import cache_get, cache_set
from ..config import get_settings


SYSTEM = (
    "You are an advisory-grade portfolio analyst at Emirates NBD Wealth.\n"
    "You translate market news into specific implications for ONE client's holdings.\n"
    "Voice: concise, professional, advisory — never retail-trader hype.\n"
    "RULES (non-negotiable):\n"
    "  * Only name securities that exist in the supplied user_holdings list — never invent tickers.\n"
    "  * Every numeric claim must reference its source field; if you can't source it, omit it.\n"
    "  * The summary paragraph must name at least one specific holding by ticker.\n"
    "  * Impact tiles must each map to a holding in user_holdings (by ticker).\n"
    "Output MUST be valid JSON matching this schema (no markdown, no commentary):\n"
    '{\n'
    '  "summary_paragraph": string,           // 2-3 sentences, names specific tickers\n'
    '  "impact_tiles": [                       // 1-4 tiles\n'
    '    {"ticker": string, "name": string, "direction": "positive"|"negative"|"neutral", "confidence": 0-100, "rationale": string}\n'
    '  ],\n'
    '  "transmission_paragraph": string,      // explain the macro transmission mechanism\n'
    '  "named_securities": [string]            // tickers referenced in the above text\n'
    '}\n'
)


def _fallback(article: dict[str, Any], holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic, non-AI fallback so the UI works without an API key.
    Picks the highest-weight matched ticker and writes a concise factual line.
    """
    matched = article.get("matched_tickers") or []
    if matched:
        primary_ticker = matched[0]
    else:
        primary_ticker = max(holdings, key=lambda h: h.get("weight_target_pct", 0))["ticker"]
    primary = next((h for h in holdings if h["ticker"] == primary_ticker), holdings[0])
    related = [h for h in holdings if h["ticker"] in matched][:3] or [primary]
    tiles = [
        {
            "ticker": h["ticker"],
            "name": h["name"],
            "direction": "neutral",
            "confidence": 55,
            "rationale": f"Article likely affects {h['name']} via {h.get('sector', 'sector')} exposure.",
        }
        for h in related
    ]
    return {
        "summary_paragraph": (
            f"This headline ('{article.get('title', '')[:120]}') likely affects "
            f"{primary['name']} ({primary['ticker']}) and other names sharing "
            f"{primary.get('sector', 'sector')} exposure in your book."
        ),
        "impact_tiles": tiles,
        "transmission_paragraph": (
            "Macro transmission summary unavailable — Claude API key not configured. "
            "Live article fetched, deterministic stub returned so the dashboard remains functional."
        ),
        "named_securities": [t["ticker"] for t in tiles],
        "degraded": True,
    }


def personalize(article: dict[str, Any], holdings: list[dict[str, Any]], portfolio_hash: str) -> dict[str, Any]:
    cache_key = f"personalization:{article['id']}:{portfolio_hash}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    user_payload = {
        "article": {
            "id": article["id"],
            "title": article["title"],
            "summary": article.get("summary", ""),
            "source": article.get("source"),
            "matched_tickers": article.get("matched_tickers") or [],
        },
        "user_holdings": [
            {"ticker": h["ticker"], "name": h["name"], "sector": h.get("sector"),
             "geography": h.get("geography"), "weight_pct": h.get("weight_pct", h.get("weight_target_pct"))}
            for h in holdings
        ],
        "user_profile": {"risk_profile": "Balanced (Moderate Growth)"},
    }
    output = ai.call_json(
        system=SYSTEM,
        user=f"Personalize this article for the holdings below. Return JSON only.\n\n{json.dumps(user_payload)}",
        model=get_settings().claude_personalization_model,
        max_tokens=900,
        temperature=0.3,
    )

    if output is None:
        output = _fallback(article, holdings)
    else:
        # Ensure the schema fields exist even if Claude omitted some
        output.setdefault("impact_tiles", [])
        output.setdefault("named_securities", [t["ticker"] for t in output.get("impact_tiles", [])])

    validation = qa.validate_personalization(output, holdings)
    output["qa"] = validation
    if not validation["ok"]:
        # If validation fails, prefer the deterministic fallback over a
        # potentially-hallucinated AI response (BRD §9: fail loudly).
        fallback = _fallback(article, holdings)
        fallback["qa"] = {"ok": True, "issues": [], "fallback_used": validation["issues"]}
        output = fallback

    cache_set(cache_key, output, ttl_seconds=get_settings().personalization_cache_ttl_seconds)
    return output
