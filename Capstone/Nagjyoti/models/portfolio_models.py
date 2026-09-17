from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Goal(BaseModel):
    name: str = "House down payment"

    target_amount: float = Field(
        default=3_000_000,
        gt=0,
    )

    time_horizon_years: int = Field(
        default=7,
        ge=1,
        le=60,
    )

    monthly_contribution: float = Field(
        default=25_000,
        ge=0,
    )


class RiskResponses(BaseModel):
    risk_appetite: Literal[
        "low",
        "medium",
        "high",
    ] = "medium"

    loss_tolerance_percent: float = Field(
        default=15.0,
        ge=0,
        le=100,
    )

    income_stability: Literal[
        "low",
        "medium",
        "high",
        "variable",
        "stable",
    ] = "stable"

    investment_experience: Literal[
        "beginner",
        "intermediate",
        "advanced",
        "low",
        "medium",
        "high",
    ] = "intermediate"

    liquidity_need: Literal[
        "low",
        "medium",
        "high",
    ] = "medium"


class PortfolioConfig(BaseModel):
    trading_days: int = Field(
        default=252,
        ge=1,
    )

    risk_free_rate: float = Field(
        default=0.03,
        ge=0,
        le=1,
    )

    methodology: str = "fixed_current_weights"

    observations_used_for_annualization: int = Field(
        default=252,
        ge=2,
    )

    monte_carlo_simulations: int = Field(
        default=10_000,
        ge=100,
        le=100_000,
    )

    random_seed: int = 42


class Holding(BaseModel):
    symbol: str = Field(min_length=1)
    quantity: float = Field(gt=0)

    current_price: Optional[float] = Field(
        default=None,
        gt=0,
    )

    purchase_price: Optional[float] = Field(
        default=None,
        gt=0,
    )

    history: List[float] = Field(
        default_factory=list
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class AnalysisRequest(BaseModel):
    goal: Goal = Field(default_factory=Goal)

    risk_responses: RiskResponses = Field(
        default_factory=RiskResponses
    )

    holdings: List[Holding]

    scenario: Literal[
        "base",
        "rate_hike",
        "market_downturn",
        "inflation",
    ] = "base"

    config: PortfolioConfig = Field(
        default_factory=PortfolioConfig
    )


class AnalysisResponse(BaseModel):
    total_market_value: float

    asset_weights: Dict[str, float]
    asset_class_allocation: Dict[str, float]
    sector_allocation: Dict[str, float]

    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    maximum_drawdown: float

    largest_holding_weight: float
    largest_sector_weight: float

    concentration: Dict[str, float]

    scenario_results: Dict[str, Any]
    monte_carlo_results: Dict[str, Any]

    data_quality_warnings: List[str]
    analysis_summary: str
    disclaimer: str


class RiskResponse(BaseModel):
    risk_score: float

    risk_profile: Literal[
        "Conservative",
        "Moderate",
        "Aggressive",
    ]

    portfolio_risk_level: Literal[
        "Conservative",
        "Moderate",
        "Aggressive",
    ]

    alignment_status: Literal[
        "Aligned",
        "Partially Aligned",
        "Not Aligned",
    ]

    alignment_reason: str

    score_breakdown: List[Dict[str, Any]]
    warnings: List[str]

    summary: str
    disclaimer: str