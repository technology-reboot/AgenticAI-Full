import json, os, re
from openai import OpenAI

SYSTEM = """You are a cautious financial-statement analyst. Use ONLY the supplied grounded context.
Every financial figure must be immediately followed by its supplied citation. Ratios marked as COMPUTED may cite
[computed from cited source figures]. If evidence is missing, say: 'Not available in the uploaded statements.'
Do not provide investment advice. Clearly distinguish observations from interpretations."""

class NarrativeQAAgent:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def answer(self, question: str, context: dict) -> str:
        if not context["figures"] and not context["notes"]: return "Not available in the uploaded statements."
        if not os.getenv("OPENAI_API_KEY"): return self._fallback(question, context)
        response = OpenAI().responses.create(model=self.model, instructions=SYSTEM,
            input=f"QUESTION:\n{question}\n\nGROUNDED CONTEXT:\n{json.dumps(context, indent=2)}")
        text = response.output_text.strip()
        if self._has_uncited_numbers(text):
            return "Answer withheld because the generated response contained a figure without a citation. Please ask for a specific metric."
        return text

    @staticmethod
    def _has_uncited_numbers(text: str) -> bool:
        for line in text.splitlines():
            if re.search(r"(?<![A-Za-z])\d+(?:\.\d+)?%?", line) and "[" not in line:
                return True
        return False

    def _fallback(self, question, context):
        q = question.lower()
        matched = [f for f in context["figures"] if f["metric"].replace("_", " ") in q or any(w in q for w in f["metric"].split("_"))]
        if matched:
            return "\n".join(f"- {f['metric'].replace('_',' ').title()}: {f['value']:,.2f} {f['currency']} {f['unit']} {f['citation']}" for f in matched[:8])
        ratios = context["ratios"]
        if ratios:
            return "Computed ratios:\n" + "\n".join(f"- {k.replace('_',' ').title()}: {v:.2f} [computed from cited source figures]" for k,v in ratios.items())
        return "Not available in the uploaded statements."
