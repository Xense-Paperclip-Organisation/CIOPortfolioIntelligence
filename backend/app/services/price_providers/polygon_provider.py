"""Polygon.io price provider.

Requires POLYGON_API_KEY env var (paid tier recommended for p99 < 500ms).
Ticker symbol mapping:
  - US equities: pass-through (AAPL, NVDA, ...)
  - Tadawul (Saudi): no Polygon coverage → returns [] / None (falls back to synth)
  - DFM (UAE): no Polygon coverage → falls back to synth

Free tier limit: 5 API calls/min. Starter ($29/mo): unlimited calls, 15-min delayed.
Developer ($79/mo+): real-time. For demo use either tier is fine.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .base import PriceProvider

log = logging.getLogger("services.prices.polygon")

_BASE = "https://api.polygon.io"


class PolygonProvider(PriceProvider):
    def __init__(self, cfg: Any) -> None:
        self._api_key: str = getattr(cfg, "polygon_api_key", "") or ""
        self._timeout: float = getattr(cfg, "request_timeout_seconds", 12.0)

    def _get(self, path: str, params: dict | None = None) -> dict | None:
        if not self._api_key:
            log.warning("POLYGON_API_KEY not set — Polygon provider cannot fetch data")
            return None
        try:
            p = {**(params or {}), "apiKey": self._api_key}
            r = requests.get(f"{_BASE}{path}", params=p, timeout=self._timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            log.warning("Polygon request failed %s: %s", path, exc)
            return None

    def _to_polygon_ticker(self, symbol: str) -> str | None:
        """Map yahoo-style suffixed symbols to Polygon tickers (US only)."""
        if "." in symbol:
            # .SR (Tadawul) and .DU (DFM) not covered by Polygon
            return None
        return symbol.upper()

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        ticker = self._to_polygon_ticker(symbol)
        if not ticker:
            return None
        data = self._get(f"/v2/last/trade/{ticker}")
        if not data or data.get("status") != "OK":
            return None
        result = data.get("results", {})
        price = result.get("p")
        if price is None:
            return None

        # Get previous close for day_change
        prev_data = self._get(f"/v2/aggs/ticker/{ticker}/prev")
        prev_close: float | None = None
        if prev_data and prev_data.get("results"):
            prev_close = prev_data["results"][0].get("c")

        return {
            "symbol": symbol,
            "price": float(price),
            "open": None,
            "high": None,
            "low": None,
            "previous_close": float(prev_close) if prev_close else None,
            "day_change_abs": float(price) - float(prev_close) if prev_close else None,
            "day_change_pct": (float(price) - float(prev_close)) / float(prev_close) * 100
                if prev_close else None,
            "week_change_pct": None,
            "volume": float(result.get("s", 0) or 0),
            "as_of": datetime.now(timezone.utc).isoformat(),
            "source": "polygon",
            "synthesized": False,
        }

    def get_candles(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        ticker = self._to_polygon_ticker(symbol)
        if not ticker:
            return []

        tf_map = {
            "1m":  ("minute", 1,  1),
            "5m":  ("minute", 5,  5),
            "1h":  ("hour",   1, 30),
            "1d":  ("day",    1, 180),
            "1mo": ("month",  1, 60),
            "1yr": ("month",  3, 120),
        }
        if timeframe not in tf_map:
            return []
        multiplier_unit, multiplier, lookback_days = tf_map[timeframe]

        to_dt = datetime.now(timezone.utc)
        from_dt = to_dt - timedelta(days=lookback_days)
        data = self._get(
            f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{multiplier_unit}"
            f"/{from_dt.strftime('%Y-%m-%d')}/{to_dt.strftime('%Y-%m-%d')}",
            {"adjusted": "true", "sort": "asc", "limit": 50000},
        )
        if not data or not data.get("results"):
            return []

        candles: list[dict[str, Any]] = []
        for bar in data["results"]:
            ts = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc).isoformat()
            candles.append({
                "t": ts,
                "o": bar.get("o"),
                "h": bar.get("h"),
                "l": bar.get("l"),
                "c": bar.get("c"),
                "v": bar.get("v", 0),
            })
        return candles

    def get_close_history(self, symbol: str, days: int = 365) -> list[float]:
        ticker = self._to_polygon_ticker(symbol)
        if not ticker:
            return []

        to_dt = datetime.now(timezone.utc)
        from_dt = to_dt - timedelta(days=days + 5)
        data = self._get(
            f"/v2/aggs/ticker/{ticker}/range/1/day"
            f"/{from_dt.strftime('%Y-%m-%d')}/{to_dt.strftime('%Y-%m-%d')}",
            {"adjusted": "true", "sort": "asc", "limit": 50000},
        )
        if not data or not data.get("results"):
            return []
        return [float(bar["c"]) for bar in data["results"] if "c" in bar][-days:]
