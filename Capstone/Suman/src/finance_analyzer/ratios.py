from collections import defaultdict
from .models import MetricRecord

class RatioEngine:
    def _map(self, records): return {r.metric: r for r in records}
    @staticmethod
    def _safe(a, b): return None if a is None or b in (None, 0) else a / b
    @staticmethod
    def _v(m, key): return m[key].value if key in m else None

    def compute(self, records: list[MetricRecord], previous: list[MetricRecord] | None = None) -> dict:
        m, p = self._map(records), self._map(previous or [])
        v = lambda k: self._v(m, k)
        avg = lambda k: (v(k) + self._v(p, k)) / 2 if v(k) is not None and self._v(p, k) is not None else v(k)
        ratios = {
            "current_ratio": self._safe(v("current_assets"), v("current_liabilities")),
            "quick_ratio": self._safe((v("cash_and_equivalents") or 0) + (v("accounts_receivable") or 0), v("current_liabilities")),
            "debt_to_equity": self._safe(v("total_debt"), v("total_equity")),
            "debt_to_assets": self._safe(v("total_debt"), v("total_assets")),
            "gross_margin": self._safe(v("gross_profit"), v("revenue")),
            "operating_margin": self._safe(v("operating_income"), v("revenue")),
            "net_margin": self._safe(v("net_income"), v("revenue")),
            "return_on_assets": self._safe(v("net_income"), avg("total_assets")),
            "return_on_equity": self._safe(v("net_income"), avg("total_equity")),
            "dso_days": (self._safe(avg("accounts_receivable"), v("revenue")) or 0) * 365 if v("revenue") else None,
            "inventory_days": (self._safe(avg("inventory"), v("cost_of_goods_sold")) or 0) * 365 if v("cost_of_goods_sold") else None,
            "accrual_quality_gap": self._safe((v("net_income") - v("operating_cash_flow")) if v("net_income") is not None and v("operating_cash_flow") is not None else None, avg("total_assets")),
        }
        return {k: val for k, val in ratios.items() if val is not None}
