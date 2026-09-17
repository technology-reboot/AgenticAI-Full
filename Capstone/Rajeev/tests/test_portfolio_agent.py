import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from main import app, AgentRequest, PortfolioAnalysisAgent


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analysis_agent_returns_expected_response_shape():
    payload = {
        "goal": {
            "name": "House down payment",
            "target_amount": 3000000,
            "time_horizon_years": 7,
            "monthly_contribution": 25000,
        },
        "risk_responses": {
            "loss_tolerance_percent": 15,
            "income_stability": "stable",
            "investment_experience": "intermediate",
            "liquidity_need": "medium",
        },
        "holdings": [
            {"symbol": "ASSET_A", "quantity": 100, "purchase_price": 120},
        ],
        "scenario": "base",
    }
    response = client.post("/agent", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "total_market_value" in body
    assert "asset_weights" in body
    assert "asset_class_allocation" in body
    assert "sector_allocation" in body
    assert "annualized_return" in body
    assert "annualized_volatility" in body
    assert "sharpe_ratio" in body
    assert "maximum_drawdown" in body
    assert "concentration" in body
    assert "data_quality_warnings" in body
    assert "analysis" in body
    assert "recommendations" in body
    assert "analytics_report" in body


def test_streamlit_ui_form_includes_current_price_and_history_fields():
    streamlit_source = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    text = streamlit_source.read_text(encoding="utf-8")
    assert "current_price" in text
    assert "history" in text


def test_agent_class_simple_prediction():
    agent = PortfolioAnalysisAgent()
    payload = AgentRequest(
        goal={
            "name": "House down payment",
            "target_amount": 3000000,
            "time_horizon_years": 7,
            "monthly_contribution": 25000,
        },
        risk_responses={
            "loss_tolerance_percent": 15,
            "income_stability": "stable",
            "investment_experience": "intermediate",
            "liquidity_need": "medium",
        },
        holdings=[
            {"symbol": "ASSET_A", "quantity": 100, "purchase_price": 120},
        ],
        scenario="base",
    )
    result = agent.evaluate(payload)
    assert result.total_market_value > 0
    assert result.asset_weights.get("ASSET_A")
    assert result.annualized_return >= 0
    assert result.sharpe_ratio >= -1
