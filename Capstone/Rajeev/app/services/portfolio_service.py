from pathlib import Path

from fastapi import HTTPException

from app.agents.portfolio_analysis_agent import DATA_FILE, PortfolioAnalysisAgent
from app.models import AgentRequest, AgentResponse


class PortfolioService:
    def __init__(self, data_file: Path | None = None):
        resolved_data_file = data_file or DATA_FILE
        self.agent = PortfolioAnalysisAgent(data_file=resolved_data_file)

    def evaluate(self, request: AgentRequest) -> AgentResponse:
        try:
            return self.agent.evaluate(request)
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - defensive safety
            raise HTTPException(status_code=500, detail=str(exc)) from exc
