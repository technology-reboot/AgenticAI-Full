from finance_analyzer.models import MetricRecord
from finance_analyzer.ratios import RatioEngine
from finance_analyzer.red_flags import TrendRedFlagAgent

def rec(metric, value, period="FY2025"):
    return MetricRecord("Demo", period, "statement", metric, value, "INR", "million", "test.csv")

def test_ratios_are_deterministic():
    records = [rec("current_assets", 200), rec("current_liabilities", 100), rec("revenue", 1000), rec("net_income", 100), rec("total_debt", 300), rec("total_equity", 200)]
    r = RatioEngine().compute(records)
    assert r["current_ratio"] == 2
    assert r["net_margin"] == .1
    assert r["debt_to_equity"] == 1.5

def test_liquidity_flag():
    _, flags = TrendRedFlagAgent().evaluate({"current_ratio": .8}, {"current_ratio": 1.2})
    assert any(f["code"] == "LIQUIDITY_DETERIORATION" for f in flags)
