from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

OUT = Path(__file__).with_name("portfolio_advisor_capstone_demo.pptx")

NAVY = RGBColor(12, 24, 43)
INK = RGBColor(24, 36, 52)
SLATE = RGBColor(74, 91, 109)
MIST = RGBColor(239, 244, 247)
WHITE = RGBColor(255, 255, 255)
TEAL = RGBColor(23, 157, 151)
ORANGE = RGBColor(235, 132, 65)
GOLD = RGBColor(241, 190, 77)
RED = RGBColor(205, 76, 71)
BLUE = RGBColor(61, 126, 182)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def rect(slide, x, y, w, h, fill, radius=False, line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    if radius:
        shape.adjustments[0] = 0.08
    return shape


def text(slide, value, x, y, w, h, size=18, color=INK, bold=False,
         font="Aptos", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.04)
    frame.margin_right = Inches(0.04)
    frame.margin_top = Inches(0.02)
    frame.margin_bottom = Inches(0.02)
    frame.vertical_anchor = valign
    para = frame.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def rich_lines(slide, lines, x, y, w, h, size=17, color=INK, spacing=5):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.04)
    frame.margin_right = Inches(0.04)
    frame.margin_top = Inches(0.02)
    for index, line in enumerate(lines):
        para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        para.text = line
        para.font.name = "Aptos"
        para.font.size = Pt(size)
        para.font.color.rgb = color
        para.space_after = Pt(spacing)
    return box


def header(slide, title, kicker, number):
    rect(slide, 0, 0, 13.333, 7.5, WHITE)
    rect(slide, 0, 0, 0.18, 7.5, TEAL)
    text(slide, kicker.upper(), 0.62, 0.38, 5.8, 0.28, 10, TEAL, True)
    text(slide, title, 0.62, 0.76, 11.5, 0.58, 27, NAVY, True)
    text(slide, f"CAPSTONE PROJECT 1  /  {number:02d}", 11.0, 0.42, 1.7, 0.25, 9, SLATE, True, align=PP_ALIGN.RIGHT)
    rect(slide, 0.62, 1.52, 12.05, 0.015, MIST)


def footer(slide, cue):
    rect(slide, 0.62, 7.05, 12.05, 0.015, MIST)
    text(slide, cue, 0.64, 7.12, 11.8, 0.2, 8.5, SLATE)


def bullet_slide(title, kicker, items, cue, number, accent=TEAL):
    slide = prs.slides.add_slide(blank)
    header(slide, title, kicker, number)
    y = 1.95
    for item in items:
        rect(slide, 0.76, y + 0.08, 0.12, 0.12, accent, radius=True)
        text(slide, item, 1.05, y, 11.0, 0.45, 19, INK)
        y += 0.72
    footer(slide, cue)
    return slide


