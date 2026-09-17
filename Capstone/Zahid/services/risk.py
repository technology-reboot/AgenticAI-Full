from dataclasses import dataclass

from advisory_agent.models import AssetClass, Portfolio, RiskProfile


@dataclass(frozen=True)
class RiskAssessment:
    profile: RiskProfile
    score: int
    rationale: str
    equity_gap: float


def assess_risk(portfolio: Portfolio, profile: RiskProfile) -> RiskAssessment:
    equity_weight = portfolio.allocation()[AssetClass.EQUITIES]
    expected_equity_weight = {RiskProfile.CONSERVATIVE: 0.25, RiskProfile.MODERATE: 0.50, RiskProfile.AGGRESSIVE: 0.70}[profile]
    score = {RiskProfile.CONSERVATIVE: 35, RiskProfile.MODERATE: 60, RiskProfile.AGGRESSIVE: 85}[profile]
    return RiskAssessment(profile, score,
                          f"The declared {profile.value} profile targets approximately {expected_equity_weight:.0%} equities.",
                          round(expected_equity_weight - equity_weight, 4))