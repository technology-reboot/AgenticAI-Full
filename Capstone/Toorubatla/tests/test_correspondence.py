import os

from app.agents.correspondence import CorrespondenceAgent
from app.models.schemas import ExceptionItem, FieldValue, TransactionRecord


def record(**overrides):
    values = {
        "document_id": "doc-1",
        "document_type": "invoice",
        "vendor_name": FieldValue(value="Dell"),
        "invoice_number": FieldValue(value="INV-1001"),
        "po_number": FieldValue(value="PO-5001"),
        "total": FieldValue(value=55000.0),
    }
    values.update(overrides)
    return TransactionRecord(**values)


def issue(code="AMOUNT_MISMATCH", **overrides):
    values = {
        "code": code,
        "severity": "high",
        "document_id": "doc-1",
        "expected": 50000.0,
        "found": 55000.0,
        "amount_at_risk": 5000.0,
        "explanation": "The invoice amount differs from the purchase order.",
    }
    values.update(overrides)
    return ExceptionItem(**values)


def agent_without_ai():
    os.environ.pop("OPENAI_API_KEY", None)
    return CorrespondenceAgent()


def test_amount_mismatch_draft_contains_specific_values():
    draft = agent_without_ai().draft(record(), [issue()])

    assert "INV-1001" in draft
    assert "PO-5001" in draft
    assert "Dell" in draft
    assert "Purchase order amount: $50,000.00" in draft
    assert "Invoice amount: $55,000.00" in draft
    assert "Difference: $5,000.00" in draft
    assert "requires human approval before sending" in draft


def test_missing_values_are_not_invented():
    draft = agent_without_ai().draft(
        record(
            vendor_name=FieldValue(),
            invoice_number=FieldValue(),
            po_number=FieldValue(),
        ),
        [issue("PO_NOT_FOUND", expected=None, found=None, amount_at_risk=0)],
    )

    assert "[invoice number]" in draft
    assert "[PO number]" in draft
    assert "Dear Vendor Team" in draft
    assert "Not available in the extracted records" in draft


def test_vendor_mismatch_and_multiple_issues_are_included():
    draft = agent_without_ai().draft(
        record(),
        [
            issue("VENDOR_MISMATCH", expected="Dell", found="Other Supplies"),
            issue("DUPLICATE_INVOICE", expected=None, found="INV-1001"),
        ],
    )

    assert "Purchase order vendor: Dell" in draft
    assert "Invoice vendor: Other Supplies" in draft
    assert "Invoice reference reported as duplicate: INV-1001" in draft
    assert "Invoice rejected" not in draft