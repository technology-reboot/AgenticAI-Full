from dataclasses import dataclass
from enum import Enum


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class AssetClass(str, Enum):
    CASH = "cash"
    BONDS = "bonds"
    EQUITIES = "equities"
    REAL_ASSETS = "real_assets"


@dataclass(frozen=True)
class Holding:
    symbol: str
    asset_class: AssetClass
    value: float


@dataclass(frozen=True)
class Portfolio:
    holdings: tuple[Holding, ...]

    @property
    def total_value(self) -> float:
        return sum(holding.value for holding in self.holdings)

    def allocation(self) -> dict[AssetClass, float]:
        total = self.total_value
        if total <= 0:
            return {asset_class: 0.0 for asset_class in AssetClass}
        amounts = {asset_class: 0.0 for asset_class in AssetClass}
        for holding in self.holdings:
            amounts[holding.asset_class] += holding.value
        return {asset_class: amount / total for asset_class, amount in amounts.items()}


@dataclass(frozen=True)
class SimulationRequest:
    monthly_contribution: float = 0.0
    years: int = 1
    annual_return: float = 0.05

    def __post_init__(self) -> None:
        if self.monthly_contribution < 0:
            raise ValueError("monthly_contribution cannot be negative")
        if self.years < 1:
            raise ValueError("years must be at least 1")
        if self.annual_return <= -1:
            raise ValueError("annual_return must be greater than -100%")
