from app.models.schemas import TransactionRecord, ExceptionItem
class CorrespondenceAgent:
    def draft(self,r:TransactionRecord,issues:list[ExceptionItem])->str:
        summary="\n".join(f"- {e.explanation}" for e in issues)
        return f"""Subject: Clarification required for invoice {r.invoice_number.value or '[invoice number]'} / PO {r.po_number.value or '[PO number]'}

Dear {r.vendor_name.value or 'Vendor'} Team,

During reconciliation, we identified the following item(s):
{summary}

Please review and provide the corrected document or supporting information. No payment decision has been made while this review is open.

Regards,
Accounts Payable Team"""
