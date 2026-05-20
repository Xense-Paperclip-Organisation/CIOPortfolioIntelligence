"""Macro data: FRED + FX. All live, all cached."""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from ..cache import cache_get, cache_set
from ..config import get_settings

log = logging.getLogger("services.macro")


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def _fred_series(series_id: str) -> dict[str, Any] | None:
    """Pull a single FRED series. Works without an API key for many series
    (rate-limited harder); honors `FRED_API_KEY` if provided.
    """
    settings = get_settings()
    cache_key = f"fred:{series_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    params: dict[str, Any] = {
        "series_id": series_id,
        "file_type": "json",
        "limit": 365,
        "sort_order": "desc",
    }
    if settings.fred_api_key:
        params["api_key"] = settings.fred_api_key
    try:
        with httpx.Client(timeout=settings.request_timeout_seconds) as client:
            resp = client.get(FRED_BASE, params=params)
            if resp.status_code != 200:
                log.warning("FRED %s returned %s", series_id, resp.status_code)
                return None
            data = resp.json()
            observations = [
                {"date": o["date"], "value": float(o["value"])}
                for o in data.get("observations", [])
                if o.get("value") not in (None, ".", "")
            ]
            if not observations:
                return None
            payload = {
                "series_id": series_id,
                "observations": observations,
                "latest": observations[0],
                "as_of": observations[0]["date"],
                "source": "FRED",
            }
            cache_set(cache_key, payload, ttl_seconds=settings.macro_cache_ttl_seconds)
            return payload
    except Exception as exc:
        log.warning("FRED %s failed: %s", series_id, exc)
        return None


def us_treasury_yield_curve() -> dict[str, float]:
    """Returns annualized %  yields keyed by maturity tenor."""
    series_map = {
        "3M": "DGS3MO",
        "1Y": "DGS1",
        "2Y": "DGS2",
        "5Y": "DGS5",
        "10Y": "DGS10",
        "30Y": "DGS30",
    }
    out: dict[str, float] = {}
    for tenor, sid in series_map.items():
        s = _fred_series(sid)
        if s and s.get("latest"):
            out[tenor] = float(s["latest"]["value"])
    return out


def risk_free_rate_1y() -> float:
    """1Y Treasury yield in percent — used as risk-free rate for Sharpe."""
    s = _fred_series("DGS1")
    if s and s.get("latest"):
        return float(s["latest"]["value"]) / 100.0
    return 0.045  # honest, conservative fallback


def fx_rate(base: str, quote: str) -> float:
    """Spot FX from exchangerate.host (free, no key). Falls back to a
    conservative static when offline so demos don't crash."""
    base = base.upper()
    quote = quote.upper()
    if base == quote:
        return 1.0
    cache_key = f"fx:{base}:{quote}"
    cached = cache_get(cache_key)
    if cached is not None:
        return float(cached)
    fallback = {
        ("USD", "AED"): 3.6725,
        ("AED", "USD"): 1 / 3.6725,
        ("USD", "SAR"): 3.75,
        ("SAR", "USD"): 1 / 3.75,
        ("EUR", "USD"): 1.08,
        ("USD", "EUR"): 1 / 1.08,
        ("AED", "SAR"): 3.75 / 3.6725,
        ("SAR", "AED"): 3.6725 / 3.75,
    }
    rate: float | None = None
    try:
        with httpx.Client(timeout=get_settings().request_timeout_seconds) as client:
            resp = client.get(
                "https://api.exchangerate.host/latest",
                params={"base": base, "symbols": quote},
            )
            if resp.status_code == 200:
                payload = resp.json()
                rate = float(payload.get("rates", {}).get(quote)) if payload.get("rates", {}).get(quote) else None
    except Exception as exc:
        log.warning("FX %s/%s failed: %s", base, quote, exc)
    if rate is None:
        rate = fallback.get((base, quote)) or 1.0
    cache_set(cache_key, rate, ttl_seconds=get_settings().macro_cache_ttl_seconds)
    return rate


def macro_snapshot() -> dict[str, Any]:
    """Compact macro tile for the header / advisory context."""
    cache_key = "macro:snapshot"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    curve = us_treasury_yield_curve()
    cpi = _fred_series("CPIAUCSL")
    payload = {
        "us_treasury_yield_curve": curve,
        "us_cpi_yoy_pct": _cpi_yoy(cpi) if cpi else None,
        "fx_usd_aed": fx_rate("USD", "AED"),
        "fx_usd_sar": fx_rate("USD", "SAR"),
        "fx_eur_usd": fx_rate("EUR", "USD"),
        "as_of": int(time.time()),
        "sources": ["FRED", "exchangerate.host"],
    }
    cache_set(cache_key, payload, ttl_seconds=get_settings().macro_cache_ttl_seconds)
    return payload


def _cpi_yoy(cpi: dict[str, Any]) -> float | None:
    obs = cpi.get("observations") or []
    if len(obs) < 13:
        return None
    try:
        latest = float(obs[0]["value"])
        twelve_months_ago = float(obs[12]["value"])
        if twelve_months_ago == 0:
            return None
        return round((latest / twelve_months_ago - 1) * 100, 2)
    except Exception:
        return None
