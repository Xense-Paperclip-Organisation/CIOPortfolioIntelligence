"""Abstract price provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PriceProvider(ABC):
    """All price providers must implement these three methods.

    Return shapes mirror the existing prices.py public API so callers need
    zero changes when the active provider is swapped.
    """

    @abstractmethod
    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Return latest quote dict or None on hard failure."""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        """Return list of OHLCV candle dicts (may be empty on failure)."""

    @abstractmethod
    def get_close_history(self, symbol: str, days: int = 365) -> list[float]:
        """Return last `days` daily closes (may be empty on failure)."""
