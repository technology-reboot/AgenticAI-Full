# Conversational Financial Statement Analyzer

A grounded GenAI MVP for uploading normalized P&L, balance-sheet and cash-flow data, computing ratios deterministically, detecting trends/red flags, retrieving evidence from ChromaDB, answering with citations, and comparing two companies.

## Team ownership
- **Trend & Red Flag Agent — Shubham Shukla:** period deltas and six red-flag patterns.
- **Retrieval / Grounding Agent — Suman Kumar:** normalization, ChromaDB indexing, exact metadata retrieval, grounded context assembly.
- **Narrative & Q&A Agent — Abhishek Tripati:** grounded conversational answers, mandatory figure citations, refusal when evidence is absent.
- **Comparison Agent — Ram M Singh:** side-by-side comparison and currency/FY-end mismatch warnings.

## Architecture
1. **Ingestion:** CSV/XLSX rows are normalized into one metric schema. PDF/TXT narrative notes are indexed as text evidence.
2. **Computation:** ratios are calculated in Python, never by the LLM.
3. **Retrieval:** known numeric metrics are fetched by exact Chroma metadata filters; narrative context uses semantic retrieval.
4. **Agents:** trend/red-flag, retrieval/grounding, narrative/Q&A and comparison are independent services.
5. **Guardrail:** the LLM receives only grounded evidence and must cite every figure. A post-check rejects uncited numeric output.

## Input format
Use one row per metric. Required columns:

`company, period, statement, metric, value, currency, unit, source_file, source_page, fiscal_year_end`

Example metric names are in `data/sample_financials.csv`. Values should use a consistent unit per company/period (for example, all values in INR million). Uploading the same company/period again replaces matching IDs.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The app works without an OpenAI key for deterministic dashboards, ratios, red flags and fallback Q&A. Set `OPENAI_API_KEY` to enable natural-language narratives.

## Docker
```bash
docker compose up --build
```
Open `http://localhost:8501`.

## Test
```bash
pytest -q
```

## Core ratios
- Current ratio = current assets / current liabilities
- Quick ratio = (cash + accounts receivable) / current liabilities
- Debt-to-equity = total debt / total equity
- Debt-to-assets = total debt / total assets
- Gross margin = gross profit / revenue
- Operating margin = operating income / revenue
- Net margin = net income / revenue
- ROA = net income / average total assets
- ROE = net income / average total equity
- DSO = average accounts receivable / revenue × 365
- Inventory days = average inventory / cost of goods sold × 365
- Accrual-quality gap = (net income − operating cash flow) / average total assets

## Red-flag rules
Thresholds are configurable in `config.py` and intentionally transparent:
1. Accrual-quality gap: positive gap above 10% of average assets.
2. DSO climbing: increase above 10% year over year.
3. Margin compression: operating-margin decline above 2 percentage points.
4. Leverage stress: debt/equity above 2.0 or increase above 25%.
5. Inventory build-up: inventory days increase above 15%.
6. Liquidity deterioration: current ratio below 1.0 or decline above 20%.

These are screening signals, not investment advice. Validate accounting definitions and units before production use.
