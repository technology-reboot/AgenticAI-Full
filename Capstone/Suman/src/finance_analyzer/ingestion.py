import io, re
from pathlib import Path
import pandas as pd
from pypdf import PdfReader
from .config import REQUIRED_COLUMNS, OPTIONAL_DEFAULTS, METRIC_ALIASES
from .models import MetricRecord

def canonical_metric(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()
    mapped = METRIC_ALIASES.get(cleaned, cleaned)
    return mapped.replace(" ", "_")

def _normalize(df: pd.DataFrame, source_name: str) -> list[MetricRecord]:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns: df[col] = default
    df["source_file"] = df["source_file"].replace({"": source_name}).fillna(source_name)
    df["metric"] = df["metric"].map(canonical_metric)
    df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", "", regex=False), errors="raise")
    records = []
    for row in df.to_dict("records"):
        records.append(MetricRecord(**{k: row[k] for k in MetricRecord.__dataclass_fields__}))
    return records

def parse_tabular(file_bytes: bytes, filename: str) -> list[MetricRecord]:
    ext = Path(filename).suffix.lower()
    if ext == ".csv": df = pd.read_csv(io.BytesIO(file_bytes))
    elif ext in {".xlsx", ".xlsm"}: df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    else: raise ValueError("Numeric statements must be CSV or XLSX.")
    return _normalize(df, filename)

def parse_narrative(file_bytes: bytes, filename: str) -> list[dict]:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return [{"text": p.extract_text() or "", "source_file": filename, "source_page": str(i + 1)}
                for i, p in enumerate(reader.pages) if (p.extract_text() or "").strip()]
    if ext == ".txt":
        return [{"text": file_bytes.decode("utf-8", errors="replace"), "source_file": filename, "source_page": ""}]
    raise ValueError("Narrative notes must be PDF or TXT.")
