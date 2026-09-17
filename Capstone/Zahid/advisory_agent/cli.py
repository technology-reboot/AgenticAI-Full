import argparse
import json
from dataclasses import asdict

from .models import AssetClass, Holding, Portfolio, RiskProfile, SimulationRequest
from agents.orchestrator import PortfolioAdvisorOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate grounded portfolio advice.")
    parser.add_argument("--risk", choices=[profile.value for profile in RiskProfile], required=True)
    parser.add_argument("--holding", action="append", required=True,
                        metavar="SYMBOL:ASSET_CLASS:VALUE",
                        help="Repeat for each holding, for example EQ:equities:7000")
    parser.add_argument("--monthly-contribution", type=float, default=0.0)
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument("--annual-return", type=float, default=0.05)
    return parser


def parse_holding(value: str) -> Holding:
    try:
        symbol, asset_class, amount = value.split(":")
        return Holding(symbol, AssetClass(asset_class), float(amount))
    except (ValueError, TypeError) as error:
        raise argparse.ArgumentTypeError(
            "holding must be SYMBOL:asset_class:value, such as EQ:equities:7000"
        ) from error


def main() -> None:
    args = build_parser().parse_args()
    portfolio = Portfolio(tuple(parse_holding(value) for value in args.holding))
    workflow = PortfolioAdvisorOrchestrator().run(
        portfolio,
        RiskProfile(args.risk),
        SimulationRequest(args.monthly_contribution, args.years, args.annual_return),
    )
    print(json.dumps(asdict(workflow), default=lambda item: item.value if hasattr(item, "value") else item, indent=2))


if __name__ == "__main__":
    main()
