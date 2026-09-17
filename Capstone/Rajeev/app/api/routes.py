from fastapi import FastAPI, HTTPException

from app.models import AgentRequest, AgentResponse
from app.services import PortfolioService

app = FastAPI(title="Portfolio Advisor Analysis Agent", version="1.0.0")
service = PortfolioService()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "portfolio-advisor-analysis-agent"}


@app.post("/agent", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    try:
        return service.evaluate(request)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive safety
        raise HTTPException(status_code=500, detail=str(exc)) from exc
