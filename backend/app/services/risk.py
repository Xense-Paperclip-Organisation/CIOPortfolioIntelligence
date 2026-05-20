"""Risk metrics: beta, vol, Sharpe, max drawdown, correlation.

All series come from `prices.get_close_history` (yfinance, cached).
Calculations are vanilla annualised quant — independently verifiable from
the same daily-close series.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import prices as prices_svc
from . import macro as macro_svc


TRADING_DAYS = 252


def _aligned_returns(symbols: list[str], days: int = 365) -> tuple[list[str], np.ndarray]:
    """Returns aligned daily log-returns matrix across the supplied symbols."""
    series = []
    valid_syms: list[str] = []
    min_len = None
    for sym in symbols:
        closes = prices_svc.get_close_history(sym, days=days)
        if len(closes) < 30:
            continue
        valid_syms.append(sym)
        series.append(closes)
        min_len = len(closes) if min_len is None else min(min_len, len(closes))
    if not series or min_len is None:
        return [], np.empty((0, 0))
    aligned = np.array([s[-min_len:] for s in series], dtype=float)
    log_returns = np.diff(np.log(aligned), axis=1)
    return valid_syms, log_returns


def correlation_matrix(symbols: list[str]) -> dict[str, Any]:
    syms, returns = _aligned_returns(symbols)
    if returns.size == 0:
        return {"symbols": [], "matrix": []}
    cm = np.corrcoef(returns)
    matrix = [[float(round(cm[i, j], 4)) for j in range(len(syms))] for i in range(len(syms))]
    return {"symbols": syms, "matrix": matrix}


def _benchmark_aligned(sym: str, days: int = 365) -> tuple[np.ndarray, np.ndarray]:
    sym_closes = prices_svc.get_close_history(sym, days=days)
    bench_closes = prices_svc.get_benchmark_closes("^GSPC", days=days)
    n = min(len(sym_closes), len(bench_closes))
    if n < 30:
        return np.array([]), np.array([])
    s = np.array(sym_closes[-n:], dtype=float)
    b = np.array(bench_closes[-n:], dtype=float)
    return np.diff(np.log(s)), np.diff(np.log(b))


def beta(sym: str) -> float | None:
    s_ret, b_ret = _benchmark_aligned(sym)
    if s_ret.size == 0:
        return None
    cov = np.cov(s_ret, b_ret, ddof=0)
    if cov[1, 1] == 0:
        return None
    return float(round(cov[0, 1] / cov[1, 1], 4))


def volatility_annualised(sym: str, days: int = 60) -> float | None:
    closes = prices_svc.get_close_history(sym, days=days)
    if len(closes) < 10:
        return None
    rets = np.diff(np.log(np.array(closes, dtype=float)))
    return float(round(rets.std(ddof=1) * math.sqrt(TRADING_DAYS) * 100, 2))


def max_drawdown(sym: str, days: int = 365) -> float | None:
    closes = prices_svc.get_close_history(sym, days=days)
    if len(closes) < 30:
        return None
    arr = np.array(closes, dtype=float)
    peaks = np.maximum.accumulate(arr)
    dd = (arr - peaks) / peaks
    return float(round(dd.min() * 100, 2))


def sharpe(sym: str, days: int = 365) -> float | None:
    closes = prices_svc.get_close_history(sym, days=days)
    if len(closes) < 30:
        return None
    arr = np.array(closes, dtype=float)
    rets = np.diff(np.log(arr))
    rf_daily = macro_svc.risk_free_rate_1y() / TRADING_DAYS
    excess = rets - rf_daily
    sigma = excess.std(ddof=1)
    if sigma == 0:
        return None
    return float(round((excess.mean() / sigma) * math.sqrt(TRADING_DAYS), 3))


def portfolio_risk(positions: list[dict[str, Any]]) -> dict[str, Any]:
    equity_positions = [p for p in positions if p.get("asset_class") not in ("Cash", "Fixed Income")]
    weights = []
    symbols = []
    for p in equity_positions:
        # use yahoo_symbol-equivalent: equity positions keyed on ticker
        sym = p.get("ticker")
        if sym in ("CASH",) or not sym:
            continue
        # map our ticker to yahoo symbol
        yh = {"AAPL": "AAPL", "NVDA": "NVDA", "TSLA": "TSLA", "MSFT": "MSFT", "META": "META",
              "EMAAR.DU": "EMAAR.DU", "2222.SR": "2222.SR", "GLD": "GLD"}.get(sym, sym)
        symbols.append(yh)
        weights.append(p["weight_pct"] / 100.0)

    if not symbols:
        return {"beta": None, "vol_30d_annualised": None, "sharpe_1y": None,
                "max_drawdown_1y": None, "correlation": {"symbols": [], "matrix": []}}

    # Per-symbol metrics
    per_symbol = {}
    for s in symbols:
        per_symbol[s] = {
            "beta": beta(s),
            "vol_30d_annualised": volatility_annualised(s, days=30),
            "max_drawdown_1y": max_drawdown(s, days=365),
            "sharpe_1y": sharpe(s, days=365),
        }

    syms, ret_matrix = _aligned_returns(symbols, days=365)
    portfolio = {}
    if ret_matrix.size:
        w = np.array([weights[symbols.index(s)] for s in syms])
        # Rescale weights so they sum to 1 over the equity sleeve we measured.
        if w.sum() > 0:
            w = w / w.sum()
        port_ret = w @ ret_matrix  # daily portfolio returns
        port_vol = float(port_ret.std(ddof=1) * math.sqrt(TRADING_DAYS) * 100)
        port_mean = float(port_ret.mean() * TRADING_DAYS * 100)
        rf = macro_svc.risk_free_rate_1y() * 100
        port_sharpe = ((port_mean - rf) / port_vol) if port_vol else None
        # Drawdown of cumulative product
        eq_curve = np.exp(np.cumsum(port_ret))
        peaks = np.maximum.accumulate(eq_curve)
        dd = ((eq_curve - peaks) / peaks).min() * 100
        # Beta vs S&P
        bench_closes = prices_svc.get_benchmark_closes("^GSPC", days=365)
        bench_ret = np.diff(np.log(np.array(bench_closes[-port_ret.size - 1:], dtype=float)))
        n = min(len(bench_ret), len(port_ret))
        if n > 30:
            cov = np.cov(port_ret[-n:], bench_ret[-n:], ddof=0)
            port_beta = cov[0, 1] / cov[1, 1] if cov[1, 1] else None
        else:
            port_beta = None
        portfolio = {
            "beta": float(round(port_beta, 3)) if port_beta is not None else None,
            "vol_annualised_pct": round(port_vol, 2),
            "expected_return_annualised_pct": round(port_mean, 2),
            "sharpe_1y": round(port_sharpe, 3) if port_sharpe is not None else None,
            "max_drawdown_1y_pct": round(dd, 2),
        }
    else:
        portfolio = {}

    return {
        "portfolio": portfolio,
        "per_symbol": per_symbol,
        "correlation": correlation_matrix(symbols),
    }
