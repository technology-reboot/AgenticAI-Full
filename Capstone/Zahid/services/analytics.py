from dataclasses import dataclass

from advisory_agent.models import AssetClass, Portfolio


@dataclass(frozen=True)
class PortfolioAnalytics:
    total_value: float
    allocation: dict[AssetClass, float]
    largest_holding: str
    concentration: float
    cash_value: float


def analyze_portfolio(portfolio: Portfolio) -> PortfolioAnalytics:
    if portfolio.total_value <= 0:
        raise ValueError("portfolio must contain a positive total value")
    largest = max(portfolio.holdings, key=lambda holding: holding.value)
    return PortfolioAnalytics(
        total_value=round(portfolio.total_value, 2),
        allocation=portfolio.allocation(),
        largest_holding=largest.symbol,
        concentration=round(largest.value / portfolio.total_value, 4),
        cash_value=round(sum(
            holding.value for holding in portfolio.holdings
            if holding.asset_class == AssetClass.CASH
        ), 2),
    )