import re
from .ratios import RatioEngine

class RetrievalGroundingAgent:
    def __init__(self, store): self.store, self.engine = store, RatioEngine()

    def build_context(self, question: str, company: str, period: str) -> dict:
        records = self.store.all_metrics(company)
        current = [r for r in records if r.period == period]
        figures = [{"metric": r.metric, "value": r.value, "currency": r.currency, "unit": r.unit, "citation": r.citation} for r in current]
        ratios = self.engine.compute(current)
        notes = self.store.semantic_notes(question, company, period)
        return {"company": company, "period": period, "figures": figures, "ratios": ratios, "notes": notes}
