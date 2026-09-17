from collections import defaultdict
from app.models.schemas import TransactionRecord, DocumentType, ExceptionItem

class AnomalyAgent:
    def detect(self,records:list[TransactionRecord])->list[ExceptionItem]:
        out=[]; seen=defaultdict(list)
        invoices=[r for r in records if r.document_type==DocumentType.invoice]
        for r in invoices:
            key=(str(r.vendor_name.value or "").lower(),str(r.invoice_number.value or "").lower(),float(r.total.value or 0))
            if key[1]: seen[key].append(r)
            if float(r.total.value or 0)>100000:
                out.append(ExceptionItem(code="POLICY_THRESHOLD",severity="high",document_id=r.document_id,expected="<= 100000",found=r.total.value,amount_at_risk=float(r.total.value or 0)))
        for group in seen.values():
            if len(group)>1:
                for r in group: out.append(ExceptionItem(code="DUPLICATE_INVOICE",severity="high",document_id=r.document_id,found=r.invoice_number.value,amount_at_risk=float(r.total.value or 0)))
        amounts=[float(r.total.value) for r in invoices if r.total.value]
        if len(amounts)>=4:
            q1,q3=sorted(amounts)[len(amounts)//4],sorted(amounts)[3*len(amounts)//4]; upper=q3+1.5*(q3-q1)
            for r in invoices:
                if r.total.value and float(r.total.value)>upper: out.append(ExceptionItem(code="AMOUNT_OUTLIER",severity="medium",document_id=r.document_id,expected=f"<= {upper:.2f}",found=r.total.value,amount_at_risk=float(r.total.value)))
        return out
