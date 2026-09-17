from typing import Any, Dict


class RiskService:

    PROFILE_ORDER = {
        "Conservative": 1,
        "Moderate": 2,
        "Aggressive": 3,
    }

    def assess(
        self,
        investor: Dict[str, Any],
        analytics: Dict[str, Any],
    ) -> Dict[str, Any]:

        risk_score, score_breakdown = (
            self.calculate_risk_score(
                investor
            )
        )

        risk_profile = (
            self.determine_risk_profile(
                risk_score
            )
        )

        portfolio_risk_level = (
            self.determine_portfolio_risk(
                analytics
            )
        )

        alignment = self.check_alignment(
            investor_profile=risk_profile,
            portfolio_profile=portfolio_risk_level,
        )

        warnings = self.generate_warnings(
            analytics,
            risk_profile,
        )

        warnings.extend(
            analytics.get(
                "data_quality_warnings",
                []
            )
        )

        return {
            "risk_score": risk_score,
            "risk_profile": risk_profile,
            "portfolio_risk_level": (
                portfolio_risk_level
            ),
            "alignment_status": (
                alignment["status"]
            ),
            "alignment_reason": (
                alignment["reason"]
            ),
            "score_breakdown": (
                score_breakdown
            ),
            "warnings": warnings,
        }

    def calculate_risk_score(
        self,
        investor: Dict[str, Any],
    ):

        components = []

        horizon_score = (
            self.score_horizon(
                investor[
                    "investment_horizon_years"
                ]
            )
        )

        appetite_score = {
            "low": 25,
            "medium": 60,
            "high": 90,
        }[
            investor[
                "risk_appetite"
            ].lower()
        ]

        loss_score = (
            self.score_loss_tolerance(
                investor[
                    "loss_tolerance_percent"
                ]
            )
        )

        capacity_score = (
            self.score_financial_capacity(
                investor[
                    "income_stability"
                ],
                investor[
                    "liquidity_need"
                ],
            )
        )

        experience_score = (
            self.score_experience(
                investor[
                    "investment_experience"
                ]
            )
        )

        components.append(
            self.create_component(
                "Investment Horizon",
                horizon_score,
                0.25,
            )
        )

        components.append(
            self.create_component(
                "Risk Appetite",
                appetite_score,
                0.25,
            )
        )

        components.append(
            self.create_component(
                "Loss Tolerance",
                loss_score,
                0.20,
            )
        )

        components.append(
            self.create_component(
                "Financial Capacity",
                capacity_score,
                0.20,
            )
        )

        components.append(
            self.create_component(
                "Investment Experience",
                experience_score,
                0.10,
            )
        )

        risk_score = sum(
            item["weighted_score"]
            for item in components
        )

        return (
            round(risk_score, 2),
            components,
        )

    @staticmethod
    def determine_risk_profile(
        score: float,
    ) -> str:

        if score < 40:
            return "Conservative"

        if score < 70:
            return "Moderate"

        return "Aggressive"

    @staticmethod
    def determine_portfolio_risk(
        analytics: Dict[str, Any],
    ) -> str:

        volatility = float(
            analytics.get(
                "annualized_volatility",
                0,
            )
        )

        largest_holding = float(
            analytics.get(
                "largest_holding_weight",
                0,
            )
        )

        largest_sector = float(
            analytics.get(
                "largest_sector_weight",
                0,
            )
        )

        score = 0

        score += (
            3 if volatility > 0.25
            else 2 if volatility > 0.15
            else 1
        )

        score += (
            3 if largest_holding > 0.30
            else 2 if largest_holding > 0.20
            else 1
        )

        score += (
            3 if largest_sector > 0.50
            else 2 if largest_sector > 0.35
            else 1
        )

        average = score / 3

        if average < 1.5:
            return "Conservative"

        if average < 2.5:
            return "Moderate"

        return "Aggressive"

    def check_alignment(
        self,
        investor_profile: str,
        portfolio_profile: str,
    ):

        difference = abs(
            self.PROFILE_ORDER[
                investor_profile
            ]
            -
            self.PROFILE_ORDER[
                portfolio_profile
            ]
        )

        if difference == 0:
            return {
                "status": "Aligned",
                "reason": (
                    "Portfolio risk aligns with "
                    "the investor profile."
                ),
            }

        if difference == 1:
            return {
                "status": "Partially Aligned",
                "reason": (
                    "Portfolio risk is slightly "
                    "different from the investor profile."
                ),
            }

        return {
            "status": "Not Aligned",
            "reason": (
                "Portfolio risk differs significantly "
                "from the investor profile."
            ),
        }

    def generate_warnings(
        self,
        analytics,
        investor_profile,
    ):

        warnings = []

        if (
            analytics.get(
                "largest_holding_weight",
                0,
            )
            > 0.25
        ):
            warnings.append(
                "Single holding exceeds 25%."
            )

        if (
            analytics.get(
                "largest_sector_weight",
                0,
            )
            > 0.40
        ):
            warnings.append(
                "Single sector exceeds 40%."
            )

        if (
            analytics.get(
                "annualized_volatility",
                0,
            )
            > 0.25
        ):
            warnings.append(
                "Portfolio volatility is high."
            )

        return warnings

    @staticmethod
    def score_horizon(
        years: int,
    ) -> float:

        if years < 3:
            return 20

        if years < 7:
            return 45

        if years < 15:
            return 70

        return 90

    @staticmethod
    def score_loss_tolerance(
        loss_percent: float,
    ) -> float:

        if loss_percent < 10:
            return 20

        if loss_percent < 20:
            return 45

        if loss_percent < 35:
            return 70

        return 90

    @staticmethod
    def score_financial_capacity(
        income_stability: str,
        liquidity_need: str,
    ) -> float:

        income_map = {
            "low": 25,
            "medium": 60,
            "high": 90,
            "stable": 80,
            "variable": 35,
        }

        liquidity_map = {
            "high": 20,
            "medium": 60,
            "low": 90,
        }

        return (
            income_map[
                income_stability.lower()
            ] * 0.6
            +
            liquidity_map[
                liquidity_need.lower()
            ] * 0.4
        )

    @staticmethod
    def score_experience(
        experience: str,
    ) -> float:

        mapping = {
            "beginner": 25,
            "intermediate": 60,
            "advanced": 90,
            "low": 25,
            "medium": 60,
            "high": 90,
        }

        return mapping[
            experience.lower()
        ]

    @staticmethod
    def create_component(
        name: str,
        score: float,
        weight: float,
    ):

        return {
            "component": name,
            "score": score,
            "weight": weight,
            "weighted_score": round(
                score * weight,
                2,
            ),
        }