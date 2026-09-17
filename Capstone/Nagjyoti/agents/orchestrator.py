from typing import Any, Dict
from agents.analysis_agent import PortfolioAnalysisAgent
from agents.risk_agent import RiskAgent
from agents.advisory_agent import AdvisoryAgent
from agents.qa_agent import QAAgent
from models import AnalysisRequest


class PortfolioOrchestrator:
    def __init__(self) -> None:

        self.analysis_agent = (PortfolioAnalysisAgent())

        self.risk_agent = (RiskAgent())

        self.advisory_agent = (AdvisoryAgent(use_llm=True))
        self.qa_agent = (QAAgent(use_llm=True))

    def run(self, request: AnalysisRequest) -> Dict[str, Any]:
        analysis_response = (self.analysis_agent.evaluate(request))

        analysis_output = (analysis_response.model_dump())

        investor = {
            "financial_goal":
                request.goal.name,

            "target_amount":
                request.goal.target_amount,

            "investment_horizon_years":
                request.goal.time_horizon_years,

            "risk_appetite":
                request.risk_responses.risk_appetite,

            "loss_tolerance_percent":
                request.risk_responses
                .loss_tolerance_percent,

            "income_stability":
                request.risk_responses
                .income_stability,

            "investment_experience":
                request.risk_responses
                .investment_experience,

            "liquidity_need":
                request.risk_responses
                .liquidity_need,
        }

        risk_response = (
            self.risk_agent.evaluate(
                investor=investor,
                analysis_output=
                analysis_output,
            )
        )

        risk_output = (risk_response.model_dump())

        advisory_result = (
            self.advisory_agent.evaluate(
                analysis_result=
                analysis_output,

                risk_result=
                risk_output,
            )
        )

        qa_result = (
            self.qa_agent.evaluate(
                analysis_result=
                analysis_output,

                risk_result=
                risk_output,

                advisory_result=
                advisory_result,
            )
        )

        return {

            "workflow_status":
                "completed",

            "analysis_result":
                analysis_output,

            "risk_result":
                risk_output,

            "advisory_result":
                advisory_result,

            "qa_result":
                qa_result,

            "disclaimer":
                risk_response.disclaimer,
        }