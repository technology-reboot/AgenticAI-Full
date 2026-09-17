from dataclasses import dataclass
from pathlib import Path

from .knowledge import KnowledgeRetriever, RetrievedChunk
from .models import AssetClass, Portfolio, RiskProfile, SimulationRequest


TARGET_ALLOCATIONS: dict[RiskProfile, dict[AssetClass, float]] = {
    RiskProfile.CONSERVATIVE: {
        AssetClass.CASH: 0.10, AssetClass.BONDS: 0.55,
        AssetClass.EQUITIES: 0.25, AssetClass.REAL_ASSETS: 0.10,
    },
    RiskProfile.MODERATE: {
        AssetClass.CASH: 0.05, AssetClass.BONDS: 0.35,
        AssetClass.EQUITIES: 0.50, AssetClass.REAL_ASSETS: 0.10,
    },
    RiskProfile.AGGRESSIVE: {
        AssetClass.CASH: 0.03, AssetClass.BONDS: 0.17,
        AssetClass.EQUITIES: 0.70, AssetClass.REAL_ASSETS: 0.10,
    },
}


@dataclass(frozen=True)
class Recommendation:
    asset_class: AssetClass
    action: str
    amount: float
    reason: str


@dataclass(frozen=True)
class AdvisoryReport:
    risk_profile: RiskProfile
    total_value: float
    current_allocation: dict[AssetClass, float]
    target_allocation: dict[AssetClass, float]
    recommendations: tuple[Recommendation, ...]
    simulation: dict[str, float]
    sources: tuple[RetrievedChunk, ...]


class AdvisoryAgent:
    """Produces explainable, risk-profile-aware portfolio guidance."""

    def __init__(self, knowledge_dir: Path | None = None):
        default_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge"
        self.retriever = KnowledgeRetriever(knowledge_dir or default_dir)

    def advise(
        self,
        portfolio: Portfolio,
        risk_profile: RiskProfile,
        simulation_request: SimulationRequest | None = None,
    ) -> AdvisoryReport:
        if portfolio.total_value <= 0:
            raise ValueError("portfolio must contain a positive total value")
        target = TARGET_ALLOCATIONS[risk_profile]
        current = portfolio.allocation()
        recommendations = []
        for asset_class in AssetClass:
            difference = target[asset_class] - current[asset_class]
            amount = round(abs(difference) * portfolio.total_value, 2)
            if amount < 1:
                continue
            action = "increase" if difference > 0 else "decrease"
            recommendations.append(Recommendation(
                asset_class, action, amount,
                f"Move allocation toward the {risk_profile.value} target of {target[asset_class]:.0%}.",
            ))
        query = f"{risk_profile.value} diversification rebalancing contributions portfolio"
        sources = tuple(self.retriever.search(query))
        request = simulation_request or SimulationRequest()
        simulation = self._simulate(portfolio.total_value, request)
        return AdvisoryReport(risk_profile, portfolio.total_value, current, target,
                              tuple(recommendations), simulation, sources)

    @staticmethod
    def _simulate(initial_value: float, request: SimulationRequest) -> dict[str, float]:
        monthly_rate = (1 + request.annual_return) ** (1 / 12) - 1
        balance = initial_value
        for _ in range(request.years * 12):
            balance = balance * (1 + monthly_rate) + request.monthly_contribution
        contributions = request.monthly_contribution * request.years * 12
        return {
            "initial_value": round(initial_value, 2),
            "contributions": round(contributions, 2),
            "projected_value": round(balance, 2),
            "projected_growth": round(balance - initial_value - contributions, 2),
        }
