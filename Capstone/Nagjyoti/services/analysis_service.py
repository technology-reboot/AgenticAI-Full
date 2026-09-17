import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from models import AnalysisRequest, PortfolioConfig


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "portfolio_training_data.json"
)


class AnalysisService:
    """
    Performs deterministic portfolio calculations.

    Responsibilities:
    - Calculate portfolio market value
    - Calculate holding weights
    - Calculate asset-class allocation
    - Calculate sector allocation
    - Calculate annualized return
    - Calculate annualized volatility
    - Calculate Sharpe ratio
    - Calculate maximum drawdown
    - Calculate concentration metrics
    - Run What-If stress tests
    - Run Monte Carlo simulation

    This service does not generate investment recommendations.
    Recommendations belong to the Advisory Agent.
    """

    def __init__(
        self,
        data_file: Path = DATA_FILE,
    ) -> None:
        self.data = self._load_data(data_file)

        self.training_data = self.data.get(
            "training_data",
            [],
        )

        self.scenario_defaults = self.data.get(
            "scenario_defaults",
            {},
        )

        self.rules = self.data.get(
            "rules",
            {},
        )

        self.disclaimer = self.rules.get(
            "disclaimer",
            (
                "This output is provided for educational "
                "and informational purposes only. It is not "
                "personalized investment advice."
            ),
        )

    @staticmethod
    def _load_data(
        data_file: Path,
    ) -> Dict[str, Any]:
        """
        Load asset metadata, scenario assumptions and rules.

        If the file is unavailable, empty defaults are returned.
        """

        if not data_file.exists():
            return {
                "training_data": [],
                "scenario_defaults": {},
                "rules": {},
            }

        with open(
            data_file,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def analyze(
        self,
        request: AnalysisRequest,
    ) -> Dict[str, Any]:
        """
        Run the complete portfolio analysis workflow.

        Returns a dictionary expected by AnalysisResponse.
        """

        if not request.holdings:
            raise ValueError(
                "Holdings list cannot be empty."
            )

        holding_values = self.calculate_holding_values(
            request
        )

        total_market_value = sum(
            market_value
            for _, market_value in holding_values
        )

        if total_market_value <= 0:
            raise ValueError(
                "Total portfolio market value must be positive."
            )

        asset_weights = self.calculate_asset_weights(
            holding_values=holding_values,
            total_market_value=total_market_value,
        )

        (
            asset_class_allocation,
            sector_allocation,
            allocation_warnings,
        ) = self.calculate_allocations(
            request=request,
            asset_weights=asset_weights,
        )

        historical_metrics = (
            self.calculate_historical_metrics(
                request=request,
                asset_weights=asset_weights,
                config=request.config,
            )
        )

        concentration = self.calculate_concentration(
            asset_weights
        )

        largest_holding_weight = concentration[
            "largest_holding_weight"
        ]

        largest_sector_weight = round(
            max(
                sector_allocation.values(),
                default=0.0,
            ),
            8,
        )

        data_quality_warnings = list(
            allocation_warnings
        )

        data_quality_warnings.extend(
            self.generate_data_quality_warnings(
                request=request,
                historical_metrics=historical_metrics,
            )
        )

        # Remove duplicate warnings while preserving order.
        data_quality_warnings = list(
            dict.fromkeys(data_quality_warnings)
        )

        scenario_results = self.run_stress_tests(
            current_value=total_market_value,
            selected_scenario=request.scenario,
        )

        monte_carlo_results = self.run_monte_carlo(
            current_value=total_market_value,
            annualized_return=historical_metrics[
                "annualized_return"
            ],
            annualized_volatility=historical_metrics[
                "annualized_volatility"
            ],
            years=request.goal.time_horizon_years,
            monthly_contribution=(
                request.goal.monthly_contribution
            ),
            target_amount=request.goal.target_amount,
            simulations=(
                request.config.monte_carlo_simulations
            ),
            random_seed=request.config.random_seed,
        )

        analysis_summary = self.build_summary(
            request=request,
            historical_metrics=historical_metrics,
            largest_holding_weight=(
                largest_holding_weight
            ),
            largest_sector_weight=(
                largest_sector_weight
            ),
            goal_success_probability=(
                monte_carlo_results[
                    "goal_success_probability"
                ]
            ),
        )

        return {
            "total_market_value": round(
                total_market_value,
                2,
            ),
            "asset_weights": asset_weights,
            "asset_class_allocation": (
                asset_class_allocation
            ),
            "sector_allocation": sector_allocation,
            "annualized_return": historical_metrics[
                "annualized_return"
            ],
            "annualized_volatility": (
                historical_metrics[
                    "annualized_volatility"
                ]
            ),
            "sharpe_ratio": historical_metrics[
                "sharpe_ratio"
            ],
            "maximum_drawdown": historical_metrics[
                "maximum_drawdown"
            ],
            "largest_holding_weight": (
                largest_holding_weight
            ),
            "largest_sector_weight": (
                largest_sector_weight
            ),
            "concentration": concentration,
            "scenario_results": scenario_results,
            "monte_carlo_results": (
                monte_carlo_results
            ),
            "data_quality_warnings": (
                data_quality_warnings
            ),
            "analysis_summary": analysis_summary,
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def calculate_holding_values(
        request: AnalysisRequest,
    ) -> List[Tuple[str, float]]:
        """
        Calculate the current market value of each holding.

        Market value = quantity * current price.

        Purchase price is used only when current price is unavailable.
        """

        values: List[Tuple[str, float]] = []

        for holding in request.holdings:
            price = (
                holding.current_price
                if holding.current_price is not None
                else holding.purchase_price
            )

            if price is None or price <= 0:
                raise ValueError(
                    "Missing a valid current price or "
                    f"purchase price for {holding.symbol}."
                )

            if holding.quantity <= 0:
                raise ValueError(
                    f"Quantity must be positive for "
                    f"{holding.symbol}."
                )

            market_value = holding.quantity * price

            values.append(
                (
                    holding.symbol,
                    market_value,
                )
            )

        return values

    @staticmethod
    def calculate_asset_weights(
        holding_values: List[Tuple[str, float]],
        total_market_value: float,
    ) -> Dict[str, float]:
        """
        Calculate the percentage weight of each holding.

        Values are stored as decimal fractions:
        0.25 means 25%.
        """

        if total_market_value <= 0:
            raise ValueError(
                "Total market value must be positive."
            )

        weights: Dict[str, float] = {}

        for symbol, market_value in holding_values:
            # Support duplicate tickers by combining their values.
            existing_weight = weights.get(
                symbol,
                0.0,
            )

            weights[symbol] = (
                existing_weight
                + market_value / total_market_value
            )

        return {
            symbol: round(weight, 8)
            for symbol, weight in weights.items()
        }

    def calculate_allocations(
        self,
        request: AnalysisRequest,
        asset_weights: Dict[str, float],
    ) -> Tuple[
        Dict[str, float],
        Dict[str, float],
        List[str],
    ]:
        """
        Calculate asset-class and sector allocations using metadata
        from portfolio_training_data.json.
        """

        metadata = {
            str(
                record.get(
                    "symbol",
                    "",
                )
            ).strip().upper(): record
            for record in self.training_data
        }

        asset_class_allocation: Dict[
            str,
            float,
        ] = {}

        sector_allocation: Dict[
            str,
            float,
        ] = {}

        warnings: List[str] = []

        processed_symbols = set()

        for holding in request.holdings:
            symbol = holding.symbol.upper()

            # A duplicated ticker should not have its combined weight
            # counted multiple times.
            if symbol in processed_symbols:
                continue

            processed_symbols.add(symbol)

            record = metadata.get(
                symbol,
                {},
            )

            if not record:
                warnings.append(
                    "Missing asset-class and sector "
                    f"metadata for {symbol}."
                )

            asset_class = str(
                record.get(
                    "asset_class",
                    "unknown",
                )
            ).strip().lower()

            sector = str(
                record.get(
                    "sector",
                    "unknown",
                )
            ).strip().lower()

            weight = asset_weights.get(
                symbol,
                0.0,
            )

            asset_class_allocation[asset_class] = (
                asset_class_allocation.get(
                    asset_class,
                    0.0,
                )
                + weight
            )

            sector_allocation[sector] = (
                sector_allocation.get(
                    sector,
                    0.0,
                )
                + weight
            )

        asset_class_allocation = {
            asset_class: round(
                weight,
                8,
            )
            for asset_class, weight
            in asset_class_allocation.items()
        }

        sector_allocation = {
            sector: round(
                weight,
                8,
            )
            for sector, weight
            in sector_allocation.items()
        }

        return (
            asset_class_allocation,
            sector_allocation,
            warnings,
        )

    @staticmethod
    def calculate_historical_metrics(
        request: AnalysisRequest,
        asset_weights: Dict[str, float],
        config: PortfolioConfig,
    ) -> Dict[str, Any]:
        """
        Calculate historical portfolio metrics from holding histories.

        Historical prices must be ordered from oldest to newest.
        """

        asset_returns: Dict[
            str,
            List[float],
        ] = {}

        history_warnings: List[str] = []

        processed_symbols = set()

        for holding in request.holdings:
            symbol = holding.symbol.upper()

            if symbol in processed_symbols:
                continue

            processed_symbols.add(symbol)

            history = holding.history

            if len(history) >= 2:
                daily_returns: List[float] = []

                for index in range(
                    1,
                    len(history),
                ):
                    previous_price = history[
                        index - 1
                    ]

                    current_price = history[
                        index
                    ]

                    if previous_price <= 0:
                        continue

                    if current_price <= 0:
                        continue

                    daily_return = (
                        current_price
                        / previous_price
                        - 1
                    )

                    daily_returns.append(
                        daily_return
                    )

                if daily_returns:
                    asset_returns[symbol] = (
                        daily_returns
                    )
                else:
                    asset_returns[symbol] = [
                        0.0
                    ] * max(
                        2,
                        config.observations_used_for_annualization,
                    )

                    history_warnings.append(
                        "No valid historical returns "
                        f"were available for {symbol}."
                    )

            else:
                asset_returns[symbol] = [
                    0.0
                ] * max(
                    2,
                    config.observations_used_for_annualization,
                )

                history_warnings.append(
                    "Insufficient historical prices "
                    f"for {symbol}; zero returns were "
                    "used for the demo calculation."
                )

        valid_lengths = [
            len(return_series)
            for return_series in asset_returns.values()
            if return_series
        ]

        observation_count = (
            min(valid_lengths)
            if valid_lengths
            else 1
        )

        portfolio_daily_returns: List[float] = []

        for index in range(observation_count):
            portfolio_return = 0.0

            for symbol, weight in asset_weights.items():
                symbol_returns = asset_returns.get(
                    symbol,
                    [],
                )

                if index < len(symbol_returns):
                    portfolio_return += (
                        weight
                        * symbol_returns[index]
                    )

            portfolio_daily_returns.append(
                portfolio_return
            )

        if not portfolio_daily_returns:
            portfolio_daily_returns = [0.0]

        mean_daily_return = statistics.fmean(
            portfolio_daily_returns
        )

        # Guard against invalid compounding if daily return <= -100%.
        compounded_base = max(0.000001, 1 + mean_daily_return)
        annualized_return = (compounded_base ** config.trading_days - 1)

        # Prevent unrealistic demo outputs
        annualized_return = max(min(annualized_return, 0.15),-0.15,)

        # Cap unrealistic returns for demo purposes
        annualized_return = min(annualized_return, 0.25)
        annualized_return = max(annualized_return,-0.25)

        if len(portfolio_daily_returns) >= 2:
            daily_volatility = statistics.pstdev(
                portfolio_daily_returns
            )
        else:
            daily_volatility = 0.0

        annualized_volatility = (daily_volatility * config.trading_days ** 0.5)

        if annualized_volatility > 0:
            sharpe_ratio = (annualized_return - config.risk_free_rate) / annualized_volatility
        else:
            sharpe_ratio = 0.0

        # Cap unrealistic Sharpe values for demo
        sharpe_ratio = max(min(sharpe_ratio, 5.0),-5.0)

        cumulative_value = 1.0
        peak_value = 1.0
        drawdowns: List[float] = []

        for daily_return in portfolio_daily_returns:
            cumulative_value *= (1 + daily_return)
            peak_value = max(peak_value, cumulative_value,)
            drawdown = (cumulative_value / peak_value - 1)
            drawdowns.append(drawdown)
        maximum_drawdown = (abs(min(drawdowns))
            if drawdowns
            else 0.0
        )

        return {
            "annualized_return": round(annualized_return, 8),
            "annualized_volatility": round(annualized_volatility, 8),
            "sharpe_ratio": round(sharpe_ratio,8),
            "maximum_drawdown": round(maximum_drawdown, 8),
            "portfolio_return_series": (portfolio_daily_returns),
            "daily_asset_returns": asset_returns,
            "history_warnings": history_warnings,
            "observations_used": observation_count,
        }

    @staticmethod
    def calculate_concentration(
        asset_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Calculate portfolio concentration metrics.

        HHI is calculated as the sum of squared holding weights.
        """

        weights = list(
            asset_weights.values()
        )

        if not weights:
            return {
                "largest_holding_weight": 0.0,
                "top_three_weight": 0.0,
                "herfindahl_index": 0.0,
            }

        largest_holding_weight = max(
            weights
        )

        top_three_weight = sum(
            sorted(
                weights,
                reverse=True,
            )[:3]
        )

        herfindahl_index = sum(
            weight ** 2
            for weight in weights
        )

        return {
            "largest_holding_weight": round(
                largest_holding_weight,
                8,
            ),
            "top_three_weight": round(
                top_three_weight,
                8,
            ),
            "herfindahl_index": round(
                herfindahl_index,
                8,
            ),
        }

    def generate_data_quality_warnings(
            self,
            request: AnalysisRequest,
            historical_metrics):
        """Generate warnings about missing or limited input data."""

        warnings: list[str] = []

        warnings.extend(historical_metrics.get("history_warnings",[],))

        observations_used = int(historical_metrics.get("observations_used",0,))

        if observations_used < 30:
            warnings.append(
                "The historical sample contains fewer "
                "than 30 return observations. Risk metrics "
                "may be less reliable.")

        symbols = [holding.symbol
                   for holding in request.holdings
                   ]

        if len(symbols) != len(set(symbols)):
            warnings.append(
                "Duplicate symbols were found. Duplicate "
                "holdings were combined for weight calculations."
            )

        return warnings

    def run_stress_tests(
        self,
        current_value: float,
        selected_scenario: str,
    ) -> Dict[str, Any]:
        """
        Run simple deterministic What-If scenarios.

        Scenario multipliers are demo assumptions loaded from
        portfolio_training_data.json. They are not forecasts.
        """

        if current_value <= 0:
            raise ValueError(
                "Current portfolio value must be positive."
            )

        scenario_names = [
            "base",
            "rate_hike",
            "market_downturn",
            "inflation",
        ]

        default_assumptions = {
            "base": {
                "growth_multiplier": 1.00,
                "stress_multiplier": 1.00,
            },
            "rate_hike": {
                "growth_multiplier": 0.94,
                "stress_multiplier": 0.88,
            },
            "market_downturn": {
                "growth_multiplier": 0.89,
                "stress_multiplier": 0.79,
            },
            "inflation": {
                "growth_multiplier": 0.96,
                "stress_multiplier": 0.82,
            },
        }

        results: Dict[str, Any] = {}

        for scenario_name in scenario_names:
            configured_assumptions = (
                self.scenario_defaults.get(
                    scenario_name,
                    {},
                )
            )

            fallback_assumptions = (
                default_assumptions[
                    scenario_name
                ]
            )

            stress_multiplier = float(
                configured_assumptions.get(
                    "stress_multiplier",
                    fallback_assumptions[
                        "stress_multiplier"
                    ],
                )
            )

            growth_multiplier = float(
                configured_assumptions.get(
                    "growth_multiplier",
                    fallback_assumptions[
                        "growth_multiplier"
                    ],
                )
            )

            if stress_multiplier < 0:
                raise ValueError(
                    f"Invalid stress multiplier for "
                    f"{scenario_name}."
                )

            stressed_value = (
                current_value
                * stress_multiplier
            )

            value_change = (
                stressed_value
                - current_value
            )

            change_percent = (
                stress_multiplier
                - 1
            )

            results[scenario_name] = {
                "selected": (
                    scenario_name
                    == selected_scenario
                ),
                "current_value": round(
                    current_value,
                    2,
                ),
                "stressed_value": round(
                    stressed_value,
                    2,
                ),
                "value_change": round(
                    value_change,
                    2,
                ),
                "change_percent": round(
                    change_percent,
                    8,
                ),
                "stress_multiplier": (
                    stress_multiplier
                ),
                "growth_multiplier": (
                    growth_multiplier
                ),
                "assumption_notice": (
                    "Demo scenario assumption, "
                    "not a market forecast."
                ),
            }

        return results

    @staticmethod
    def run_monte_carlo(
        current_value: float,
        annualized_return: float,
        annualized_volatility: float,
        years: int,
        monthly_contribution: float,
        target_amount: float,
        simulations: int,
        random_seed: int,
    ) -> Dict[str, Any]:
        """
        Run a monthly Monte Carlo portfolio projection.

        Output includes:
        - Goal success probability
        - P10 outcome
        - P50 outcome
        - P90 outcome
        - Yearly projection bands

        Results are simulated estimates, not guarantees.
        """

        if current_value <= 0:
            raise ValueError(
                "Current portfolio value must be positive."
            )

        if years <= 0:
            raise ValueError(
                "Investment horizon must be positive."
            )

        if simulations < 100:
            raise ValueError(
                "At least 100 Monte Carlo simulations "
                "are required."
            )

        if monthly_contribution < 0:
            raise ValueError(
                "Monthly contribution cannot be negative."
            )

        if target_amount <= 0:
            raise ValueError(
                "Target amount must be positive."
            )

        random_generator = (
            np.random.default_rng(
                random_seed
            )
        )

        months = years * 12

        safe_annualized_return = max(min(annualized_return, 0.15), -0.15)

        monthly_return = (
            (1 + safe_annualized_return)
            ** (1 / 12)
            - 1
        )

        monthly_volatility = max(
            0.0,
            annualized_volatility
            / np.sqrt(12),
        )

        portfolio_values = np.full(
            simulations,
            current_value,
            dtype=float,
        )

        yearly_p10: List[float] = []
        yearly_p50: List[float] = []
        yearly_p90: List[float] = []

        for month in range(
            1,
            months + 1,
        ):
            simulated_returns = (
                random_generator.normal(
                    loc=monthly_return,
                    scale=monthly_volatility,
                    size=simulations,
                )
            )

            # Prevent mathematically impossible losses below -100%
            # and limit extreme demo outliers.
            simulated_returns = np.clip(
                simulated_returns,
                -0.95,
                2.0,
            )

            portfolio_values = (
                portfolio_values
                * (1 + simulated_returns)
                + monthly_contribution
            )

            # Portfolio values cannot be negative.
            portfolio_values = np.maximum(
                portfolio_values,
                0.0,
            )

            if month % 12 == 0:
                yearly_p10.append(
                    round(
                        float(
                            np.percentile(
                                portfolio_values,
                                10,
                            )
                        ),
                        2,
                    )
                )

                yearly_p50.append(
                    round(
                        float(
                            np.percentile(
                                portfolio_values,
                                50,
                            )
                        ),
                        2,
                    )
                )

                yearly_p90.append(
                    round(
                        float(
                            np.percentile(
                                portfolio_values,
                                90,
                            )
                        ),
                        2,
                    )
                )

        goal_success_probability = float(
            np.mean(
                portfolio_values
                >= target_amount
            )
        )

        worst_case_p10 = float(
            np.percentile(
                portfolio_values,
                10,
            )
        )

        median_case_p50 = float(
            np.percentile(
                portfolio_values,
                50,
            )
        )

        best_case_p90 = float(
            np.percentile(
                portfolio_values,
                90,
            )
        )

        return {
            "simulations": simulations,
            "investment_horizon_years": years,
            "goal_success_probability": round(
                goal_success_probability,
                6,
            ),
            "worst_case_p10": round(
                worst_case_p10,
                2,
            ),
            "median_case_p50": round(
                median_case_p50,
                2,
            ),
            "best_case_p90": round(
                best_case_p90,
                2,
            ),
            "yearly_projection": {
                "years": list(
                    range(
                        1,
                        years + 1,
                    )
                ),
                "p10": yearly_p10,
                "p50": yearly_p50,
                "p90": yearly_p90,
            },
            "assumptions": {
                "annualized_return": round(
                    annualized_return,
                    8,
                ),
                "annualized_volatility": round(
                    annualized_volatility,
                    8,
                ),
                "monthly_contribution": round(
                    monthly_contribution,
                    2,
                ),
                "target_amount": round(
                    target_amount,
                    2,
                ),
                "random_seed": random_seed,
                "projection_notice": (
                    "Simulation based on historical inputs "
                    "and assumptions. Results are not guaranteed."
                ),
            },
        }

    @staticmethod
    def build_summary(
        request: AnalysisRequest,
        historical_metrics: Dict[str, Any],
        largest_holding_weight: float,
        largest_sector_weight: float,
        goal_success_probability: float,
    ) -> str:
        """
        Build a deterministic human-readable analysis summary.
        """

        annualized_return = historical_metrics[
            "annualized_return"
        ]

        annualized_volatility = historical_metrics[
            "annualized_volatility"
        ]

        sharpe_ratio = historical_metrics[
            "sharpe_ratio"
        ]

        maximum_drawdown = historical_metrics[
            "maximum_drawdown"
        ]

        return (
            f"Goal '{request.goal.name}' was evaluated "
            f"over {request.goal.time_horizon_years} years. "
            f"The calculated historical annualized return is "
            f"{annualized_return:.2%}, annualized volatility "
            f"is {annualized_volatility:.2%}, Sharpe ratio is "
            f"{sharpe_ratio:.2f}, and maximum drawdown is "
            f"{maximum_drawdown:.2%}. The largest holding "
            f"represents {largest_holding_weight:.2%} of the "
            f"portfolio, while the largest sector represents "
            f"{largest_sector_weight:.2%}. Based on the stated "
            f"simulation assumptions, the estimated probability "
            f"of reaching the goal is "
            f"{goal_success_probability:.2%}."
        )