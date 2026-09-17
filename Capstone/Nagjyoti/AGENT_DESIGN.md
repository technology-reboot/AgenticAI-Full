# Agent Design Document

# Overview

The application follows a multi-agent design.

Each agent has a clearly defined responsibility.

Portfolio Orchestrator
        │
        ▼
Analysis Agent
        │
        ▼
Risk Agent
        │
        ▼
Advisory Agent
        │
        ▼
QA Agent

---

# Portfolio Orchestrator

Role:

Coordinates execution flow between all agents.

Responsibilities:

- Build execution workflow
- Pass outputs between agents
- Aggregate final response

Output:

Analysis Result
Risk Result
Advisory Result
QA Result

---

# Analysis Agent

Purpose:

Perform financial analysis.

Inputs:

- Holdings
- Historical prices
- Goal information

Responsibilities:

- Return calculations
- Volatility calculations
- Sharpe ratio
- Drawdown
- Portfolio valuation
- Monte Carlo simulation
- Sector allocation

Output:

Portfolio Metrics
Goal Projections
Risk Metrics

---

# Risk Agent

Purpose:

Assess investor suitability.

Inputs:

- Investor Profile
- Portfolio Analytics

Responsibilities:

- Risk scoring
- Risk classification
- Alignment analysis
- Warning generation

Output:

Risk Score
Risk Profile
Portfolio Risk
Alignment Status
Warnings

---

# Advisory Agent

Purpose:

Generate recommendations.

Inputs:

- Analysis Results
- Risk Assessment

Responsibilities:

- Interpret analytics
- Suggest diversification
- Suggest rebalancing
- Recommend goal alignment actions

Output:

Recommendations
Observations
Actionable Insights

---

# QA Agent

Purpose:

Validate recommendations.

Inputs:

- Analysis Results
- Risk Assessment
- Advisory Output

Responsibilities:

- Suitability review
- Unsupported claim detection
- Disclaimer verification
- Responsible AI validation

Outputs:

Approved

or

Revision Required

---

# Benefits of Multi-Agent Design

- Separation of concerns
- Explainability
- Maintainability
- Responsible AI validation
- Independent quality control

---

# Future Enhancements

- Real-time stock prices
- Azure OpenAI integration
- ESG scoring
- Portfolio optimization
- Tax-aware recommendations
- Scenario-based stress testing