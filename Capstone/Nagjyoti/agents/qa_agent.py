import json

from services.llm_service import LLMService


class QAAgent:

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
        advisory_result,
    ):

        if not self.use_llm:

            return {
                "status": "Approved",

                "comments": []
            }

        prompt = f"""
        Review the response.

        Analysis:

        {json.dumps(analysis_result)}

        Risk:

        {json.dumps(risk_result)}

        Advice:

        {json.dumps(advisory_result)}

        Check:

        - suitability

        - unsupported claims

        - missing disclaimer

        Return:
        Approved or Revision Required
        """

        review = self.llm.generate(
            prompt
        )

        status = (
            "Approved"
            if "approved"
            in review.lower()
            else "Revision Required"
        )

        return {
            "status": status,
            "review": review
        }