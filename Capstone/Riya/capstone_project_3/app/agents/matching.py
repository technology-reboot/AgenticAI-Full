from rapidfuzz.fuzz import ratio
from app.core.config import settings
from app.models.schemas import TransactionRecord, DocumentType, ExceptionItem

class MatchingAgent:
    def match(self,records:list[TransactionRecord])->list[ExceptionItem]:
        invoices=[r for r in records if r.document_type==DocumentType.invoice]
        pos=[r for r in records if r.document_type==DocumentType.purchase_order]
        receipts=[r for r in records if r.document_type==DocumentType.receipt]
        out=[]
        for inv in invoices:
            po=self._best_po(inv,pos)
            if not po:
                out.append(ExceptionItem(code="PO_NOT_FOUND",severity="high",document_id=inv.document_id,found=inv.po_number.value,amount_at_risk=float(inv.total.value or 0)))
                continue
            if inv.total.value is not None and po.total.value is not None and abs(float(inv.total.value)-float(po.total.value))>settings.amount_tolerance:
                out.append(ExceptionItem(code="AMOUNT_MISMATCH",severity="high",document_id=inv.document_id,expected=po.total.value,found=inv.total.value,amount_at_risk=abs(float(inv.total.value)-float(po.total.value))))
            if inv.vendor_name.value and po.vendor_name.value and ratio(str(inv.vendor_name.value),str(po.vendor_name.value))<80:
                out.append(ExceptionItem(code="VENDOR_MISMATCH",severity="medium",document_id=inv.document_id,expected=po.vendor_name.value,found=inv.vendor_name.value))
            if not receipts:
                out.append(ExceptionItem(code="RECEIPT_NOT_FOUND",severity="medium",document_id=inv.document_id,found=inv.invoice_number.value,amount_at_risk=float(inv.total.value or 0)))
        return out
    @staticmethod
    def _best_po(inv,pos):
        exact=[p for p in pos if inv.po_number.value and str(inv.po_number.value)==str(p.po_number.value)]
        return exact[0] if exact else (pos[0] if len(pos)==1 else None)
