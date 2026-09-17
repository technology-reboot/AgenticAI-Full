from app.models.schemas import DocumentType

def classify(text: str, file_name: str, is_csv: bool=False) -> tuple[DocumentType,float]:
    s=(file_name+"\n"+text[:10000]).lower()
    scores={
      DocumentType.purchase_order: sum(k in s for k in ["purchase order","po number","po #","ship to"]),
      DocumentType.invoice: sum(k in s for k in ["invoice","invoice number","bill to","amount due"]),
      DocumentType.receipt: sum(k in s for k in ["receipt","paid","payment receipt","thank you"]),
      DocumentType.bank_statement: sum(k in s for k in ["bank statement","transaction date","debit","credit","balance"])+(2 if is_csv else 0),
    }
    kind,score=max(scores.items(), key=lambda x:x[1])
    return (kind, min(.55+.12*score,.99)) if score else (DocumentType.unknown,.25)
