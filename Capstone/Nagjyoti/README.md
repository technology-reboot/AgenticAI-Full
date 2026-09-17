# Personalized Portfolio Advisor with What-If Simulation

An AI-powered, multi-agent portfolio analysis platform that helps investors evaluate portfolio performance, understand portfolio risk, assess financial goal achievement, and receive explainable recommendations validated through an independent QA agent.

---

# Problem Statement

Investors often struggle to:

- Understand portfolio risk
- Measure progress toward financial goals
- Interpret investment performance metrics
- Evaluate diversification
- Validate investment recommendations

This solution combines deterministic financial analytics with AI-powered advisory and quality assurance agents to deliver transparent and explainable portfolio insights.

---

# Key Features

## Portfolio Analysis

- Portfolio valuation
- Annualized return
- Annualized volatility
- Sharpe ratio
- Maximum drawdown
- Sector allocation

## Risk Assessment

- Investor risk profiling
- Portfolio risk classification
- Risk alignment analysis
- Concentration risk detection

## Goal Planning

- Monte Carlo simulation
- Financial goal projection
- Goal success probability

## AI Recommendations

- Portfolio observations
- Diversification suggestions
- Rebalancing recommendations
- Goal alignment recommendations

## Quality Assurance

- Independent QA review
- Suitability analysis
- Unsupported claim detection
- Disclaimer validation

---

# Multi-Agent Architecture

                User
                  │
                  ▼
          Streamlit Dashboard
                  │
                  ▼
       Portfolio Orchestrator
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼

Analysis      Risk       Advisory
 Agent        Agent       Agent
                              │
                              ▼
                          QA Agent
                              │
                              ▼
                       Final Output

---

# Agents

## Analysis Agent

Responsible for:

- Portfolio valuation
- Historical performance analysis
- Risk metrics
- Monte Carlo simulations
- Sector analysis

Outputs:

- Annual Return
- Volatility
- Sharpe Ratio
- Drawdown
- Portfolio Value
- Goal Success Probability

---

## Risk Agent

Responsible for:

- Investor risk scoring
- Portfolio risk classification
- Risk alignment assessment
- Warning generation

Outputs:

- Risk Score
- Risk Profile
- Portfolio Risk
- Alignment Status

---

## Advisory Agent

Responsible for:

- Portfolio observations
- Diversification analysis
- Rebalancing suggestions
- Goal alignment recommendations

Uses LLM-based reasoning.

---

## QA Agent

Responsible for:

- Recommendation review
- Suitability assessment
- Unsupported claim detection
- Disclaimer verification

Provides Responsible AI validation.

---

# Project Structure

portfolio-advisor/

agents/
    analysis_agent.py
    risk_agent.py
    advisory_agent.py
    qa_agent.py
    orchestrator.py

services/
    analysis_service.py
    risk_service.py
    llm_service.py

models/
    ...

data/
    portfolio_training_data.json

streamlit_app.py
requirements.txt

README.md
AGENT_DESIGN.md
DEMO_GUIDE.md

---

# Installation

## Create Virtual Environment

```bash
python -m venv .venv
```

## Activate

Windows

```bash
.venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Application

```bash
streamlit run streamlit_app.py
```

---

# Portfolio Input

Two options are supported:

## Manual Entry

Enter:

- Symbol
- Quantity
- Current Price
- Price History

Example:

MSFT
Quantity = 100
Current Price = 500

History:
450,460,470,480,490,500

---

## CSV Upload

Example CSV:

```csv
symbol,quantity,current_price,history
MSFT,100,500,"450,460,470,480,490,500"
TSLA,50,300,"250,270,290,310,300"
JPM,100,250,"220,230,240,245,250"
```

---

# Sample Output

Portfolio Overview

- Portfolio Value
- Annual Return
- Volatility
- Sharpe Ratio

Risk Assessment

- Risk Profile
- Portfolio Risk
- Alignment Status

Goal Planning

- Best Case
- Expected Case
- Worst Case
- Goal Success Probability

Recommendations

- Diversification Suggestions
- Rebalancing Suggestions
- Goal Alignment Suggestions

QA Review

- Suitability Analysis
- Recommendation Validation

---

# Responsible AI

The platform:

- Does not provide financial advice
- Provides educational insights only
- Clearly discloses assumptions
- Uses QA validation before presenting recommendations

---

# Disclaimer

This solution is intended for educational and informational purposes only and does not constitute investment advice.