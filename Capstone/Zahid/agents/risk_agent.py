from advisory_agent.models import Portfolio, RiskProfile
from services.risk import RiskAssessment, assess_risk


class RiskAgent:
    def assess(self, portfolio: Portfolio, profile: RiskProfile) -> RiskAssessment:
        return assess_risk(portfolio, profile)