import hashlib, json
import chromadb
from .models import MetricRecord

class GroundingStore:
    def __init__(self, path: str = ".chroma"):
        client = chromadb.PersistentClient(path=path)
        self.metrics = client.get_or_create_collection("financial_metrics")
        self.notes = client.get_or_create_collection("financial_notes")

    @staticmethod
    def _id(parts: list[str]) -> str:
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def index_metrics(self, records: list[MetricRecord]) -> None:
        if not records: return
        ids, docs, metadata = [], [], []
        for r in records:
            ids.append(self._id([r.company, r.period, r.metric, r.source_file, r.source_page]))
            docs.append(f"{r.company} {r.period} {r.metric} = {r.value} {r.currency} {r.unit}")
            metadata.append(r.metadata())
        self.metrics.upsert(ids=ids, documents=docs, metadatas=metadata)

    def index_notes(self, notes: list[dict], company: str, period: str) -> None:
        if not notes: return
        ids, docs, metas = [], [], []
        for n in notes:
            text = n["text"].strip()
            if not text: continue
            ids.append(self._id([company, period, n["source_file"], n["source_page"]]))
            docs.append(text)
            metas.append({"company": company, "period": period, "source_file": n["source_file"], "source_page": n["source_page"]})
        if ids: self.notes.upsert(ids=ids, documents=docs, metadatas=metas)

    def retrieve_exact_metrics(self, company: str, period: str, metrics: list[str]) -> list[MetricRecord]:
        """Retrieve known metrics by exact metadata filters, never semantic similarity."""
        if not metrics: return []
        result = self.metrics.get(where={"$and": [
            {"company": {"$eq": company}}, {"period": {"$eq": period}},
            {"metric": {"$in": metrics}},
        ]}, include=["metadatas"])
        return [MetricRecord(**{k: m[k] for k in MetricRecord.__dataclass_fields__}) for m in (result.get("metadatas") or [])]

    def all_metrics(self, company: str | None = None) -> list[MetricRecord]:
        result = self.metrics.get(where={"company": company} if company else None, include=["metadatas"])
        return [MetricRecord(**{k: m[k] for k in MetricRecord.__dataclass_fields__}) for m in (result.get("metadatas") or [])]

    def semantic_notes(self, question: str, company: str, period: str, n_results: int = 4) -> list[dict]:
        try:
            res = self.notes.query(query_texts=[question], n_results=n_results,
                where={"$and": [{"company": company}, {"period": period}]},
                include=["documents", "metadatas"])
            return [{"text": d, **m} for d, m in zip(res["documents"][0], res["metadatas"][0])]
        except Exception:
            return []
