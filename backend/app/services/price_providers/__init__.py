"""Price provider factory — resolves the active and shadow providers from config."""
from __future__ import annotations

from ...config import get_settings
from .base import PriceProvider
from .yfinance_provider import YFinanceProvider
from .polygon_provider import PolygonProvider
from .alpha_vantage_provider import AlphaVantageProvider


def _make(name: str) -> PriceProvider | None:
    if not name:
        return None
    cfg = get_settings()
    mapping: dict[str, type[PriceProvider]] = {
        "yfinance": YFinanceProvider,
        "polygon": PolygonProvider,
        "alpha_vantage": AlphaVantageProvider,
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown PRICE_PROVIDER {name!r} — valid: {list(mapping)}")
    return cls(cfg)


def get_active_provider() -> PriceProvider:
    return _make(get_settings().price_provider) or YFinanceProvider(get_settings())


def get_shadow_provider() -> PriceProvider | None:
    return _make(get_settings().price_provider_shadow)


__all__ = [
    "PriceProvider",
    "YFinanceProvider",
    "PolygonProvider",
    "AlphaVantageProvider",
    "get_active_provider",
    "get_shadow_provider",
]
