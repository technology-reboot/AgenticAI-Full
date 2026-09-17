from models import (
    AnalysisRequest,
    AnalysisResponse,
)
from services.analysis_service import AnalysisService


class PortfolioAnalysisAgent:
    def __init__(self) -> None:
        self.analysis_service = AnalysisService()

    def evaluate(
        self,
        request: AnalysisRequest,
    ) -> AnalysisResponse:
        result = self.analysis_service.analyze(
            request
        )

        return AnalysisResponse(
            **result
        )