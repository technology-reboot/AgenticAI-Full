import json

from services.llm_service import LLMService


class AdvisoryAgent:

    def __init__(
        self,
        use_llm=True,
    ):

        self.use_llm = use_llm

        self.llm = (
            LLMService()
            if use_llm
            else None
        )

    def evaluate(
        self,
        analysis_result,
        risk_result,
    ):

        if not self.use_llm:

            return {
                "recommendations": [
                    "Increase diversification.",
                    "Reduce concentration risk."
                ],

                "rebalancing_actions": [
                    "Review sector allocation."
                ]
            }

        prompt = f"""
Portfolio Analysis:
{json.dumps(analysis_result, indent=2)}

Risk Assessment:
{json.dumps(risk_result, indent=2)}

Provide:
1. Key portfolio observations.
2. Diversification suggestions.
3. Rebalancing suggestions.
4. Goal alignment recommendations.

Do not guarantee future returns.
Do not provide regulated financial advice.
Return concise recommendations.
""".strip()

        response = (
            self.llm.generate(
                prompt
            )
        )

        return {
            "recommendations": response
        }