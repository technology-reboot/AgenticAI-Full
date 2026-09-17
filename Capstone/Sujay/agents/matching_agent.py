"""
Matching Agent - Sambhaji S Pandhare

Performs the three-way match (PO invoice receipt) with configurable
tolerances and fuzzy vendor matching. Deterministic Python, no LLM—
this has to be auditable.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class MatchResult:
    """Result of a three-way match operation."""
    MATCH = "match"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    NO_MATCH = "no_match"


class AmountTolerance:
    """Tolerance configuration for amount matching."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class MatchingAgent:
    """
    Matching Agent - Sambhaji S Pandhare

    Performs the three-way match (PO invoice receipt) with configurable
    tolerances and fuzzy vendor matching. Deterministic Python, no LLM—
    this has to be auditable.
    """

    def __init__(self,po_tolerance: float = 2.0, invoice_tolerance: float = 5.0, receipt_tolerance: float = 5.0,
                 vendor_fuzzy_threshold: float = 0.8):
        """
        Initialize the MatchingAgent.

        Args:
            po_tolerance: Tolerance for PO amount matching (percentage)
            invoice_tolerance: Tolerance for invoice amount matching (percentage)
            receipt_tolerance: Tolerance for receipt amount matching (percentage)
            vendor_fuzzy_threshold: Similarity threshold for fuzzy vendor matching (0-1)
        """
        self.name = "matching_agent"
        self.version = "1.0.0"
        self.po_tolerance = po_tolerance
        self.invoice_tolerance = invoice_tolerance
        self.receipt_tolerance = receipt_tolerance
        self.vendor_fuzzy_threshold = vendor_fuzzy_threshold

    def three_way_match(self, po_data: Dict[str, Any], invoice_data: Dict[str, Any],
                        receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform three-way match: PO vs Invoice vs Receipt.

        Args:
            po_data: Purchase Order data dict
            invoice_data: Invoice data dict
            receipt_data: Receipt data dict

        Returns:
            Dict with match result and details
        """
        results = {
            "overall_status": MatchResult.NO_MATCH,
            "po_invoice_match": MatchResult.NO_MATCH,
            "invoice_receipt_match": MatchResult.NO_MATCH,
            "po_receipt_match": MatchResult.NO_MATCH,
            "discrepancies": [],
            "matched_amounts": {},
            "fuzzy_vendor_match": False
        }

        try:
            po_amount = float(po_data.get("total_amount", 0) or 0)
            invoice_amount = float(invoice_data.get("total_amount", 0) or 0)
            receipt_amount = float(receipt_data.get("total_amount", 0) or 0)

            # PO vs Invoice match
            po_inv_diff = abs(po_amount - invoice_amount)
            po_inv_percent_diff = (po_inv_diff / po_amount * 100) if po_amount > 0 else 0

            if po_inv_percent_diff <= self.po_tolerance:
                results["po_invoice_match"] = MatchResult.MATCH
                results["matched_amounts"]["po_invoice"] = invoice_amount
            else:
                results["discrepancies"].append({
                    "type": "po_invoice_amount",
                    "po_amount": po_amount,
                    "invoice_amount": invoice_amount,
                    "difference": po_inv_diff,
                    "percent_difference": po_inv_percent_diff,
                    "tolerance": self.po_tolerance
                })

            # Invoice vs Receipt match
            inv_rec_diff = abs(invoice_amount - receipt_amount)
            inv_rec_percent_diff = (inv_rec_diff / invoice_amount * 100) if invoice_amount > 0 else 0

            if inv_rec_percent_diff <= self.invoice_tolerance:
                results["invoice_receipt_match"] = MatchResult.MATCH
                results["matched_amounts"]["invoice_receipt"] = receipt_amount
            else:
                results["discrepancies"].append({
                    "type": "invoice_receipt_amount",
                    "invoice_amount": invoice_amount,
                    "receipt_amount": receipt_amount,
                    "difference": inv_rec_diff,
                    "percent_difference": inv_rec_percent_diff,
                    "tolerance": self.invoice_tolerance
                })

            # PO vs Receipt match
            po_rec_diff = abs(po_amount - receipt_amount)
            po_rec_percent_diff = (po_rec_diff / po_amount * 100) if po_amount > 0 else 0

            if po_rec_percent_diff <= self.receipt_tolerance:
                results["po_receipt_match"] = MatchResult.MATCH
                results["matched_amounts"]["po_receipt"] = receipt_amount
            else:
                results["discrepancies"].append({
                    "type": "po_receipt_amount",
                    "po_amount": po_amount,
                    "receipt_amount": receipt_amount,
                    "difference": po_rec_diff,
                    "percent_difference": po_rec_percent_diff,
                    "tolerance": self.receipt_tolerance
                })

            # Fuzzy vendor matching
            po_vendor = po_data.get("vendor_name", "").lower()
            inv_vendor = invoice_data.get("vendor_name", "").lower()
            rec_vendor = receipt_data.get("vendor_name", "").lower()

            vendor_similarity = self._calculate_string_similarity(po_vendor, inv_vendor)
            if vendor_similarity >= self.vendor_fuzzy_threshold:
                results["fuzzy_vendor_match"] = True

            # Overall status
            if (results["po_invoice_match"] == MatchResult.MATCH and
                results["invoice_receipt_match"] == MatchResult.MATCH):
                results["overall_status"] = MatchResult.MATCH
            elif len(results["discrepancies"]) > 0:
                results["overall_status"] = MatchResult.MISMATCH
            else:
                results["overall_status"] = MatchResult.PARTIAL

        except (ValueError, TypeError, KeyError) as e:
            results["error"] = str(e)

        return results

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Jaro-Winkler-like approach.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0

        # Simple similarity: overlap of characters
        set1 = set(str1.lower())
        set2 = set(str2.lower())

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def match_invoice_to_po(self, invoice: Dict[str, Any], po: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a single invoice to a purchase order.

        Args:
            invoice: Invoice data dict
            po: Purchase Order data dict

        Returns:
            Match result dict
        """
        return self.three_way_match(po, invoice, {
            "total_amount": invoice.get("total_amount", 0),
            "vendor_name": invoice.get("vendor_name", "")
        })

    def match_receipt_to_invoice(self, receipt: Dict[str, Any], invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a receipt to an invoice.

        Args:
            receipt: Receipt data dict
            invoice: Invoice data dict

        Returns:
            Match result dict
        """
        return self.three_way_match(
            {"total_amount": invoice.get("total_amount", 0), "vendor_name": invoice.get("vendor_name", "")},
            invoice,
            {"total_amount": receipt.get("total_amount", 0), "vendor_name": receipt.get("vendor_name", "")}
        )