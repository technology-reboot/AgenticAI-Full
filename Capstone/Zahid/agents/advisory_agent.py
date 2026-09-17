from dataclasses import dataclass

from advisory_agent.advisor import AdvisoryAgent as DeterministicAdvisor
from advisory_agent.models import Portfolio, RiskProfile, SimulationRequest
from services.llm import create_advisory_llm
from services.risk import RiskAssessment


@dataclass(frozen=True)
class AdvisoryNarrative:
    text: str
    model: str


class AdvisoryAgent:
    """Combines deterministic recommendations with optional grounded LLM narration."""

    def __init__(self) -> None:
        self.calculator = DeterministicAdvisor()
        self.llm = create_advisory_llm()

    def generate(self, portfolio: Portfolio, profile: RiskProfile,
                 simulation: SimulationRequest, risk: RiskAssessment):
        report = self.calculator.advise(portfolio, profile, simulation)
        if self.llm is None:
            return report, AdvisoryNarrative(
                "OpenAI is not configured. The structured recommendations and scenarios remain available. "
                "This is not financial advice.",
                "offline",
            )
        from langchain_core.messages import HumanMessage, SystemMessage

        sources = "\n".join(f"[{item.source}] {item.text}" for item in report.sources)
        prompt = (
            "Produce a concise portfolio advisory narrative from the structured facts below. "
            "Do not invent prices, returns, tax advice, or securities. Explain trade-offs, "
            "mention the scenario risks, cite sources by filename, and state that this is not financial advice.\n\n"
            f"Risk assessment: {risk}\nRecommendations: {report.recommendations}\n"
            f"What-if projection: {report.simulation}\nSources:\n{sources}"
        )
        response = self.llm.invoke([
            SystemMessage(content="You are a cautious, explainable portfolio advisory writer."),
            HumanMessage(content=prompt),
        ])
        return report, AdvisoryNarrative(str(response.content), "openai")