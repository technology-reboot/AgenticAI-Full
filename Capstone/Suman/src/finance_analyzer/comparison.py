from .ratios import RatioEngine

class ComparisonAgent:
    def compare(self, records_a, records_b, period_a: str, period_b: str) -> dict:
        a = [r for r in records_a if r.period == period_a]
        b = [r for r in records_b if r.period == period_b]
        warnings = []
        currencies_a, currencies_b = {r.currency for r in a}, {r.currency for r in b}
        fy_a, fy_b = {r.fiscal_year_end for r in a}, {r.fiscal_year_end for r in b}
        if currencies_a != currencies_b: warnings.append(f"Currency mismatch: {currencies_a} vs {currencies_b}. Absolute values are not directly comparable.")
        if fy_a != fy_b: warnings.append(f"Fiscal-year-end mismatch: {fy_a} vs {fy_b}. Periods may not be aligned.")
        ra, rb = RatioEngine().compute(a), RatioEngine().compute(b)
        common = sorted(set(ra) & set(rb))
        return {"warnings": warnings, "rows": [{"ratio": k, "company_a": ra[k], "company_b": rb[k], "difference": ra[k]-rb[k]} for k in common]}
