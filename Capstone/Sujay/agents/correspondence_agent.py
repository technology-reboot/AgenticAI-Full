"""
Correspondence Agent - Toorubatla Upendra

Drafts a professional vendor dispute email citing the PO number and
specific discrepancy — always a draft for review, never auto-send.
"""

import json
from typing import Dict, List, Any, Optional


class CorrespondenceAgent:
    """
    Correspondence Agent - Toorubatla Upendra

    Drafts a professional vendor dispute email citing the PO number and
    specific discrepancy — always a draft for review, never auto-send.
    """

    def __init__(self):
        self.name = "correspondence_agent"
        self.version = "1.0.0"

    def draft_dispute_email(self, invoice_number: str, po_number: str,
                          discrepancy_type: str, amount: float,
                          description: str) -> Dict[str, str]:
        """
        Draft a professional vendor dispute email.

        Args:
            invoice_number: Invoice number with discrepancy
            po_number: Associated Purchase Order number
            discrepancy_type: Type of discrepancy
            amount: Amount involved
            description: Description of the discrepancy

        Returns:
            Dict with 'subject' and 'body' keys — always a draft
        """
        subject = f"Dispute Request - Invoice #{invoice_number} - PO #{po_number}"

        body = f"""Subject: {subject}

Dear Vendor,

This letter serves as a formal dispute request regarding Invoice #{invoice_number}
associated with Purchase Order PO {po_number}.

DISCREPANCY DETAILS:
• Invoice Number: {invoice_number}
• Purchase Order: PO {po_number}
• Discrepancy Type: {discrepancy_type}
• Amount in Dispute: ${amount:.2f}

DESCRIPTION:
{description}

REQUESTED ACTION:
Please review the above discrepancy and provide a resolution or
corrected invoice within 15 business days. Kindly reference the PO
number in all correspondence related to this matter.

If you believe this discrepancy is erroneous, please provide supporting
documentation (Purchase Order copy, delivery receipts, etc.) for our
review.

Should you have any questions, please contact our Accounts Payable
department.

Thank you for your prompt attention to this matter.

Sincerely,

Accounts Payable Department
"""

        return {
            "subject": subject,
            "body": body,
            "is_draft": True,
            "note": "This is a DRAFT for review only. Never auto-send. "
                    "Human review required before sending."
        }

    def draft_batch(self, disputes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Batch draft multiple dispute emails.

        Args:
            disputes: List of dispute dicts with invoice_number, po_number,
                      discrepancy_type, amount, description

        Returns:
            List of email dicts
        """
        return [self.draft_dispute_email(
            d["invoice_number"], d["po_number"],
            d["discrepancy_type"], d["amount"], d["description"]
        ) for d in disputes]