from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class MetricRecord:
    company: str
    period: str
    statement: str
    metric: str
    value: float
    currency: str = "UNKNOWN"
    unit: str = "absolute"
    source_file: str = "upload"
    source_page: str = ""
    fiscal_year_end: str = "UNKNOWN"

    @property
    def citation(self) -> str:
        page = f", p.{self.source_page}" if self.source_page else ""
        return f"[{self.source_file}{page}; {self.company}; {self.period}; {self.metric}]"

    def metadata(self) -> dict:
        data = asdict(self)
        data["value"] = float(self.value)
        return data
