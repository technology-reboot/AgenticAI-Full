import os

from advisory_agent.models import Portfolio
from services.market import MarketSnapshot, fetch_prices


class DataAgent:
    """Normalizes portfolio inputs and optionally enriches holdings with prices."""

    def enrich(self, portfolio: Portfolio) -> tuple[MarketSnapshot, ...]:
        if os.getenv("ENABLE_LIVE_MARKET_DATA", "0") != "1":
            return tuple(MarketSnapshot(holding.symbol, None, "yfinance", "disabled")
                         for holding in portfolio.holdings)
        return fetch_prices([holding.symbol for holding in portfolio.holdings])