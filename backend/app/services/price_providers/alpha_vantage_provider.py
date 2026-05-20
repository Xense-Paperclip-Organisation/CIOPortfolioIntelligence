"""Alpha Vantage price provider.

Requires ALPHA_VANTAGE_API_KEY.  Free tier: 25 requests/day. Paid ($50/mo):
500 req/min. Poor coverage for DFM (.DU) and Tadawul (.SR) tickers — those
fall back to synth. Good fallback for US equities when Polygon is unavailable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests

from .base import PriceProvider

log = logging.getLogger("services.prices.alpha_vantage")

_BASE = "https://www.alphavantage.co/query"


class AlphaVantageProvider(PriceProvider):
    def __init__(self, cfg: Any) -> None:
        self._api_key: str = getattr(cfg, "alpha_vantage_api_key", "") or ""
        self._timeout: float = getattr(cfg, "request_timeout_seconds", 12.0)

    def _get(self, params: dict) -> dict | None:
        if not self._api_key:
            log.warning("ALPHA_VANTAGE_API_KEY not set")
            return None
        try:
            p = {**params, "apikey": self._api_key}
            r = requests.get(_BASE, params=p, timeout=self._timeout)
            r.raise_for_status()
            data = r.json()
            if "Note" in data or "Information" in data:
                log.warning("Alpha Vantage rate-limit: %s", data.get("Note") or data.get("Information"))
                return None
            return data
        except Exception as exc:
            log.warning("Alpha Vantage request failed: %s", exc)
            return None

    def _clean_symbol(self, symbol: str) -> str | None:
        """Strip Yahoo suffixes. .SR and .DU have no AV coverage."""
        if "." in symbol:
            return None
        return symbol.upper()

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        sym = self._clean_symbol(symbol)
        if not sym:
            return None
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": sym})
        if not data:
            return None
        q = data.get("Global Quote", {})
        price_str = q.get("05. price")
        if not price_str:
            return None
        price = float(price_str)
        prev_close_str = q.get("08. previous close", "0")
        prev_close = float(prev_close_str) if prev_close_str else 0.0
        return {
            "symbol": symbol,
            "price": price,
            "open": float(q.get("02. open", 0) or 0),
            "high": float(q.get("03. high", 0) or 0),
            "low": float(q.get("04. low", 0) or 0),
            "previous_close": prev_close,
            "day_change_abs": float(q.get("09. change", 0) or 0),
            "day_change_pct": float(q.get("10. change percent", "0%").replace("%", "") or 0),
            "week_change_pct": None,
            "volume": float(q.get("06. volume", 0) or 0),
            "as_of": q.get("07. latest trading day", datetime.now(timezone.utc).date().isoformat()),
            "source": "alpha_vantage",
            "synthesized": False,
        }

    def get_candles(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        sym = self._clean_symbol(symbol)
        if not sym:
            return []

        intraday = timeframe in ("1m", "5m", "1h")
        if intraday:
            interval_map = {"1m": "1min", "5m": "5min", "1h": "60min"}
            data = self._get({
                "function": "TIME_SERIES_INTRADAY",
                "symbol": sym,
                "interval": interval_map[timeframe],
                "outputsize": "full",
            })
            ts_key = f"Time Series ({interval_map[timeframe]})"
        elif timeframe in ("1d", "1yr"):
            data = self._get({"function": "TIME_SERIES_DAILY", "symbol": sym, "outputsize": "full"})
            ts_key = "Time Series (Daily)"
        else:  # 1mo
            data = self._get({"function": "TIME_SERIES_MONTHLY", "symbol": sym})
            ts_key = "Monthly Time Series"

        if not data:
            return []
        series = data.get(ts_key, {})
        candles: list[dict[str, Any]] = []
        for ts_str, bar in sorted(series.items()):
            candles.append({
                "t": ts_str,
                "o": float(bar.get("1. open", 0)),
                "h": float(bar.get("2. high", 0)),
                "l": float(bar.get("3. low", 0)),
                "c": float(bar.get("4. close", 0)),
                "v": float(bar.get("5. volume", 0) or 0),
            })
        return candles

    def get_close_history(self, symbol: str, days: int = 365) -> list[float]:
        sym = self._clean_symbol(symbol)
        if not sym:
            return []
        data = self._get({"function": "TIME_SERIES_DAILY", "symbol": sym, "outputsize": "full"})
        if not data:
            return []
        series = data.get("Time Series (Daily)", {})
        closes = [float(v["4. close"]) for _, v in sorted(series.items()) if "4. close" in v]
        return closes[-days:]
