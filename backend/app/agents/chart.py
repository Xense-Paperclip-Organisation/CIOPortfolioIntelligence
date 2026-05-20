"""ChartAgent — per-holding candle narrative (BRD §4.6).

Given a recent OHLCV window, returns the structured explanation panel
("Direction / Range / Volume / Pattern / Key Moment / Watch Levels / Last
Candle"). Deterministic Python fallback so the chart panel always populates.
"""
from __future__ import annotations

import json
import statistics
from typing import Any

from . import client as ai
from . import qa
from ..cache import cache_get, cache_set
from ..config import get_settings


SYSTEM = (
    "You are a senior markets technician at Emirates NBD Wealth.\n"
    "You explain a single chart to a private-bank client in 5 short lines.\n"
    "Voice: factual, neutral, advisory. No hype, no price targets you can't justify.\n"
    "Hard rules:\n"
    "  * Use only the OHLCV window provided. Don't invent prices.\n"
    "  * Mark patterns clearly (e.g. 'staircase breakout', 'lower-high reversal').\n"
    "  * Watch levels must come from the supplied window: closest swing high/low.\n"
    "Output MUST be valid JSON matching:\n"
    '{\n'
    '  "direction": {"pct": number, "tag": string},          // tag e.g. "Strongly Bullish"\n'
    '  "range": {"high": number, "low": number},\n'
    '  "volume_tag": string,                                  // "Institutional"|"Retail"|...\n'
    '  "pattern": {"name": string, "explanation": string},\n'
    '  "key_moment": string,\n'
    '  "support": number,\n'
    '  "resistance": number,\n'
    '  "next_target": number,\n'
    '  "last_candle": string\n'
    '}\n'
)


def _deterministic(candles: list[dict[str, Any]], ticker: str) -> dict[str, Any]:
    if not candles:
        return {
            "direction": {"pct": 0, "tag": "Insufficient Data"},
            "range": {"high": 0, "low": 0},
            "volume_tag": "n/a",
            "pattern": {"name": "n/a", "explanation": "No candles available."},
            "key_moment": "n/a",
            "support": 0,
            "resistance": 0,
            "next_target": 0,
            "last_candle": "n/a",
            "degraded": True,
        }
    closes = [c["c"] for c in candles]
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    volumes = [c.get("v", 0) for c in candles]
    first = closes[0]
    last = closes[-1]
    pct = (last - first) / first * 100 if first else 0
    tag = (
        "Strongly Bullish" if pct > 6 else
        "Bullish" if pct > 1.5 else
        "Strongly Bearish" if pct < -6 else
        "Bearish" if pct < -1.5 else
        "Neutral"
    )
    high = max(highs)
    low = min(lows)
    vol_median = statistics.median(volumes) if volumes else 0
    last_vol = volumes[-1] if volumes else 0
    volume_tag = "Institutional" if last_vol > vol_median * 1.4 else ("Retail" if last_vol < vol_median * 0.7 else "Mixed")

    # Pattern heuristic
    last_three = closes[-3:]
    if len(last_three) >= 3 and last_three[-1] > last_three[-2] > last_three[-3]:
        pattern_name = "Higher-High Continuation"
        pattern_explanation = "Three sequential higher closes suggest sustained demand."
    elif len(last_three) >= 3 and last_three[-1] < last_three[-2] < last_three[-3]:
        pattern_name = "Lower-Low Reversal"
        pattern_explanation = "Three sequential lower closes — sellers in control."
    else:
        pattern_name = "Range-Bound"
        pattern_explanation = "No clear directional commit in the last 3 candles."

    support = round(min(lows[-20:]) if len(lows) >= 20 else low, 4)
    resistance = round(max(highs[-20:]) if len(highs) >= 20 else high, 4)
    next_target = round(last + (last - support), 4) if pct > 0 else round(last - (resistance - last), 4)
    last_candle = (
        f"Last candle closed at {last:.2f}, range {min(lows[-1], last):.2f}–{max(highs[-1], last):.2f}; "
        f"{'gap up' if last > closes[-2] * 1.005 else 'gap down' if last < closes[-2] * 0.995 else 'inside prior range'}."
        if len(closes) > 1 else f"Last candle close: {last:.2f}."
    )
    key_moment = (
        f"{ticker} {'broke above' if last > resistance * 0.99 else 'rejected from' if last < resistance * 0.97 else 'consolidating near'} the "
        f"{resistance:.2f} swing-high."
    )
    return {
        "direction": {"pct": round(pct, 2), "tag": tag},
        "range": {"high": round(high, 4), "low": round(low, 4)},
        "volume_tag": volume_tag,
        "pattern": {"name": pattern_name, "explanation": pattern_explanation},
        "key_moment": key_moment,
        "support": support,
        "resistance": resistance,
        "next_target": next_target,
        "last_candle": last_candle,
        "degraded": False,
    }


def explain(candles: list[dict[str, Any]], ticker: str, timeframe: str) -> dict[str, Any]:
    cache_key = f"chart_explain:{ticker}:{timeframe}:{len(candles)}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    deterministic = _deterministic(candles, ticker)
    payload = {
        "ticker": ticker,
        "timeframe": timeframe,
        "candles_tail": candles[-50:],
        "deterministic_baseline": deterministic,
    }
    raw = ai.call_json(
        system=SYSTEM,
        user="Explain this chart. Return JSON only.\n\n" + json.dumps(payload),
        model=get_settings().claude_personalization_model,
        max_tokens=700,
        temperature=0.25,
    )
    output = raw if raw and qa.validate_chart(raw)["ok"] else deterministic
    if raw and not qa.validate_chart(raw)["ok"]:
        output = deterministic
        output["qa"] = {"ok": True, "fallback_used": qa.validate_chart(raw)["issues"]}
    else:
        output.setdefault("qa", {"ok": True, "issues": []})

    cache_set(cache_key, output, ttl_seconds=get_settings().price_cache_ttl_seconds)
    return output
