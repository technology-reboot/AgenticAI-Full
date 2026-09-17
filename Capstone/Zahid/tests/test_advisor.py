from pathlib import Path

import pytest

from advisory_agent import AdvisoryAgent, AssetClass, Portfolio, RiskProfile, SimulationRequest
from advisory_agent.models import Holding


@pytest.fixture
def portfolio() -> Portfolio:
    return Portfolio((
        Holding("US_EQ", AssetClass.EQUITIES, 7000),
        Holding("BOND", AssetClass.BONDS, 3000),
    ))


def test_report_is_risk_aware_and_grounded(portfolio: Portfolio) -> None:
    report = AdvisoryAgent().advise(portfolio, RiskProfile.CONSERVATIVE)

    assert report.target_allocation[AssetClass.BONDS] == 0.55
    assert any(item.asset_class == AssetClass.EQUITIES and item.action == "decrease"
               for item in report.recommendations)
    assert report.sources
    assert all(source.source.endswith(".md") for source in report.sources)


def test_what_if_includes_contributions_and_growth(portfolio: Portfolio) -> None:
    simulation = AdvisoryAgent().advise(
        portfolio, RiskProfile.MODERATE, SimulationRequest(100, 2, 0.05)
    ).simulation

    assert simulation["initial_value"] == 10000
    assert simulation["contributions"] == 2400
    assert simulation["projected_value"] > 12400
    assert simulation["projected_growth"] > 0


def test_invalid_portfolio_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        AdvisoryAgent().advise(Portfolio(()), RiskProfile.MODERATE)
