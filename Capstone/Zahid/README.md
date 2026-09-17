# Portfolio Advisor
Personalize Portfolio Advisor with What-if Simulation

• Create a goal-based advisory agent where users enter financial goals, risk appetite, and current holdings, and receive a suggested allocation. The agent should stress-test the portfolio against scenarios (rate hike, market downturn, inflation), visualize projected outcomes in charts, and suggest rebalancing steps.<br/>
• Suitability disclaimers must be included. Bonus: multi-agent roles (risk profiler, allocator, simulator).<br/>
• Objective: Deliver personalized, scenario-tested investment guidance with clear risk communication.<br/>
• Learning takeaways: Goal-based financial planning logic, Monte Carlo / scenario simulation, data visualization, risk profiling, and embedding responsible-advice guardrails and disclaimers.<br/>

Data Agent -<br/>
Ingests the portfolio CSV, fetches live prices via yfinance and news headlines per ticker; outputs a clean, structured dataset for everything downstream.

Analysis Agent -<br/>
Computes portfolio metrics — returns, Sharpe ratio, sector allocation, concentration — and produces the analytics report the advisory chain reasons from

Risk Agent -<br/>
Scores the investor's risk profile (conservative / moderate / aggressive) and evaluates whether current holdings match that tolerance

Advisory Agent -<br/>
Generates investment and rebalancing suggestions grounded in the RAG knowledge layer, tailored to the risk profile

QA Agent -<br/>
The compliance and suitability gate — checks every recommendation before it reaches the user, and can send it back for revision

## Advisory Agent implementation

The project now uses a role-based workflow. `PortfolioAdvisorOrchestrator` coordinates Data, Risk, Advisory, and QA agents while reusable services keep calculations deterministic. It includes:

- Risk-profile target allocations for conservative, moderate, and aggressive investors
- Dollar-based rebalancing recommendations from current holdings
- Local RAG retrieval with source citations from `data/knowledge/`
- What-if projections using monthly contributions and an assumed annual return
- A JSON CLI suitable for later use by a supervisor agent or API
- OpenAI narration through `OPENAI_API_KEY` and `gpt-4o-mini`, with an offline fallback
- Market-price enrichment through optional yFinance integration
- Market downturn, rate hike, and inflation spike stress tests
- A Streamlit dashboard with scenario charts

### Run locally

Create and activate a virtual environment, then install the project and its test dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest
portfolio-advisor --risk moderate --holding US_EQ:equities:7000 --holding BOND:bonds:3000 --monthly-contribution 250 --years 5 --annual-return 0.06
```

The CLI now runs the full workflow and returns analytics, risk assessment, allocation recommendations, stress scenarios, retrieved sources, narrative model status, and QA checks.

The projections are illustrative only and ignore fees, taxes, inflation, withdrawals, and changing returns. They are not financial advice or a guarantee of performance.

### Run the dashboard

```powershell
copy .env.example .env
streamlit run main.py
```

Add a real `OPENAI_API_KEY` to `.env` to enable the grounded narrative. The calculation, scenario, citation, and QA layers remain usable without a key.

Set `ENABLE_LIVE_MARKET_DATA=1` to enable yFinance enrichment for real ticker symbols. It is disabled by default for deterministic demos and tests.

### Project structure

```text
agents/       Data, Risk, Advisory, QA, and workflow orchestration
services/     Analytics, risk scoring, scenarios, market data, and OpenAI adapter
data/         Knowledge documents and future portfolio/profile inputs
reports/      JSON and Markdown report renderers
main.py       Streamlit dashboard
```
