from __future__ import annotations
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    invoice="invoice"; purchase_order="purchase_order"; receipt="receipt"; bank_statement="bank_statement"; unknown="unknown"
class ExtractionMethod(str, Enum):
    pdf_text="pdf_text"; pdf_ocr="pdf_ocr"; image_ocr="image_ocr"; csv="csv"
class ProcessingStatus(str, Enum):
    success="success"; failed="failed"

class IngestedDocument(BaseModel):
    document_id: str
    file_name: str
    mime_type: str
    document_type: DocumentType
    extraction_method: ExtractionMethod
    raw_text: str = ""
    tables: list[list[dict[str, Any]]] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    sha256: str
    page_count: int | None = None
    status: ProcessingStatus = ProcessingStatus.success
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FieldValue(BaseModel):
    value: str | float | date | None = None
    confidence: float = Field(default=0, ge=0, le=1)

class LineItem(BaseModel):
    description: str = ""
    quantity: float = 0
    unit_price: float = 0
    amount: float = 0

class TransactionRecord(BaseModel):
    document_id: str
    document_type: DocumentType
    vendor_name: FieldValue = Field(default_factory=FieldValue)
    invoice_number: FieldValue = Field(default_factory=FieldValue)
    po_number: FieldValue = Field(default_factory=FieldValue)
    transaction_date: FieldValue = Field(default_factory=FieldValue)
    subtotal: FieldValue = Field(default_factory=FieldValue)
    tax: FieldValue = Field(default_factory=FieldValue)
    total: FieldValue = Field(default_factory=FieldValue)
    currency: FieldValue = Field(default_factory=lambda: FieldValue(value="USD", confidence=.4))
    line_items: list[LineItem] = Field(default_factory=list)
    overall_confidence: float = 0

class ExceptionItem(BaseModel):
    code: str
    severity: str
    document_id: str
    expected: Any = None
    found: Any = None
    amount_at_risk: float = 0
    explanation: str = ""

class ApprovalDecision(BaseModel):
    document_id: str
    route: str
    reason: str
    amount_at_risk: float = 0
    decided_by: str = "system"

class ReviewRequest(BaseModel):
    document_id: str
    decision: Literal["approve", "reject", "request_clarification"]
    reason: str = ""
    decided_by: str = "human_reviewer"


class VendorEmailDraft(BaseModel):
    subject: str
    body: str
    requires_human_approval: bool = True

class ReconciliationResponse(BaseModel):
    documents: list[IngestedDocument]
    records: list[TransactionRecord]
    exceptions: list[ExceptionItem]
    decisions: list[ApprovalDecision]
    vendor_emails: list[str]