# 1
slide = prs.slides.add_slide(blank)
rect(slide, 0, 0, 13.333, 7.5, NAVY)
rect(slide, 0, 0, 0.2, 7.5, TEAL)
rect(slide, 8.6, 0, 4.733, 7.5, TEAL)
rect(slide, 9.25, 0.75, 2.95, 2.95, NAVY, radius=True)
text(slide, "PA", 9.62, 1.22, 2.2, 1.1, 50, WHITE, True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
text(slide, "PORTFOLIO\nADVISOR", 0.85, 1.2, 7.2, 1.35, 38, WHITE, True)
text(slide, "Personalized, scenario-tested investment guidance", 0.9, 2.9, 6.8, 0.5, 21, GOLD, False)
text(slide, "Capstone Project 1", 0.9, 4.25, 4.2, 0.4, 19, WHITE, True)
text(slide, "Presented by Syed Hussein", 0.9, 4.78, 4.2, 0.32, 15, RGBColor(202, 218, 226))
text(slide, "Explainable calculations  |  grounded narrative  |  QA guardrails", 0.9, 6.65, 7.3, 0.25, 11, RGBColor(202, 218, 226))

# 2
bullet_slide("The problem", "WHY THIS PROJECT", [
    "Investors need guidance that connects goals, risk tolerance, and current holdings.",
    "A portfolio can be concentrated even when its total value looks healthy.",
    "Recommendations should be explainable, scenario-tested, and clearly caveated.",
    "The system must separate reliable calculations from flexible language generation.",
], "Talk track: This is decision support, not automatic trading or a promise of future performance.", 2, ORANGE)

# 3
slide = prs.slides.add_slide(blank)
header(slide, "What the system delivers", "SOLUTION", 3)
labels = [("INPUT", "Holdings\nRisk profile\nContributions", BLUE), ("ANALYZE", "Allocation\nConcentration\nRisk gap", TEAL), ("ADVISE", "Rebalance\nProjection\nSources", ORANGE), ("CHECK", "Scenarios\nNarrative\nQA gate", GOLD)]
for i, (label, body, color) in enumerate(labels):
    x = 0.72 + i * 3.08
    rect(slide, x, 2.0, 2.45, 2.45, MIST, radius=True, line=color)
    rect(slide, x, 2.0, 2.45, 0.43, color, radius=True)
    text(slide, label, x + 0.18, 2.09, 2.05, 0.22, 12, WHITE, True, align=PP_ALIGN.CENTER)
    text(slide, body, x + 0.2, 2.78, 2.05, 1.2, 19, NAVY, True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    if i < 3:
        text(slide, ">", x + 2.57, 2.95, 0.4, 0.4, 24, SLATE, True, align=PP_ALIGN.CENTER)
footer(slide, "Talk track: One workflow produces analytics, recommendations, projections, stress tests, and a checked explanation.")

# 4
slide = prs.slides.add_slide(blank)
header(slide, "Architecture and orchestration", "HOW IT WORKS", 4)
flow = [("User / UI", BLUE), ("Data Agent", TEAL), ("Analysis + Risk", ORANGE), ("Advisory Agent", GOLD), ("QA Agent", RED)]
for i, (label, color) in enumerate(flow):
    x = 0.78 + i * 2.48
    rect(slide, x, 2.3, 1.92, 1.0, color, radius=True)
    text(slide, label, x + 0.12, 2.57, 1.68, 0.4, 16, WHITE, True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
    if i < len(flow) - 1:
        text(slide, ">", x + 2.04, 2.55, 0.35, 0.4, 22, SLATE, True, align=PP_ALIGN.CENTER)
rect(slide, 2.35, 4.2, 8.7, 1.1, MIST, radius=True)
text(slide, "PortfolioAdvisorOrchestrator.run()", 2.6, 4.45, 8.2, 0.3, 23, NAVY, True, align=PP_ALIGN.CENTER)
text(slide, "Coordinates analysis -> enrichment -> risk -> advice -> scenarios -> QA", 2.6, 4.9, 8.2, 0.25, 13, SLATE, align=PP_ALIGN.CENTER)
footer(slide, "Code anchor: agents/orchestrator.py. Each agent has one focused responsibility.")

# 5
slide = prs.slides.add_slide(blank)
header(slide, "Portfolio model and validation", "CODE WALKTHROUGH", 5)
code = """@dataclass(frozen=True)\nclass Holding:\n    symbol: str\n    asset_class: AssetClass\n    value: float\n\n@property\ndef total_value(self) -> float:\n    return sum(h.value for h in self.holdings)"""
rect(slide, 0.72, 1.95, 6.0, 3.8, NAVY, radius=True)
text(slide, code, 1.0, 2.25, 5.45, 3.2, 16, WHITE, font="Consolas")
text(slide, "Why this matters", 7.35, 2.08, 4.3, 0.35, 20, TEAL, True)
rich_lines(slide, ["Structured inputs", "Frozen dataclasses reduce accidental mutation.", "Enums restrict risk profiles and asset classes.", "Validation rejects empty or invalid simulation requests."], 7.35, 2.7, 4.75, 2.7, 17, INK, 12)
footer(slide, "Code anchor: advisory_agent/models.py. The model layer keeps the workflow explicit and testable.")

# 6
slide = prs.slides.add_slide(blank)
header(slide, "Risk profile targets", "CODE WALKTHROUGH", 6)
rect(slide, 0.72, 1.95, 5.65, 4.15, NAVY, radius=True)
text(slide, "RiskProfile.MODERATE: {\n    CASH: 0.05,\n    BONDS: 0.35,\n    EQUITIES: 0.50,\n    REAL_ASSETS: 0.10,\n}", 1.0, 2.3, 5.0, 2.6, 18, WHITE, font="Consolas")
text(slide, "Target allocation", 7.05, 1.98, 4.5, 0.35, 20, ORANGE, True)
alloc = [("Cash", 5, TEAL), ("Bonds", 35, BLUE), ("Equities", 50, ORANGE), ("Real assets", 10, GOLD)]
y = 2.72
for label, pct, color in alloc:
    text(slide, f"{label}  {pct}%", 7.05, y, 1.65, 0.25, 14, INK, True)
    rect(slide, 8.85, y + 0.04, 3.0, 0.22, MIST, radius=True)
    rect(slide, 8.85, y + 0.04, 3.0 * pct / 50, 0.22, color, radius=True)
    y += 0.62
footer(slide, "Talk track: These are reference targets for the selected profile, not personalized regulated advice.")

# 7
slide = prs.slides.add_slide(blank)
header(slide, "Dollar-based rebalancing", "CODE WALKTHROUGH", 7)
rect(slide, 0.72, 2.0, 5.8, 2.15, NAVY, radius=True)
text(slide, "difference = target - current\namount = abs(difference) * total_value\naction = increase or decrease", 1.0, 2.45, 5.25, 1.3, 19, WHITE, font="Consolas")
text(slide, "Example: $10,000 portfolio", 7.15, 2.0, 4.5, 0.35, 20, TEAL, True)
rich_lines(slide, ["Current equities: 70%", "Moderate target: 50%", "Gap: -20%", "Recommendation: decrease equities by $2,000"], 7.15, 2.7, 4.6, 2.2, 19, INK, 10)
rect(slide, 7.1, 5.25, 4.7, 0.62, MIST, radius=True)
text(slide, "No random recommendation: a transparent calculation.", 7.3, 5.43, 4.3, 0.22, 13, SLATE, True, align=PP_ALIGN.CENTER)
footer(slide, "Code anchor: advisory_agent/advisor.py. The LLM does not calculate this amount.")

# 8
slide = prs.slides.add_slide(blank)
header(slide, "What-if projection", "CODE WALKTHROUGH", 8)
rect(slide, 0.72, 1.95, 6.2, 3.8, NAVY, radius=True)
text(slide, "monthly_rate = (1 + annual_return) ** (1/12) - 1\n\nfor month in range(years * 12):\n    balance *= (1 + monthly_rate)\n    balance += monthly_contribution", 1.0, 2.25, 5.65, 2.8, 16, WHITE, font="Consolas")
text(slide, "Outputs", 7.45, 2.05, 3.7, 0.35, 20, ORANGE, True)
rich_lines(slide, ["Initial value", "Total contributions", "Projected value", "Projected growth"], 7.45, 2.72, 4.2, 2.2, 19, INK, 12)
text(slide, "Illustrative only: fixed return assumption; no fees, tax, inflation, withdrawals, or changing returns.", 7.45, 5.2, 4.55, 0.7, 13, RED, True)
footer(slide, "Code anchor: AdvisoryAgent._simulate(). This is a projection, not a forecast or guarantee.")

# 9
slide = prs.slides.add_slide(blank)
header(slide, "Local knowledge retrieval", "RAG LAYER", 9)
rect(slide, 0.72, 2.0, 5.95, 3.65, NAVY, radius=True)
text(slide, "query = f\"{profile} diversification\nrebalancing contributions portfolio\"\n\nsources = retriever.search(query)", 1.0, 2.4, 5.35, 2.15, 17, WHITE, font="Consolas")
text(slide, "Current approach", 7.25, 2.05, 4.4, 0.35, 20, TEAL, True)
rich_lines(slide, ["Loads Markdown sections from data/knowledge/", "Tokenizes query and document text", "Scores word overlap", "Returns top four source chunks", "Can later be replaced by embeddings/vector search"], 7.25, 2.75, 4.8, 2.8, 17, INK, 8)
footer(slide, "Code anchor: advisory_agent/knowledge.py. This is lightweight keyword-based RAG, not a vector database.")

# 10
slide = prs.slides.add_slide(blank)
header(slide, "LLM configuration", "OPENAI INTEGRATION", 10)
rect(slide, 0.72, 1.95, 6.0, 3.85, NAVY, radius=True)
text(slide, "from langchain_openai import ChatOpenAI\n\nreturn ChatOpenAI(\n    model=os.getenv(\"OPENAI_MODEL\",\n                   \"gpt-4o-mini\"),\n    temperature=0,\n)", 1.0, 2.22, 5.5, 2.8, 16, WHITE, font="Consolas")
text(slide, "Configuration", 7.35, 2.02, 4.1, 0.35, 20, ORANGE, True)
rich_lines(slide, ["Provider: OpenAI", "Default model: gpt-4o-mini", "Framework: LangChain", "Temperature: 0", "Credential: OPENAI_API_KEY", "Model override: OPENAI_MODEL"], 7.35, 2.72, 4.5, 2.8, 18, INK, 8)
footer(slide, "Temperature 0 favors consistent, controlled explanations over creative variation.")

# 11
slide = prs.slides.add_slide(blank)
header(slide, "LLM safety boundary", "GROUNDED NARRATIVE", 11)
rect(slide, 0.72, 2.0, 11.85, 1.35, MIST, radius=True)
text(slide, "Do not invent prices, returns, tax advice, or securities. Explain trade-offs, mention scenario risks, cite sources, and state that this is not financial advice.", 1.0, 2.32, 11.25, 0.7, 21, NAVY, True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
rect(slide, 0.95, 4.1, 3.35, 1.1, TEAL, radius=True)
rect(slide, 4.98, 4.1, 3.35, 1.1, ORANGE, radius=True)
rect(slide, 9.02, 4.1, 3.35, 1.1, GOLD, radius=True)
text(slide, "Deterministic\ncalculations", 1.15, 4.36, 2.95, 0.55, 18, WHITE, True, align=PP_ALIGN.CENTER)
text(slide, "Structured facts\ninto prompt", 5.18, 4.36, 2.95, 0.55, 18, WHITE, True, align=PP_ALIGN.CENTER)
text(slide, "Natural-language\nexplanation", 9.22, 4.36, 2.95, 0.55, 18, NAVY, True, align=PP_ALIGN.CENTER)
footer(slide, "Key design principle: the model explains the recommendation; it does not originate the financial calculation.")

# 12
slide = prs.slides.add_slide(blank)
header(slide, "Scenario stress testing", "RISK COMMUNICATION", 12)
scenarios = [("Market downturn", -13.4, RED), ("Rate hike", -5.9, ORANGE), ("Inflation spike", -3.3, GOLD)]
text(slide, "Illustrative change for the demo portfolio", 0.82, 1.95, 5.5, 0.3, 17, SLATE)
for i, (label, change, color) in enumerate(scenarios):
    x = 0.95 + i * 4.05
    text(slide, label, x, 2.72, 3.0, 0.3, 17, NAVY, True, align=PP_ALIGN.CENTER)
    rect(slide, x + 0.7, 3.35, 1.65, 1.8, MIST, radius=True)
    rect(slide, x + 0.7, 3.35 + (1.8 * (1 - abs(change) / 15)), 1.65, 1.8 * abs(change) / 15, color, radius=True)
    text(slide, f"{change:.1f}%", x + 0.82, 5.45, 1.4, 0.35, 22, color, True, align=PP_ALIGN.CENTER)
text(slide, "Predefined shocks are transparent assumptions, not market predictions.", 2.75, 6.2, 7.8, 0.3, 16, SLATE, True, align=PP_ALIGN.CENTER)
footer(slide, "Code anchor: services/scenarios.py. Each asset class receives an explicit scenario shock.")

# 13
slide = prs.slides.add_slide(blank)
header(slide, "QA and suitability gate", "COMPLIANCE GUARDRAIL", 13)
checks = [("Calculations outside LLM", TEAL), ("Retrieved sources present", BLUE), ("Disclaimer present", ORANGE)]
for i, (label, color) in enumerate(checks):
    x = 0.9 + i * 4.05
    rect(slide, x, 2.15, 3.35, 1.25, color, radius=True)
    text(slide, "CHECK", x + 0.2, 2.42, 2.95, 0.22, 11, WHITE, True, align=PP_ALIGN.CENTER)
    text(slide, label, x + 0.22, 2.8, 2.9, 0.35, 17, WHITE, True, align=PP_ALIGN.CENTER)
rect(slide, 3.25, 4.65, 6.85, 0.9, MIST, radius=True)
text(slide, "approved = sources > 0 and disclaimer is present", 3.5, 4.95, 6.35, 0.28, 18, NAVY, True, align=PP_ALIGN.CENTER)
text(slide, "This is a presentation guardrail, not a substitute for legal or financial review.", 2.4, 6.1, 8.5, 0.3, 15, RED, True, align=PP_ALIGN.CENTER)
footer(slide, "Code anchor: agents/qa_agent.py. An ungrounded or undisclaimed narrative is not approved.")

# 14
slide = prs.slides.add_slide(blank)
header(slide, "Live demo scenario", "DEMO", 14)
rect(slide, 0.72, 1.95, 4.45, 4.4, NAVY, radius=True)
text(slide, "INPUT", 1.0, 2.25, 3.9, 0.25, 12, GOLD, True, align=PP_ALIGN.CENTER)
rich_lines(slide, ["Risk: moderate", "Equities: $7,000", "Bonds: $3,000", "Monthly contribution: $250", "Duration: 5 years", "Assumed return: 6%"], 1.25, 2.85, 3.4, 2.5, 19, WHITE, 13)
text(slide, "EXPECTED OUTPUT", 5.95, 2.02, 5.25, 0.3, 12, TEAL, True, align=PP_ALIGN.CENTER)
rich_lines(slide, ["Current equities: 70%", "Target equities: 50%", "Decrease equities: $2,000", "Increase bonds: $500", "Add cash: $500", "Run three stress scenarios"], 6.25, 2.72, 4.65, 2.55, 19, INK, 10)
rect(slide, 6.15, 5.65, 4.9, 0.52, MIST, radius=True)
text(slide, "streamlit run main.py", 6.35, 5.82, 4.5, 0.2, 15, NAVY, True, font="Consolas", align=PP_ALIGN.CENTER)
footer(slide, "Demo sequence: enter profile and holdings -> generate report -> show recommendations -> show chart -> show QA status.")

# 15
bullet_slide("Limitations and next steps", "ROADMAP", [
    "Current RAG uses keyword matching; embeddings and a vector store are future options.",
    "Scenario shocks and annual returns are illustrative assumptions.",
    "Future work: Monte Carlo simulation, fees, taxes, inflation, withdrawals, and historical backtesting.",
    "Future product work: CSV upload, richer risk questionnaire, news analysis, and portfolio history.",
], "Talk track: The project is intentionally transparent about what it calculates and what it does not claim.", 15, BLUE)

# 16
slide = prs.slides.add_slide(blank)
rect(slide, 0, 0, 13.333, 7.5, NAVY)
rect(slide, 0, 0, 0.18, 7.5, TEAL)
text(slide, "Closing message", 0.85, 0.9, 5.6, 0.45, 16, GOLD, True)
text(slide, "Explainable guidance\nwith responsible AI", 0.85, 1.55, 7.0, 1.15, 35, WHITE, True)
text(slide, "The Portfolio Advisor combines deterministic portfolio logic, local knowledge retrieval, optional OpenAI narration, scenario testing, and QA guardrails.", 0.9, 3.25, 6.5, 1.0, 21, RGBColor(202, 218, 226))
rect(slide, 8.25, 1.35, 3.65, 3.65, TEAL, radius=True)
text(slide, "CALCULATE\nGROUND\nSTRESS-TEST\nCHECK", 8.62, 2.0, 2.9, 2.1, 25, WHITE, True, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)
text(slide, "Thank you", 0.9, 6.35, 2.3, 0.35, 20, WHITE, True)
text(slide, "Syed Hussein  |  Capstone Project 1", 0.9, 6.8, 4.8, 0.25, 11, RGBColor(202, 218, 226))

prs.save(OUT)
print(OUT)
