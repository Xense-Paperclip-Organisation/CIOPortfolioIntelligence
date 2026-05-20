"""Ahmed Al-Mansouri — the ONLY mocked element in the POC (BRD §3).

Every other figure in the dashboard — prices, news, FX, macro — is pulled live.
"""
from __future__ import annotations

from datetime import date
from typing import Any


# Balanced (Moderate Growth) target allocation used by the Alignment alert
# logic and the Allocation-vs-Target donut. Sourced from the BRD §3.2
# Balanced-profile guideposts.
BALANCED_TARGET = {
    "asset_class": {
        "Equity": 50.0,
        "Fixed Income": 30.0,
        "Cash": 5.0,
        "Commodity": 5.0,
        "Alternatives": 10.0,
    },
    "geography": {
        "USA": 30.0,
        "Europe": 15.0,
        "Japan": 5.0,
        "EM Asia": 10.0,
        "MENA": 25.0,
        "Global": 15.0,
    },
    "sector_cap_pct": 15.0,
    "single_name_cap_pct": 10.0,
    "currency": {
        "USD": 45.0,
        "AED": 35.0,
        "SAR": 10.0,
        "EUR": 10.0,
    },
    "target_beta": 0.9,
    "fixed_income_floor_pct": 25.0,
    "cash_ceiling_pct": 8.0,
}


# Ahmed's stated holdings — the only mocked figures in the entire POC.
# Prices are pulled live at request time; only the *positions* (qty/cost basis)
# are static so we have something to revalue.
HOLDINGS: list[dict[str, Any]] = [
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "asset_class": "Equity",
        "geography": "USA",
        "sector": "US Technology",
        "currency": "USD",
        "weight_target_pct": 18.0,
        "shares": 1_800,
        "cost_basis_per_share": 165.0,
        "yahoo_symbol": "AAPL",
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corp.",
        "asset_class": "Equity",
        "geography": "USA",
        "sector": "US Technology",
        "currency": "USD",
        "weight_target_pct": 16.0,
        "shares": 950,
        "cost_basis_per_share": 480.0,
        "yahoo_symbol": "NVDA",
    },
    {
        "ticker": "TSLA",
        "name": "Tesla Inc.",
        "asset_class": "Equity",
        "geography": "USA",
        "sector": "US Consumer Discretionary",
        "currency": "USD",
        "weight_target_pct": 12.0,
        "shares": 1_200,
        "cost_basis_per_share": 220.0,
        "yahoo_symbol": "TSLA",
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corp.",
        "asset_class": "Equity",
        "geography": "USA",
        "sector": "US Technology",
        "currency": "USD",
        "weight_target_pct": 10.0,
        "shares": 700,
        "cost_basis_per_share": 320.0,
        "yahoo_symbol": "MSFT",
    },
    {
        "ticker": "META",
        "name": "Meta Platforms",
        "asset_class": "Equity",
        "geography": "USA",
        "sector": "US Technology",
        "currency": "USD",
        "weight_target_pct": 6.0,
        "shares": 280,
        "cost_basis_per_share": 350.0,
        "yahoo_symbol": "META",
    },
    {
        "ticker": "EMAAR.DU",
        "name": "Emaar Properties",
        "asset_class": "Equity",
        "geography": "MENA",
        "sector": "UAE Real Estate",
        "currency": "AED",
        "weight_target_pct": 8.0,
        "shares": 25_000,
        "cost_basis_per_share": 7.5,
        "yahoo_symbol": "EMAAR.DU",
    },
    {
        "ticker": "2222.SR",
        "name": "Saudi Aramco",
        "asset_class": "Equity",
        "geography": "MENA",
        "sector": "Energy",
        "currency": "SAR",
        "weight_target_pct": 5.0,
        "shares": 6_500,
        "cost_basis_per_share": 30.0,
        "yahoo_symbol": "2222.SR",
    },
    {
        "ticker": "KSA-SUKUK-5.6-2030",
        "name": "Saudi Govt Sukuk 5.6% 2030",
        "asset_class": "Fixed Income",
        "geography": "MENA",
        "sector": "Sovereign",
        "currency": "SAR",
        "weight_target_pct": 7.0,
        "face_value_usd": 224_000.0,
        "coupon_pct": 5.6,
        "maturity": "2030-04-15",
        "duration_years": 5.2,
        # Synthesized from FRED yield curve + duration (BRD risk register).
        "yahoo_symbol": None,
    },
    {
        "ticker": "GLD",
        "name": "SPDR Gold Shares",
        "asset_class": "Commodity",
        "geography": "Global",
        "sector": "Gold",
        "currency": "USD",
        "weight_target_pct": 3.0,
        "shares": 350,
        "cost_basis_per_share": 195.0,
        "yahoo_symbol": "GLD",
    },
    {
        "ticker": "CASH",
        "name": "Cash (USD/AED)",
        "asset_class": "Cash",
        "geography": "UAE",
        "sector": "Cash",
        "currency": "USD",
        "weight_target_pct": 15.0,
        "balance_usd": 480_000.0,
        "yahoo_symbol": None,
    },
]


def get_profile() -> dict[str, Any]:
    return {
        "id": "ahmed-al-mansouri",
        "name": "Ahmed Al-Mansouri",
        "age": 42,
        "city": "Dubai",
        "country": "UAE",
        "profession": "Senior engineering manager",
        "stated_risk_profile": "Balanced (Moderate Growth)",
        "stated_investment_goal": "Retirement at 60 + children's education in 8 years",
        "stated_time_horizon_years": [10, 15],
        "liability_currencies": ["AED", "USD"],
        "total_aum_aed_equivalent": 3_200_000,
        "last_reviewed": date.today().isoformat(),
        "balanced_target": BALANCED_TARGET,
        "holdings": HOLDINGS,
    }
