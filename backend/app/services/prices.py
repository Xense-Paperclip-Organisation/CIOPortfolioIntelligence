"""Live market-price service.

Active provider is selected by the PRICE_PROVIDER env var (default: yfinance).
An optional PRICE_PROVIDER_SHADOW runs in parallel; its result is logged for
comparison only — it never reaches the caller. This allows safe 1-week shadow
validation before a hard cutover.

Fallback chain (always):
  active provider → synthesized random-walk (marked synthesized: true)

Coverage notes:
  yfinance  — US + .SR (Tadawul) + .DU (DFM, thin)
  polygon   — US only; .SR/.DU symbols fall back to synth
  alpha_vantage — US only; free tier is 25 req/day
"""
from __future__ import annotations

import logging
import random
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from ..cache import cache_get, cache_set
from ..config import get_settings
from ..logging_config import log_ctx
from .price_providers import get_active_provider, get_shadow_provider

log = logging.getLogger("services.prices")

VALID_TIMEFRAMES = ("1m", "5m", "1h", "1d", "1mo", "1yr")


# ---------------------------------------------------------------------------
# Helpers shared by multiple call sites (synthesized fallback, sukuk estimate)
# ---------------------------------------------------------------------------

def _synth_candles(seed: str, count: int = 90) -> list[dict[str, Any]]:
    """Last-resort synthesized candle series. Always marked synthesized: true."""
    rng = random.Random(seed)
    base = 100.0
    out: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0)
    for i in range(count, 0, -1):
        ts = now - timedelta(days=i)
        drift = rng.gauss(0.0005, 0.018)
        new_base = max(1.0, base * (1 + drift))
        hi = max(base, new_base) * (1 + abs(rng.gauss(0, 0.006)))
        lo = min(base, new_base) * (1 - abs(rng.gauss(0, 0.006)))
        out.append({
            "t": ts.isoformat(),
            "o": round(base, 4),
            "h": round(hi, 4),
            "l": round(lo, 4),
            "c": round(new_base, 4),
            "v": round(rng.uniform(1e5, 5e6)),
        })
        base = new_base
    return out


def _synth_quote(symbol: str) -> dict[str, Any]:
    seed = f"{symbol}:{int(time.time() // 600)}"
    rng = random.Random(seed)
    base = 100 + (hash(symbol) % 300)
    day_change = rng.gauss(0, 1.2)
    return {
        "symbol": symbol,
        "price": round(base * (1 + day_change / 100), 4),
        "open": round(base, 4),
        "high": round(base * 1.01, 4),
        "low": round(base * 0.99, 4),
        "previous_close": round(base, 4),
        "day_change_abs": round(base * day_change / 100, 4),
        "day_change_pct": round(day_change, 4),
        "week_change_pct": round(rng.gauss(0, 2.5), 4),
        "volume": int(rng.uniform(1e5, 2e6)),
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": "synthesized-fallback",
        "synthesized": True,
    }


def _synth_closes(symbol: str, days: int) -> list[float]:
    rng = random.Random(symbol)
    base = 100.0
    closes: list[float] = []
    for _ in range(days):
        base *= (1 + rng.gauss(0.0004, 0.018))
        closes.append(round(base, 4))
    return closes


# ---------------------------------------------------------------------------
# Shadow-run (fire-and-forget; errors are swallowed)
# ---------------------------------------------------------------------------

def _shadow_run_quote(shadow_symbol: str) -> None:
    try:
        shadow = get_shadow_provider()
        if shadow is None:
            return
        result = shadow.get_quote(shadow_symbol)
        log.info("SHADOW quote %s → %s", shadow_symbol, result)
    except Exception as exc:
        log.debug("Shadow quote error for %s: %s", shadow_symbol, exc)


def _shadow_run_candles(shadow_symbol: str, timeframe: str) -> None:
    try:
        shadow = get_shadow_provider()
        if shadow is None:
            return
        result = shadow.get_candles(shadow_symbol, timeframe)
        log.info("SHADOW candles %s/%s → %d bars", shadow_symbol, timeframe, len(result))
    except Exception as exc:
        log.debug("Shadow candles error for %s/%s: %s", shadow_symbol, timeframe, exc)


def _fire_shadow(fn, *args) -> None:
    """Run shadow fn in a daemon thread so it never blocks the response."""
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_quote(symbol: str) -> dict[str, Any] | None:
    if not symbol:
        return None
    cache_key = f"quote:{symbol}:{get_settings().price_provider}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Shadow run (async, no-wait)
    if get_settings().price_provider_shadow:
        _fire_shadow(_shadow_run_quote, symbol)

    provider = get_active_provider()
    quote = provider.get_quote(symbol)

    if quote is None:
        log_ctx(
            log, logging.WARNING,
            "Provider returned no quote — using synthesized fallback",
            symbol=symbol,
            provider=get_settings().price_provider,
        )
        quote = _synth_quote(symbol)

    cache_set(cache_key, quote, ttl_seconds=get_settings().price_cache_ttl_seconds)
    return quote


def get_candles(symbol: str, timeframe: str) -> dict[str, Any]:
    if timeframe not in VALID_TIMEFRAMES:
        raise ValueError(f"unknown timeframe {timeframe!r} — expected {VALID_TIMEFRAMES}")

    cache_key = f"candles:{symbol}:{timeframe}:{get_settings().price_provider}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    if get_settings().price_provider_shadow:
        _fire_shadow(_shadow_run_candles, symbol, timeframe)

    provider = get_active_provider()
    candles = provider.get_candles(symbol, timeframe)
    synthesized = not candles
    if synthesized:
        log_ctx(
            log, logging.WARNING,
            "Provider returned no candles — using synthesized fallback",
            symbol=symbol,
            timeframe=timeframe,
            provider=get_settings().price_provider,
        )
        candles = _synth_candles(f"{symbol}:{timeframe}")

    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "source": get_settings().price_provider if not synthesized else "synthesized-fallback",
        "synthesized": synthesized,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }
    cache_set(cache_key, payload, ttl_seconds=get_settings().price_cache_ttl_seconds)
    return payload


def get_close_history(symbol: str, days: int = 365) -> list[float]:
    cache_key = f"closes:{symbol}:{days}:{get_settings().price_provider}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    provider = get_active_provider()
    closes = provider.get_close_history(symbol, days)
    if not closes:
        closes = _synth_closes(symbol, days)

    cache_set(cache_key, closes, ttl_seconds=get_settings().price_cache_ttl_seconds)
    return closes


def get_benchmark_closes(symbol: str = "^GSPC", days: int = 365) -> list[float]:
    return get_close_history(symbol, days=days)


def sukuk_price_estimate(coupon_pct: float, maturity_iso: str, duration_years: float,
                         current_yield_pct: float) -> dict[str, Any]:
    """Synthesize a sukuk clean price from the live yield curve + duration."""
    try:
        maturity = datetime.fromisoformat(maturity_iso)
    except Exception:
        maturity = datetime.now() + timedelta(days=365 * 5)
    years_to_maturity = max(0.25, (maturity - datetime.now()).days / 365.25)
    price = 100.0 + (coupon_pct - current_yield_pct) * min(duration_years, years_to_maturity)
    return {
        "price": round(price, 4),
        "yield_pct": current_yield_pct,
        "duration_years": duration_years,
        "years_to_maturity": round(years_to_maturity, 2),
        "synthesized": True,
        "source": "yield-curve+duration",
    }
