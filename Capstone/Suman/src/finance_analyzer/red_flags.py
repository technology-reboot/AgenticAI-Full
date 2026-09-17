from .config import THRESHOLDS

class TrendRedFlagAgent:
    @staticmethod
    def _pct(curr, prev): return None if prev in (None, 0) or curr is None else (curr - prev) / abs(prev)

    def evaluate(self, current: dict, previous: dict) -> tuple[dict, list[dict]]:
        deltas = {k: self._pct(v, previous.get(k)) for k, v in current.items() if k in previous}
        flags = []
        def add(code, severity, message): flags.append({"code": code, "severity": severity, "message": message})
        aq = current.get("accrual_quality_gap")
        if aq is not None and aq > THRESHOLDS["accrual_gap"]: add("ACCRUAL_QUALITY_GAP", "high", f"Accrual gap is {aq:.1%} of average assets.")
        if deltas.get("dso_days") is not None and deltas["dso_days"] > THRESHOLDS["dso_increase"]: add("DSO_CLIMBING", "medium", f"DSO increased {deltas['dso_days']:.1%}.")
        if current.get("operating_margin") is not None and previous.get("operating_margin") is not None and previous["operating_margin"] - current["operating_margin"] > THRESHOLDS["margin_drop"]: add("MARGIN_COMPRESSION", "high", "Operating margin fell by more than 2 percentage points.")
        de = current.get("debt_to_equity")
        if (de is not None and de > THRESHOLDS["debt_equity_high"]) or (deltas.get("debt_to_equity") is not None and deltas["debt_to_equity"] > THRESHOLDS["debt_equity_increase"]): add("LEVERAGE_STRESS", "high", "Debt-to-equity is high or rising sharply.")
        if deltas.get("inventory_days") is not None and deltas["inventory_days"] > THRESHOLDS["inventory_days_increase"]: add("INVENTORY_BUILD_UP", "medium", f"Inventory days increased {deltas['inventory_days']:.1%}.")
        cr = current.get("current_ratio")
        if (cr is not None and cr < THRESHOLDS["current_ratio_low"]) or (deltas.get("current_ratio") is not None and deltas["current_ratio"] < -THRESHOLDS["current_ratio_decline"]): add("LIQUIDITY_DETERIORATION", "high", "Current ratio is below 1.0 or deteriorated by more than 20%.")
        return deltas, flags
