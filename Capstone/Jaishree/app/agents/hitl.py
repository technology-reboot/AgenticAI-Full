from app.core.config import settings
from app.models.schemas import TransactionRecord, ExceptionItem, ApprovalDecision
class HITLRouter:
    def route(self,records:list[TransactionRecord],exceptions:list[ExceptionItem])->list[ApprovalDecision]:
        by_doc={r.document_id:r for r in records}; grouped={}
        for e in exceptions: grouped.setdefault(e.document_id,[]).append(e)
        decisions=[]
        for doc_id,r in by_doc.items():
            issues=grouped.get(doc_id,[]); risk=max([e.amount_at_risk for e in issues] or [0])
            human=bool(issues) or r.overall_confidence<settings.human_review_confidence or risk>settings.auto_clear_max_amount
            reasons=[]
            if issues: reasons.append("exceptions: "+", ".join(e.code for e in issues))
            if r.overall_confidence<settings.human_review_confidence: reasons.append("low extraction confidence")
            decisions.append(ApprovalDecision(document_id=doc_id,route="human_review" if human else "auto_clear",reason="; ".join(reasons) or "No exception and confidence is sufficient",amount_at_risk=risk))
        return decisions
