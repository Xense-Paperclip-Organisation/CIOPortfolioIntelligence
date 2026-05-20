"""yfinance price provider — wraps the existing unofficial Yahoo Finance logic."""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from .base import PriceProvider

log = logging.getLogger("services.prices.yfinance")


def _tf_to_yf(timeframe: str) -> tuple[str, str]:
    return {
        "1m": ("1d", "1m"),
        "5m": ("5d", "5m"),
        "1h": ("1mo", "1h"),
        "1d": ("6mo", "1d"),
        "1mo": ("5y", "1mo"),
        "1yr": ("max", "3mo"),
    }[timeframe]


def _df_to_candles(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    out: list[dict[str, Any]] = []
    df = df.reset_index()
    ts_col = df.columns[0]
    for _, row in df.iterrows():
        ts = row[ts_col]
        if hasattr(ts, "to_pydatetime"):
            ts = ts.to_pydatetime()
        if isinstance(ts, datetime):
            ts_iso = ts.replace(tzinfo=ts.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
        else:
            ts_iso = str(ts)
        try:
            open_ = float(row.get("Open"))
            high_ = float(row.get("High"))
            low_ = float(row.get("Low"))
            close_ = float(row.get("Close"))
            vol_ = float(row.get("Volume", 0) or 0)
        except (TypeError, ValueError):
            continue
        if any(math.isnan(x) for x in (open_, high_, low_, close_)):
            continue
        out.append({"t": ts_iso, "o": open_, "h": high_, "l": low_, "c": close_, "v": vol_})
    return out


class YFinanceProvider(PriceProvider):
    def __init__(self, _cfg: Any = None) -> None:
        pass

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        try:
            tkr = yf.Ticker(symbol)
            hist = tkr.history(period="5d", interval="1d", auto_adjust=False)
            if hist is not None and not hist.empty:
                last = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else last
                week_first = hist.iloc[0]
                return {
                    "symbol": symbol,
                    "price": float(last["Close"]),
                    "open": float(last["Open"]),
                    "high": float(last["High"]),
                    "low": float(last["Low"]),
                    "previous_close": float(prev["Close"]),
                    "day_change_abs": float(last["Close"]) - float(prev["Close"]),
                    "day_change_pct": (float(last["Close"]) - float(prev["Close"])) / float(prev["Close"]) * 100
                        if float(prev["Close"]) else 0.0,
                    "week_change_pct": (float(last["Close"]) - float(week_first["Close"])) / float(week_first["Close"]) * 100
                        if float(week_first["Close"]) else 0.0,
                    "volume": float(last.get("Volume", 0) or 0),
                    "as_of": last.name.isoformat() if hasattr(last.name, "isoformat") else str(last.name),
                    "source": "yfinance",
                    "synthesized": False,
                }
        except Exception as exc:
            log.warning("yfinance quote failed for %s: %s", symbol, exc)
        return None

    def get_candles(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        try:
            period, interval = _tf_to_yf(timeframe)
            tkr = yf.Ticker(symbol)
            df = tkr.history(period=period, interval=interval, auto_adjust=False)
            return _df_to_candles(df)
        except Exception as exc:
            log.warning("yfinance candles failed for %s/%s: %s", symbol, timeframe, exc)
            return []

    def get_close_history(self, symbol: str, days: int = 365) -> list[float]:
        try:
            tkr = yf.Ticker(symbol)
            df = tkr.history(period=f"{max(days, 30)}d", interval="1d", auto_adjust=False)
            if df is not None and not df.empty:
                return [float(x) for x in df["Close"].dropna().tolist()]
        except Exception as exc:
            log.warning("yfinance close history failed for %s: %s", symbol, exc)
        return []
