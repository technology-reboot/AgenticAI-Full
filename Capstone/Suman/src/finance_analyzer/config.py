REQUIRED_COLUMNS = {"company", "period", "statement", "metric", "value"}
OPTIONAL_DEFAULTS = {
    "currency": "UNKNOWN", "unit": "absolute", "source_file": "upload",
    "source_page": "", "fiscal_year_end": "UNKNOWN"
}
THRESHOLDS = {
    "accrual_gap": 0.10, "dso_increase": 0.10, "margin_drop": 0.02,
    "debt_equity_high": 2.0, "debt_equity_increase": 0.25,
    "inventory_days_increase": 0.15, "current_ratio_low": 1.0,
    "current_ratio_decline": 0.20,
}
METRIC_ALIASES = {
    "sales": "revenue", "net sales": "revenue", "turnover": "revenue",
    "cogs": "cost_of_goods_sold", "cost of sales": "cost_of_goods_sold",
    "profit after tax": "net_income", "pat": "net_income",
    "trade receivables": "accounts_receivable", "receivables": "accounts_receivable",
    "trade payables": "accounts_payable", "borrowings": "total_debt",
    "shareholders equity": "total_equity", "cash from operations": "operating_cash_flow",
}
