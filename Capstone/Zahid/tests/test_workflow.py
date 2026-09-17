from advisory_agent.models import AssetClass, Holding, Portfolio, RiskProfile
from agents.orchestrator import PortfolioAdvisorOrchestrator
from reports.report import to_markdown


def test_orchestrator_runs_offline_with_scenarios_and_qa() -> None:
    portfolio = Portfolio((
        Holding("EQ", AssetClass.EQUITIES, 7000),
        Holding("BD", AssetClass.BONDS, 3000),
    ))

    workflow = PortfolioAdvisorOrchestrator().run(portfolio, RiskProfile.MODERATE)

    assert len(workflow.scenarios) == 3
    assert workflow.narrative.model in {"offline", "openai"}
    assert workflow.qa.approved is True
    assert "Stress scenarios" in to_markdown(workflow)