from pathlib import Path
from app.agents.ingestion import IngestionAgent
from app.agents.extraction import ExtractionAgent
from app.agents.matching import MatchingAgent
from app.agents.anomaly import AnomalyAgent
from app.agents.explanation import ExplanationAgent
from app.agents.hitl import HITLRouter
from app.agents.correspondence import CorrespondenceAgent
from app.models.schemas import ReconciliationResponse, DocumentType

class ReconciliationPipeline:
    def __init__(self):
        self.ingestion=IngestionAgent(); self.extraction=ExtractionAgent(); self.matching=MatchingAgent(); self.anomaly=AnomalyAgent(); self.explanation=ExplanationAgent(); self.hitl=HITLRouter(); self.correspondence=CorrespondenceAgent()
    def run(self,paths:list[Path])->ReconciliationResponse:
        documents=[self.ingestion.ingest(p) for p in paths]
        records=[self.extraction.extract(d) for d in documents if d.status=="success"]
        exceptions=[self.explanation.explain(e) for e in self.matching.match(records)+self.anomaly.detect(records)]
        decisions=self.hitl.route(records,exceptions); emails=[]
        by_doc={r.document_id:r for r in records}
        for d in decisions:
            issues=[e for e in exceptions if e.document_id==d.document_id]
            r=by_doc[d.document_id]
            if d.route=="human_review" and issues and r.document_type==DocumentType.invoice: emails.append(self.correspondence.draft(r,issues))
        return ReconciliationResponse(documents=documents,records=records,exceptions=exceptions,decisions=decisions,vendor_emails=emails)
