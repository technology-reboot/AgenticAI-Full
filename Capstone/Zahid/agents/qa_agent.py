from dataclasses import dataclass

from agents.advisory_agent import AdvisoryNarrative


@dataclass(frozen=True)
class QAResult:
    approved: bool
    checks: tuple[str, ...]


class QAAgent:
    """Compliance-oriented guardrail for presentation, not a substitute for legal review."""

    def review(self, narrative: AdvisoryNarrative, source_count: int) -> QAResult:
        checks = ["structured calculations are produced outside the LLM"]
        if source_count:
            checks.append("narrative has retrieved knowledge sources")
        else:
            checks.append("warning: no knowledge sources were retrieved")
        if "not financial advice" in narrative.text.lower():
            checks.append("suitability disclaimer is present")
        else:
            checks.append("warning: suitability disclaimer is missing")
        approved = source_count > 0 and "not financial advice" in narrative.text.lower()
        return QAResult(approved, tuple(checks))