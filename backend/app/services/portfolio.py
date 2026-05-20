"""Portfolio revaluation, allocation gap, alignment alerts."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .. import profile as profile_mod
from . import prices as prices_svc
from . import macro as macro_svc


USD = "USD"


def _convert_to_usd(amount: float, currency: str) -> float:
    if currency.upper() == USD:
        return amount
    rate = macro_svc.fx_rate(currency, USD)
    return amount * rate


def revalue_holdings() -> dict[str, Any]:
    """Live-price every holding and return positions + portfolio totals (USD)."""
    profile = profile_mod.get_profile()
    holdings = profile["holdings"]
    treasury = macro_svc.us_treasury_yield_curve()
    sukuk_yield = treasury.get("5Y") or 4.5

    positions: list[dict[str, Any]] = []
    total_value_usd = 0.0
    total_day_pnl_usd = 0.0

    for h in holdings:
        ticker = h["ticker"]
        asset_class = h["asset_class"]
        currency = h.get("currency", USD)
        if asset_class == "Cash":
            value_native = float(h.get("balance_usd", 0.0))
            value_usd = value_native
            position = {
                "ticker": ticker,
                "name": h["name"],
                "asset_class": asset_class,
                "geography": h.get("geography"),
                "sector": h.get("sector"),
                "currency": currency,
                "quote": {
                    "price": 1.0,
                    "previous_close": 1.0,
                    "day_change_pct": 0.0,
                    "week_change_pct": 0.0,
                    "source": "cash",
                    "synthesized": False,
                },
                "value_usd": value_usd,
                "value_native": value_native,
                "day_pnl_usd": 0.0,
                "quantity": value_native,
            }
        elif asset_class == "Fixed Income":
            est = prices_svc.sukuk_price_estimate(
                coupon_pct=h.get("coupon_pct", 5.0),
                maturity_iso=h.get("maturity", "2030-01-01"),
                duration_years=h.get("duration_years", 5.0),
                current_yield_pct=sukuk_yield,
            )
            face_value_usd = float(h.get("face_value_usd", 0.0))
            value_usd = face_value_usd * est["price"] / 100.0
            position = {
                "ticker": ticker,
                "name": h["name"],
                "asset_class": asset_class,
                "geography": h.get("geography"),
                "sector": h.get("sector"),
                "currency": currency,
                "quote": {
                    "price": est["price"],
                    "previous_close": est["price"],
                    "day_change_pct": 0.0,
                    "week_change_pct": 0.0,
                    "source": est["source"],
                    "synthesized": True,
                    "yield_pct": est["yield_pct"],
                    "duration_years": est["duration_years"],
                },
                "value_usd": value_usd,
                "value_native": value_usd,
                "day_pnl_usd": 0.0,
                "quantity": face_value_usd,
            }
        else:
            quote = prices_svc.get_quote(h["yahoo_symbol"]) or {}
            shares = float(h.get("shares", 0))
            price_native = float(quote.get("price") or 0.0)
            value_native = shares * price_native
            value_usd = _convert_to_usd(value_native, currency)
            prev_native = float(quote.get("previous_close") or price_native)
            day_pnl_native = shares * (price_native - prev_native)
            day_pnl_usd = _convert_to_usd(day_pnl_native, currency)
            cost_native = shares * float(h.get("cost_basis_per_share", 0))
            unrealized_native = value_native - cost_native
            position = {
                "ticker": ticker,
                "name": h["name"],
                "asset_class": asset_class,
                "geography": h.get("geography"),
                "sector": h.get("sector"),
                "currency": currency,
                "quote": quote,
                "shares": shares,
                "cost_basis_per_share": h.get("cost_basis_per_share"),
                "value_usd": value_usd,
                "value_native": value_native,
                "day_pnl_usd": day_pnl_usd,
                "unrealized_pnl_native": unrealized_native,
                "quantity": shares,
            }
        total_value_usd += position["value_usd"]
        total_day_pnl_usd += position["day_pnl_usd"]
        positions.append(position)

    # Now compute weights
    for p in positions:
        p["weight_pct"] = (p["value_usd"] / total_value_usd * 100.0) if total_value_usd else 0.0

    fx_aed = macro_svc.fx_rate(USD, "AED")
    return {
        "positions": positions,
        "total_value_usd": total_value_usd,
        "total_value_aed": total_value_usd * fx_aed,
        "day_pnl_usd": total_day_pnl_usd,
        "day_pnl_pct": (total_day_pnl_usd / (total_value_usd - total_day_pnl_usd) * 100.0)
        if (total_value_usd - total_day_pnl_usd) else 0.0,
        "fx_usd_aed": fx_aed,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def allocation_breakdown(positions: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(p["value_usd"] for p in positions) or 1.0

    def bucket(key: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for p in positions:
            k = p.get(key) or "Other"
            out[k] = out.get(k, 0.0) + p["value_usd"]
        return {k: round(v / total * 100, 2) for k, v in out.items()}

    by_asset = bucket("asset_class")
    by_geo = bucket("geography")
    by_sector = bucket("sector")
    by_currency = bucket("currency")
    return {
        "asset_class": by_asset,
        "geography": by_geo,
        "sector": by_sector,
        "currency": by_currency,
    }


def alignment_alerts(positions: list[dict[str, Any]],
                     allocation: dict[str, Any],
                     target: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    equity_pct = allocation["asset_class"].get("Equity", 0)
    target_equity = target["asset_class"].get("Equity", 50.0)
    if equity_pct - target_equity > 10:
        alerts.append({
            "severity": "high",
            "category": "asset-class",
            "headline": f"Equity exposure {equity_pct:.0f}% vs Balanced target {target_equity:.0f}%",
            "body": ("Your portfolio is over-weight equity relative to your stated Balanced "
                     f"profile. Rebalancing roughly {equity_pct - target_equity:.0f} percentage points "
                     "into fixed income would bring you closer to the model."),
            "metric": {"current_pct": equity_pct, "target_pct": target_equity, "gap_pct": equity_pct - target_equity},
        })

    fi_pct = allocation["asset_class"].get("Fixed Income", 0)
    if fi_pct < target.get("fixed_income_floor_pct", 25):
        alerts.append({
            "severity": "high",
            "category": "asset-class",
            "headline": f"Fixed income at {fi_pct:.0f}% — below {target.get('fixed_income_floor_pct')}% floor",
            "body": "Your defensive sleeve is thin for a Balanced profile, particularly with an 8-year "
                    "education-funding milestone approaching. Consider adding investment-grade GCC sukuk and "
                    "short-duration USD treasury exposure.",
            "metric": {"current_pct": fi_pct, "target_pct": target.get("fixed_income_floor_pct")},
        })

    cash_pct = allocation["asset_class"].get("Cash", 0)
    if cash_pct > target.get("cash_ceiling_pct", 8):
        alerts.append({
            "severity": "medium",
            "category": "cash-drag",
            "headline": f"Cash at {cash_pct:.0f}% — material drag on returns",
            "body": ("Cash earning sub-inflation returns. Suggest deploying excess cash into your "
                     "under-weight fixed-income sleeve in tranches over the next 3 months."),
            "metric": {"current_pct": cash_pct, "target_pct": target.get("cash_ceiling_pct")},
        })

    usa_pct = allocation["geography"].get("USA", 0)
    target_usa = target["geography"].get("USA", 30)
    if usa_pct - target_usa > 15:
        alerts.append({
            "severity": "high",
            "category": "geography",
            "headline": f"USA geographic skew {usa_pct:.0f}% vs target {target_usa:.0f}%",
            "body": ("Heavy US tilt amplifies USD beta and concentrates currency risk. Adding "
                     "European (e.g., VGK), Japan and EM-Asia equity sleeves would re-balance geography."),
            "metric": {"current_pct": usa_pct, "target_pct": target_usa},
        })

    sector_cap = target.get("sector_cap_pct", 15)
    for sector_name, weight in allocation["sector"].items():
        if weight > sector_cap and sector_name.lower() != "cash":
            alerts.append({
                "severity": "high",
                "category": "sector",
                "headline": f"{sector_name} sector at {weight:.0f}% — over {sector_cap}% prudent cap",
                "body": f"Concentration in {sector_name} elevates idiosyncratic risk. Trim and "
                        "diversify into adjacent or counter-cyclical sectors.",
                "metric": {"current_pct": weight, "target_pct": sector_cap},
            })

    # Single-name + correlated cluster alert (AAPL + NVDA + TSLA tech cluster)
    cap = target.get("single_name_cap_pct", 10)
    over_cap_names = [p for p in positions if p["weight_pct"] > cap and p["asset_class"] == "Equity"]
    if over_cap_names:
        names_list = ", ".join(p["ticker"] for p in over_cap_names)
        alerts.append({
            "severity": "high",
            "category": "single-name",
            "headline": f"Single-name positions exceed {cap}% cap: {names_list}",
            "body": "Single-position concentration above a 10% cap creates outsized idiosyncratic risk. "
                    "Trim the largest positions and redeploy into diversified ETFs.",
            "metric": {"names": [p["ticker"] for p in over_cap_names], "cap_pct": cap},
        })

    # Tech cluster check
    tech_names = {"AAPL", "NVDA", "TSLA", "MSFT", "META"}
    tech_weight = sum(p["weight_pct"] for p in positions if p["ticker"] in tech_names)
    if tech_weight > 25:
        alerts.append({
            "severity": "high",
            "category": "correlation",
            "headline": f"US-tech cluster (AAPL/NVDA/TSLA/MSFT/META) = {tech_weight:.0f}% of book",
            "body": ("These names share macro drivers (US rates, AI capex, mega-cap sentiment) — "
                     "treating them as independent positions understates true concentration risk."),
            "metric": {"cluster_weight_pct": tech_weight},
        })

    # Currency mismatch
    usd_pct = allocation["currency"].get("USD", 0)
    if usd_pct > target["currency"].get("USD", 45) + 20:
        alerts.append({
            "severity": "medium",
            "category": "currency",
            "headline": f"USD exposure {usd_pct:.0f}% vs target ~{target['currency'].get('USD',45):.0f}%",
            "body": ("USD over-weight is partly defensible because of an 8-year USD education liability, "
                     "but it leaves AED-denominated retirement liabilities under-hedged."),
            "metric": {"current_pct": usd_pct, "target_pct": target["currency"].get("USD", 45)},
        })
    return alerts


def portfolio_hash(positions: list[dict[str, Any]]) -> str:
    """Stable hash of (ticker, weight_pct) pairs — used as personalization
    cache key per BRD §8."""
    snapshot = sorted(
        ((p["ticker"], round(p["weight_pct"], 2)) for p in positions),
        key=lambda x: x[0],
    )
    return hashlib.sha1(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()[:16]
