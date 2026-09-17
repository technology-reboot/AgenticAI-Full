import json
import os
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from app.models import AgentRequest, AgentResponse, Holding, PortfolioConfig
from app.reporting.portfolio_report import PortfolioReportBuilder

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "portfolio_training_data.json"


class PortfolioAnalysisAgent:
    def __init__(self, data_file: Path = DATA_FILE):
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        self.data = self._load_data(data_file)
        self.training = self.data.get("training_data", [])
        self.rules = self.data.get("rules", {})
        self.scenarios = self.data.get("scenario_defaults", {})
        self.disclaimer = self.rules.get("disclaimer", "This is educational advice and not investment advice.")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.api_key:
            try:
                self.openai_client = OpenAI(api_key=self.api_key)
            except Exception:
                self.openai_client = None
        self.report_builder = PortfolioReportBuilder()

    def _load_data(self, data_file: Path) -> Dict[str, Any]:
        if not data_file.exists():
            return {"training_data": [], "rules": {}, "scenario_defaults": {}}
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate(self, request: AgentRequest) -> AgentResponse:
        if not request.holdings:
            raise HTTPException(status_code=400, detail="Holdings list cannot be empty.")

        values = []
        weights = {}
        for holding in request.holdings:
            price = holding.current_price if holding.current_price is not None else holding.purchase_price
            if price is None or price <= 0:
                raise HTTPException(status_code=400, detail=f"Missing current_price for holding {holding.symbol}.")
            if holding.quantity <= 0:
                raise HTTPException(status_code=400, detail=f"Quantity must be positive for holding {holding.symbol}.")
            values.append((holding.symbol.upper(), holding.quantity * price, price))

        total_market_value = sum(value for _, value, _ in values)
        if total_market_value <= 0:
            raise HTTPException(status_code=400, detail="Holdings total market value must be positive.")

        for symbol, value, _ in values:
            weights[symbol] = round(value / total_market_value, 6)

        records = {item.get("symbol", "").upper(): item for item in self.training}
        warnings = []
        unknown = [holding.symbol.upper() for holding in request.holdings if holding.symbol.upper() not in records]
        if unknown:
            warnings.append(f"Missing training metadata for symbol(s): {', '.join(unknown)}")

        asset_class_allocation: Dict[str, float] = {}
        sector_allocation: Dict[str, float] = {}
        for holding in request.holdings:
            item = records.get(holding.symbol.upper(), {})
            asset_class = item.get("asset_class", "unknown")
            sector = item.get("sector", "unknown")
            weight = weights.get(holding.symbol.upper(), 0.0)
            asset_class_allocation[asset_class] = asset_class_allocation.get(asset_class, 0.0) + weight
            sector_allocation[sector] = sector_allocation.get(sector, 0.0) + weight

        portfolio_returns = self.compute_historical_metrics(request, values, weights, request.config)
        annualized_return = portfolio_returns["annualized_return"]
        annualized_volatility = portfolio_returns["annualized_volatility"]
        sharpe_ratio = portfolio_returns["sharpe_ratio"]
        maximum_drawdown = portfolio_returns["maximum_drawdown"]
        daily_asset_returns = portfolio_returns["daily_asset_returns"]
        portfolio_return_series = portfolio_returns["portfolio_return_series"]

        concentration = self.compute_concentration(weights)
        recommendations = self._recommendations(request, annualized_return, annualized_volatility, metrics=portfolio_returns)

        analytics_report = self.report_builder.build(
            request=request,
            total_market_value=total_market_value,
            weights=weights,
            asset_class_allocation=asset_class_allocation,
            sector_allocation=sector_allocation,
            annualized_return=annualized_return,
            annualized_volatility=annualized_volatility,
            sharpe_ratio=sharpe_ratio,
            maximum_drawdown=maximum_drawdown,
            concentration=concentration,
            warnings=warnings,
            daily_asset_returns=daily_asset_returns,
            portfolio_return_series=portfolio_return_series,
            disclaimer=self.disclaimer,
            scenarios=self.scenarios,
        )

        recommendations = self._generate_ai_recommendations_if_possible(request, analytics_report, recommendations)

        analysis = self._build_local_analysis(request, annualized_return, annualized_volatility, sharpe_ratio)
        analysis = self._generate_ai_analysis_if_possible(request, analytics_report, analysis)

        return AgentResponse(
            total_market_value=round(total_market_value, 2),
            asset_weights=weights,
            asset_class_allocation=asset_class_allocation,
            sector_allocation=sector_allocation,
            annualized_return=annualized_return,
            annualized_volatility=annualized_volatility,
            sharpe_ratio=sharpe_ratio,
            maximum_drawdown=maximum_drawdown,
            concentration=concentration,
            data_quality_warnings=warnings,
            analysis=analysis,
            recommendations=recommendations,
            analytics_report=analytics_report,
        )

    def compute_historical_metrics(self, request: AgentRequest, values: List[Tuple[str, float, float]], weights: Dict[str, float], config: PortfolioConfig) -> Dict[str, Any]:
        daily_asset_returns: Dict[str, List[float]] = {}
        trading_days = max(1, config.trading_days)

        for symbol, _, _ in values:
            history = []
            for holding in request.holdings:
                if holding.symbol.upper() == symbol and holding.history:
                    history = holding.history
                    break
            if len(history) >= 2:
                daily_series = []
                for index in range(1, len(history)):
                    daily_series.append(history[index] / history[index - 1] - 1)
                daily_asset_returns[symbol] = daily_series
            else:
                daily_asset_returns[symbol] = [0.0] * max(2, config.observations_used_for_annualization)

        length = min(len(series) for series in daily_asset_returns.values()) if daily_asset_returns else 1
        if length == 0:
            length = 1
        portfolio_returns = []
        for idx in range(length):
            total = 0.0
            for symbol, _, _ in values:
                total += weights[symbol] * daily_asset_returns[symbol][idx]
            portfolio_returns.append(total)

        if len(portfolio_returns) == 0:
            portfolio_returns = [0.0]

        mean_daily_return = statistics.fmean(portfolio_returns)
        annualized_return = round((1 + mean_daily_return) ** trading_days - 1, 6)
        annualized_volatility = round(statistics.pstdev(portfolio_returns) * (trading_days ** 0.5), 6)
        sharpe_ratio = round((annualized_return - config.risk_free_rate) / max(annualized_volatility, 0.000001), 6)

        cumulative = 1.0
        peak = 1.0
        drawdowns = []
        for daily_return in portfolio_returns:
            cumulative *= (1 + daily_return)
            if cumulative > peak:
                peak = cumulative
            drawdowns.append(cumulative / peak - 1)
        maximum_drawdown = round(abs(min(drawdowns)) if drawdowns else 0.0, 6)

        if all(value == 0.0 for value in portfolio_returns):
            sharpe_ratio = 0.0

        return {
            "daily_asset_returns": daily_asset_returns,
            "portfolio_return_series": portfolio_returns,
            "annualized_return": annualized_return,
            "annualized_volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "maximum_drawdown": maximum_drawdown,
        }

    def compute_concentration(self, weights: Dict[str, float]) -> Dict[str, float]:
        items = list(weights.values())
        largest_holding_weight = round(max(items), 6)
        top_three_weight = round(sum(sorted(items, reverse=True)[:3]), 6)
        herfindahl_index = round(sum(weight * weight for weight in items), 6)
        return {
            "largest_holding_weight": largest_holding_weight,
            "top_three_weight": top_three_weight,
            "herfindahl_index": herfindahl_index,
        }

    def _build_local_analysis(self, request: AgentRequest, annualized_return: float, annualized_volatility: float, sharpe_ratio: float) -> str:
        return (
            f"Goal '{request.goal.name}' evaluated over {request.goal.time_horizon_years} years. "
            f"The portfolio is projected to return {annualized_return:.2%} annually with "
            f"volatility {annualized_volatility:.2%} and Sharpe ratio {sharpe_ratio:.2f}."
        )

    def _generate_ai_recommendations_if_possible(self, request: AgentRequest, analytics_report: Dict[str, Any], fallback_recommendations: List[str]) -> List[str]:
        if not self.openai_client:
            return fallback_recommendations

        try:
            prompt = {
                "goal": request.goal.model_dump(),
                "risk_responses": request.risk_responses.model_dump(),
                "scenario": request.scenario,
                "summary": analytics_report,
                "fallback_recommendations": fallback_recommendations,
            }
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise portfolio advisory assistant. Return exactly a JSON array of 3 or 4 short recommendation strings in plain text. Do not give regulated investment advice. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": json.dumps(prompt, indent=2)},
                ],
            )
            text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                    return parsed[:4]
            except Exception:
                pass
            return fallback_recommendations
        except Exception:
            return fallback_recommendations

    def _generate_ai_analysis_if_possible(self, request: AgentRequest, analytics_report: Dict[str, Any], fallback_text: str) -> str:
        if not self.openai_client:
            return fallback_text + " " + self.disclaimer

        try:
            prompt = {
                "goal": request.goal.model_dump(),
                "risk_responses": request.risk_responses.model_dump(),
                "scenario": request.scenario,
                "summary": analytics_report,
            }
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise portfolio advisory assistant. Produce one short paragraph with scenario-aware financial planning guidance and a clear suitability disclaimer. Do not give regulated investment advice.",
                    },
                    {"role": "user", "content": json.dumps(prompt, indent=2)},
                ],
            )
            text = response.choices[0].message.content.strip()
            return text if text else fallback_text
        except Exception:
            return fallback_text + " " + self.disclaimer

    def _recommendations(self, request: AgentRequest, annualized_return: float, annualized_volatility: float, metrics: Dict[str, Any]) -> List[str]:
        recommendations = []
        if annualized_volatility > 0.20:
            recommendations.append("Reduce volatility by adding defensive or fixed-income exposure and review sector concentration.")
        else:
            recommendations.append("Maintain current exposure and monitor risk on a quarterly basis.")

        if request.goal.target_amount and request.goal.target_amount > 0:
            recommendations.append(f"Track progress toward goal '{request.goal.name}' against the annual contribution path.")

        recommendations.append("Stress-test the portfolio against rate hike, market downturn, and inflation scenarios.")
        recommendations.append("Suitability disclaimer: this output is educational and should be reviewed with a qualified advisor.")
        recommendations.append(
            f"Historical methodology: fixed current weights; risk-free-rate assumption: {request.config.risk_free_rate}; observations: {request.config.observations_used_for_annualization}."
        )
        return recommendations
