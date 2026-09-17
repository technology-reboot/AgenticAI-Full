from typing import Any, Dict

from models import RiskResponse
from services.risk_service import RiskService


DISCLAIMER = (
    "This assessment is provided for educational and "
    "informational purposes only. It is based on user "
    "inputs, historical portfolio information and "
    "simplified risk rules. It is not investment, "
    "financial, legal or tax advice. Historical results "
    "and simulated outcomes do not guarantee future "
    "performance. Consult a qualified financial adviser "
    "before making investment decisions."
)


class RiskAgent:
    def __init__(self) -> None:
        self.risk_service = RiskService()

    def evaluate(
        self,
        investor: Dict[str, Any],
        analysis_output: Dict[str, Any],
    ) -> RiskResponse:
        analytics = {
            "annualized_volatility": (
                analysis_output[
                    "annualized_volatility"
                ]
            ),
            "maximum_drawdown": (
                analysis_output[
                    "maximum_drawdown"
                ]
            ),
            "largest_holding_weight": (
                analysis_output[
                    "largest_holding_weight"
                ]
            ),
            "largest_sector_weight": (
                analysis_output[
                    "largest_sector_weight"
                ]
            ),
            "sector_allocation": (
                analysis_output.get(
                    "sector_allocation",
                    {},
                )
            ),
            "data_quality_warnings": (
                analysis_output.get(
                    "data_quality_warnings",
                    [],
                )
            ),
        }

        result = self.risk_service.assess(
            investor=investor,
            analytics=analytics,
        )

        result["summary"] = (
            f"The investor is classified as "
            f'{result["risk_profile"]} with a risk '
            f'score of {result["risk_score"]}. '
            f"The portfolio is classified as "
            f'{result["portfolio_risk_level"]}. '
            f"The portfolio is "
            f'{result["alignment_status"].lower()} '
            f"with the investor risk profile."
        )

        result["disclaimer"] = DISCLAIMER

        return RiskResponse(
            **result
        )