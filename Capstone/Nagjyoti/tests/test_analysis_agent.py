from agents.analysis_agent import PortfolioAnalysisAgent
from models import AnalysisRequest

agent = PortfolioAnalysisAgent()

request = AnalysisRequest(
    holdings=[
        {
            "symbol": "ASSET_A",
            "quantity": 100,
            "current_price": 120,
            "history": [100, 105, 110, 120]
        }
    ]
)

result = agent.evaluate(request)

print(result.model_dump())