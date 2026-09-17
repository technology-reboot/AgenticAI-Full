from dataclasses import dataclass

from advisory_agent.models import Portfolio, RiskProfile, SimulationRequest
from agents.advisory_agent import AdvisoryAgent, AdvisoryNarrative
from agents.data_agent import DataAgent
from agents.qa_agent import QAAgent, QAResult
from agents.risk_agent import RiskAgent
from services.analytics import PortfolioAnalytics, analyze_portfolio
from services.scenarios import ScenarioResult, run_default_scenarios
from services.risk import RiskAssessment


@dataclass(frozen=True)
class AdvisoryWorkflow:
    analytics: PortfolioAnalytics
    risk: RiskAssessment
    report: object
    scenarios: tuple[ScenarioResult, ...]
    narrative: AdvisoryNarrative
    qa: QAResult


class PortfolioAdvisorOrchestrator:
    def __init__(self) -> None:
        self.data_agent = DataAgent()
        self.risk_agent = RiskAgent()
        self.advisory_agent = AdvisoryAgent()
        self.qa_agent = QAAgent()

    def run(self, portfolio: Portfolio, profile: RiskProfile,
            simulation: SimulationRequest | None = None) -> AdvisoryWorkflow:
        analytics = analyze_portfolio(portfolio)
        self.data_agent.enrich(portfolio)
        risk = self.risk_agent.assess(portfolio, profile)
        report, narrative = self.advisory_agent.generate(
            portfolio, profile, simulation or SimulationRequest(), risk,
        )
        scenarios = run_default_scenarios(portfolio)
        qa = self.qa_agent.review(narrative, len(report.sources))
        return AdvisoryWorkflow(analytics, risk, report, scenarios, narrative, qa)