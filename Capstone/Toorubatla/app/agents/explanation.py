from app.models.schemas import ExceptionItem
class ExplanationAgent:
    def explain(self,e:ExceptionItem)->ExceptionItem:
        labels={"PO_NOT_FOUND":"No matching purchase order was found","AMOUNT_MISMATCH":"The invoice amount differs from the purchase order","VENDOR_MISMATCH":"The invoice vendor does not match the purchase order vendor","RECEIPT_NOT_FOUND":"No goods or service receipt was found","DUPLICATE_INVOICE":"The same vendor, invoice number, and amount appear more than once","POLICY_THRESHOLD":"The invoice exceeds the configured approval threshold","AMOUNT_OUTLIER":"The amount is unusually high compared with this batch"}
        base=labels.get(e.code,"A reconciliation exception was detected")
        detail=f". Expected: {e.expected}; found: {e.found}" if e.expected is not None or e.found is not None else "."
        e.explanation=base+detail+". Review the source documents before approval."
        return e
