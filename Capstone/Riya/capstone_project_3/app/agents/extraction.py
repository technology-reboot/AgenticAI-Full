import re
from datetime import date
from dateutil import parser as dateparser
from app.models.schemas import TransactionRecord, FieldValue, IngestedDocument, LineItem

class ExtractionAgent:
    PATTERNS={
      "invoice_number":[r"invoice\s*(?:number|no\.?|#)\s*[:\-]?\s*([A-Z0-9\-/]+)"],
      "po_number": [r"(?:PO\s*Number|PO\s*No\.?|PO#|Purchase\s*Order\s*Number)\s*[:\-]?\s*([A-Z0-9\-\/]+)"],
      "total":[r"(?:grand\s+total|amount\s+due|total)\s*[:$₹€£ ]+([\d,]+(?:\.\d{1,2})?)"],
      "tax":[r"(?:tax|gst|vat)\s*[:$₹€£ ]+([\d,]+(?:\.\d{1,2})?)"],
      "date":[r"(?:invoice\s+date|date)\s*[:\-]?\s*([0-9A-Za-z, /\-]+)"],
      "vendor":[r"(?:vendor|supplier|from)\s*[:\-]?\s*([^\n|]{2,80})"]}
    def extract(self,d:IngestedDocument)->TransactionRecord:
        text=d.raw_text
        inv=self._field(text,"invoice_number"); po=self._field(text,"po_number")
        total=self._money(self._field(text,"total")); tax=self._money(self._field(text,"tax"))
        dt=self._field(text,"date"); vendor=self._field(text,"vendor")
        vals=[inv,po,total,tax,dt,vendor]; present=[x.confidence for x in vals if x.value is not None]
        return TransactionRecord(document_id=d.document_id,document_type=d.document_type,vendor_name=vendor,invoice_number=inv,po_number=po,transaction_date=self._date(dt),tax=tax,total=total,overall_confidence=round((sum(present)/len(present) if present else 0)*d.confidence,3))
    def _field(self,text,key):
        for p in self.PATTERNS[key]:
            m=re.search(p,text,re.I)
            if m: return FieldValue(value=m.group(1).strip(),confidence=.86)
        return FieldValue()
    @staticmethod
    def _money(v):
        if v.value is not None:
            try: v.value=float(str(v.value).replace(",",""))
            except ValueError: v.confidence=.2
        return v
    @staticmethod
    def _date(v):
        if v.value:
            try: v.value=dateparser.parse(str(v.value),fuzzy=True).date()
            except Exception: v.confidence=.2
        return v
