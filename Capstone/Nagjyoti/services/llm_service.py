import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        self.model = os.getenv("OPENAI_MODEL","gpt-4o-mini",)

        self.client = (OpenAI(api_key=api_key)
            if api_key
            else None
        )

    def is_available(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str,) -> str:
        if not self.is_available():
            return "LLM unavailable."

        try:
            response = (
                self.client.responses.create(
                    model=self.model,
                    input=prompt,
                )
            )

            return (
                response.output_text.strip()
            )

        except Exception:
            return (
                "Unable to generate response."
            )

    def generate_risk_summary(self, risk_result: dict[str, Any]) -> str:

        default_summary = (
            f"The investor is classified as "
            f'{risk_result["risk_profile"]} with a '
            f'risk score of {risk_result["risk_score"]}. '
            f"The portfolio is "
            f'{risk_result["alignment_status"].lower()} '
            f"with this risk profile."
        )

        if not self.is_available():
            return default_summary

        prompt = f"""
You are the explanation component of a portfolio Risk Agent.

Use only the calculated information below.

Risk score:
{risk_result["risk_score"]}

Investor risk profile:
{risk_result["risk_profile"]}

Portfolio risk level:
{risk_result["portfolio_risk_level"]}

Alignment:
{risk_result["alignment_status"]}

Alignment reason:
{risk_result["alignment_reason"]}

Warnings:
{risk_result["warnings"]}

Instructions:

- Do not recalculate anything.
- Do not change the risk score.
- Do not change the risk profile.
- Do not suggest buying or selling.
- Do not guarantee returns.
- Use professional language.
- Maximum 100 words.
- Mention that this is educational.
"""

        try:

            response = (
                self.client.responses.create(
                    model=self.model,
                    input=prompt,
                )
            )

            return (
                response.output_text.strip()
            )

        except Exception:
            return default_summary
