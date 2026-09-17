"""
Explanation Agent - Sujay Kumar

Turns each exception into a plain-language explanation a finance clerk
can act on, citing the actual expected vs. found amounts.
"""

import re
from typing import Dict, List, Any, Optional


class ExplanationAgent:
    """
    Explanation Agent - Sujay Kumar

    Turns each exception into a plain-language explanation a finance clerk
    can act on, citing the actual expected vs. found amounts.
    """

    def __init__(self):
        self.name = "explanation_agent"
        self.version = "1.0.0"

    def explain_exception(self, exception: Dict[str, Any]) -> str:
        """
        Convert an exception dict into plain-language explanation.

        Args:
            exception: Exception dict from matching or anomaly agent

        Returns:
            Plain-language explanation string
        """
        exc_type = exception.get("type", "unknown")
        invoice_num = exception.get("invoice_number", "N/A")
        amount = exception.get("amount", 0)
        description = exception.get("description", "")
        percent_diff = exception.get("percent_difference", 0)
        tolerance = exception.get("tolerance", 0)

        if exc_type == "po_invoice_amount":
            return self._explain_po_invoice_amount(amount, percent_diff, tolerance)
        elif exc_type == "invoice_receipt_amount":
            return self._explain_invoice_receipt_amount(amount, percent_diff)
        elif exc_type == "po_receipt_amount":
            return self._explain_po_receipt_amount(amount, percent_diff)
        elif exc_type == "duplicate_invoice":
            return self._explain_duplicate_invoice(invoice_num)
        elif exc_type == "threshold_amount":
            return self._explain_threshold_amount(amount)
        elif exc_type == "statistical_outlier":
            return self._explain_statistical_outlier(amount)
        else:
            return f"Exception {invoice_num}: {description}. Amount: ${amount:.2f}."

    def _explain_po_invoice_amount(self, amount: float, percent_diff: float, tolerance: float) -> str:
        """Explain PO vs Invoice amount mismatch."""
        if percent_diff <= tolerance:
            return (f"PO ${amount:.2f} matches Invoice ${amount:.2f} within {tolerance:.1f}% tolerance. "
                    "No action required.")
        else:
            over_or_under = "over" if percent_diff > 0 else "under"
            return (f"PO amount ${amount:.2f} is {over_or_under} by {percent_diff:.1f}% "
                    f"versus Invoice ${amount:.2f}. Requires review and possible "
                    f"adjustment or PO revision.")

    def _explain_invoice_receipt_amount(self, amount: float, percent_diff: float) -> str:
        """Explain Invoice vs Receipt amount mismatch."""
        over_or_under = "over" if percent_diff > 0 else "under"
        return (f"Invoice amount ${amount:.2f} is {over_or_under} by {percent_diff:.1f}% "
                f"versus Receipt ${amount:.2f}. Check for: missing items, "
                f"pricing errors, or data entry errors.")

    def _explain_po_receipt_amount(self, amount: float, percent_diff: float) -> str:
        """Explain PO vs Receipt amount mismatch."""
        over_or_under = "over" if percent_diff > 0 else "under"
        return (f"PO amount ${amount:.2f} is {over_or_under} by {percent_diff:.1f}% "
                f"versus Receipt ${amount:.2f}. Verify: goods received, "
                f"pricing agreements, or delivery discrepancies.")

    def _explain_duplicate_invoice(self, invoice_num: str) -> str:
        """Explain duplicate invoice detection."""
        return (f"DUPLICATE INVOICE: Invoice #{invoice_num} appears more than once. "
                "Verify which is the legitimate invoice. Cancel or merge as appropriate. "
                "Do not pay duplicate amounts.")

    def _explain_threshold_amount(self, amount: float) -> str:
        """Explain threshold amount breach."""
        return (f"POLICY BREACH: Invoice amount ${amount:.2f} exceeds "
                f"approval threshold ${self.threshold_amount:.2f}. Requires "
                f"senior approval before processing.")

    def _explain_statistical_outlier(self, amount: float) -> str:
        """Explain statistical outlier."""
        return (f"ANOMALY: Invoice amount ${amount:.2f} is a statistical "
                f"outlier compared to vendor's historical pricing. Requires "
                f"investigation to verify pricing accuracy or terms change.")

    def batch_explain(self, exceptions: List[Dict[str, Any]]) -> List[str]:
        """
        Batch explain multiple exceptions.

        Args:
            exceptions: List of exception dicts

        Returns:
            List of plain-language explanations
        """
        return [self.explain_exception(exc) for exc in exceptions]