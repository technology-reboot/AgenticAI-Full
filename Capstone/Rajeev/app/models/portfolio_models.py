from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Goal(BaseModel):
    name: str = Field(default="House down payment")
    target_amount: float = Field(default=3000000.0)
    time_horizon_years: int = Field(default=7)
    monthly_contribution: float = Field(default=25000.0)


class RiskResponses(BaseModel):
    loss_tolerance_percent: float = Field(default=15.0)
    income_stability: str = Field(default="stable")
    investment_experience: str = Field(default="intermediate")
    liquidity_need: str = Field(default="medium")


class PortfolioConfig(BaseModel):
    trading_days: int = Field(default=252)
    risk_free_rate: float = Field(default=0.03)
    methodology: str = Field(default="fixed_current_weights")
    observations_used_for_annualization: int = Field(default=252)


class Holding(BaseModel):
    symbol: str
    quantity: float
    current_price: Optional[float] = None
    purchase_price: Optional[float] = None
    history: List[float] = Field(default_factory=list)


class AgentRequest(BaseModel):
    goal: Goal = Field(default_factory=Goal)
    risk_responses: RiskResponses = Field(default_factory=RiskResponses)
    holdings: List[Holding]
    scenario: str = Field(default="base")
    config: PortfolioConfig = Field(default_factory=PortfolioConfig)


class AgentResponse(BaseModel):
    total_market_value: float
    asset_weights: Dict[str, float]
    asset_class_allocation: Dict[str, float]
    sector_allocation: Dict[str, float]
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    maximum_drawdown: float
    concentration: Dict[str, float]
    data_quality_warnings: List[str]
    analysis: str
    recommendations: List[str]
    analytics_report: Dict[str, Any]
