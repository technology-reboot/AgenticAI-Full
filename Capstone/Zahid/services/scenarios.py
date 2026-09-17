from dataclasses import dataclass

from advisory_agent.models import AssetClass, Portfolio


@dataclass(frozen=True)
class Scenario:
    name: str
    shocks: dict[AssetClass, float]
    description: str


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    description: str
    portfolio_change: float
    ending_value: float
    asset_changes: dict[AssetClass, float]


DEFAULT_SCENARIOS = (
    Scenario("market_downturn", {AssetClass.EQUITIES: -0.20, AssetClass.REAL_ASSETS: -0.10, AssetClass.BONDS: 0.02}, "Equities fall sharply while defensive assets provide limited offset."),
    Scenario("rate_hike", {AssetClass.BONDS: -0.08, AssetClass.EQUITIES: -0.05, AssetClass.CASH: 0.02}, "Higher rates pressure bonds and growth assets."),
    Scenario("inflation_spike", {AssetClass.BONDS: -0.04, AssetClass.CASH: -0.02, AssetClass.REAL_ASSETS: 0.08, AssetClass.EQUITIES: -0.03}, "Inflation reduces the real value of cash and fixed income."),
)


def run_scenario(portfolio: Portfolio, scenario: Scenario) -> ScenarioResult:
    changes = {
        asset_class: round(sum(
            holding.value * scenario.shocks.get(holding.asset_class, 0.0)
            for holding in portfolio.holdings
            if holding.asset_class == asset_class
        ), 2)
        for asset_class in AssetClass
    }
    change = round(sum(changes.values()), 2)
    return ScenarioResult(scenario.name, scenario.description, change,
                          round(portfolio.total_value + change, 2), changes)


def run_default_scenarios(portfolio: Portfolio) -> tuple[ScenarioResult, ...]:
    return tuple(run_scenario(portfolio, scenario) for scenario in DEFAULT_SCENARIOS)