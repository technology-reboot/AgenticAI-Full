import json

from agents.risk_agent import RiskAgent

with open("data/investor_profile.json", "r") as f:
    investor = json.load(f)

with open("data/portfolio_analytics.json", "r") as f:
    portfolio_analytics = json.load(f)

risk_agent = RiskAgent(use_llm=False)

result = risk_agent.run(
    investor,
    portfolio_analytics
)

print(result)