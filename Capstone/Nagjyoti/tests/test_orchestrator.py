import sys
import json
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)


from agents.orchestrator import (
    PortfolioOrchestrator
)

from models import (
    AnalysisRequest,
    Goal,
    RiskResponses,
    Holding,
)


with open(
    "data/investor_profile.json",
    "r",
    encoding="utf-8",
) as file:

    investor = json.load(file)


request = AnalysisRequest(

    goal=Goal(
        **investor["goal"]
    ),

    risk_responses=RiskResponses(
        **investor["risk_responses"]
    ),

    holdings=[
        Holding(
            symbol="ASSET_A",
            quantity=100,
            current_price=120,
            history=[
                100,
                105,
                110,
                120
            ]
        ),
        Holding(
            symbol="ASSET_B",
            quantity=50,
            current_price=80,
            history=[
                70,
                75,
                78,
                80
            ]
        )
    ]
)

orchestrator = (
    PortfolioOrchestrator()
)

result = (
    orchestrator.run(
        request
    )
)

print(
    json.dumps(
        result,
        indent=4
    )
)