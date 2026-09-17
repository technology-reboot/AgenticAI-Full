from typing import Any, Dict


class PortfolioReportBuilder:
    def build(self, request, total_market_value: float, weights: Dict[str, float], asset_class_allocation: Dict[str, float], sector_allocation: Dict[str, float], annualized_return: float, annualized_volatility: float, sharpe_ratio: float, maximum_drawdown: float, concentration: Dict[str, float], warnings: list[str], daily_asset_returns: Dict[str, list[float]], portfolio_return_series: list[float], disclaimer: str, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "scenario": request.scenario,
            "goal": request.goal.model_dump(),
            "risk_responses": request.risk_responses.model_dump(),
            "methodology": request.config.methodology,
            "risk_free_rate_assumption": request.config.risk_free_rate,
            "observations_used_for_annualization": request.config.observations_used_for_annualization,
            "portfolio_metrics": {
                "total_market_value": round(total_market_value, 2),
                "asset_weights": weights,
                "asset_class_allocation": asset_class_allocation,
                "sector_allocation": sector_allocation,
                "annualized_return": annualized_return,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "maximum_drawdown": maximum_drawdown,
                "concentration": concentration,
                "data_quality_warnings": warnings,
            },
            "daily_asset_returns": daily_asset_returns,
            "portfolio_return_series": portfolio_return_series,
            "disclaimer": disclaimer,
            "stress_tests": {
                "rate_hike": scenarios.get("rate_hike", {"growth_multiplier": 0.94, "stress_multiplier": 0.88}),
                "market_downturn": scenarios.get("market_downturn", {"growth_multiplier": 0.89, "stress_multiplier": 0.79}),
                "inflation": scenarios.get("inflation", {"growth_multiplier": 0.96, "stress_multiplier": 0.82}),
            },
        }
