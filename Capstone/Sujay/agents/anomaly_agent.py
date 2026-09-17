"""
Anomaly Agent - Shivam Thaman

Independent of matching: detects duplicate invoices, statistical
outliers against vendor history, and policy breaches like above
threshold amounts.
"""

import json
import math
from collections import defaultdict
from typing import Dict, List, Any, Optional


class AnomalyType:
    """Types of anomalies that can be detected."""
    DUPLICATE_INVOICE = "duplicate_invoice"
    STATISTICAL_OUTLIER = "statistical_outlier"
    POLICY_BREACH = "policy_breach"
    THRESHOLD_AMOUNT = "threshold_amount"


class AnomalyResult:
    """Result of anomaly detection."""
    def __init__(self):
        self.anomalies = []
        self.summary = {
            "total_anomalies": 0,
            "by_type": defaultdict(int),
            "critical_count": 0
        }
        self.details = {}


class AnomalyAgent:
    """
    Anomaly Agent - Shivam Thaman

    Independent of matching: detects duplicate invoices, statistical
    outliers against vendor history, and policy breaches like above
    threshold amounts.
    """

    def __init__(self, threshold_amount: float = 1000.0, history_size: int = 10):
        """
        Initialize the AnomalyAgent.

        Args:
            threshold_amount: Amount threshold for policy breach detection
            history_size: Number of past transactions to consider for history
        """
        self.name = "anomaly_agent"
        self.version = "1.0.0"
        self.threshold_amount = threshold_amount
        self.history_size = history_size

    def detect_anomalies(self, invoices: List[Dict[str, Any]], vendor_history: Dict[str, List[Dict[str, Any]]] = None) -> AnomalyResult:
        """
        Detect anomalies in a list of invoices.

        Args:
            invoices: List of invoice dicts
            vendor_history: Optional dict of vendor -> list of past invoices

        Returns:
            AnomalyResult with detected anomalies
        """
        result = AnomalyResult()
        result.summary["total_anomalies"] = 0

        if not invoices:
            return result

        # Track seen invoice numbers for duplicate detection
        seen_invoice_numbers = set()
        invoice_by_number = defaultdict(list)

        for invoice in invoices:
            inv_num = invoice.get("invoice_number", "")
            amount = float(invoice.get("total_amount", 0) or 0)

            # 1. Duplicate invoice detection
            if inv_num in seen_invoice_numbers:
                anomaly = {
                    "type": AnomalyType.DUPLICATE_INVOICE,
                    "invoice_number": inv_num,
                    "amount": amount,
                    "description": f"Duplicate invoice number: {inv_num}",
                    "severity": "high"
                }
                result.anomalies.append(anomaly)
                result.summary["by_type"][AnomalyType.DUPLICATE_INVOICE] += 1
                result.summary["total_anomalies"] += 1
            else:
                seen_invoice_numbers.add(inv_num)
                invoice_by_number[inv_num].append(invoice)

            # 2. Threshold amount policy breach
            if amount > self.threshold_amount:
                anomaly = {
                    "type": AnomalyType.THRESHOLD_AMOUNT,
                    "invoice_number": inv_num,
                    "amount": amount,
                    "description": f"Invoice amount ${amount:.2f} exceeds threshold ${self.threshold_amount:.2f}",
                    "severity": "high"
                }
                result.anomalies.append(anomaly)
                result.summary["by_type"][AnomalyType.THRESHOLD_AMOUNT] += 1
                result.summary["total_anomalies"] += 1
                result.summary["critical_count"] += 1

            # 3. Statistical outlier detection (against vendor history)
            if vendor_history and inv_num in vendor_history:
                history = vendor_history[inv_num]
                if len(history) > 0:
                    historical_amounts = [float(h.get("total_amount", 0) or 0) for h in history]
                    avg_historical_amount = sum(historical_amounts) / len(historical_amounts)
                    std_dev = math.sqrt(sum((x - avg_historical_amount) ** 2 for x in historical_amounts) / len(historical_amounts))

                    if std_dev > 0:
                        z_score = (amount - avg_historical_amount) / std_dev
                        if abs(z_score) > 2.0:  # 2 standard deviations
                            anomaly = {
                                "type": AnomalyType.STATISTICAL_OUTLIER,
                                "invoice_number": inv_num,
                                "amount": amount,
                                "description": f"Statistical outlier: ${amount:.2f} vs historical avg ${avg_historical_amount:.2f} (z-score: {z_score:.2f})",
                                "severity": "medium" if abs(z_score) < 3.0 else "high"
                            }
                            result.anomalies.append(anomaly)
                            result.summary["by_type"][AnomalyType.STATISTICAL_OUTLIER] += 1
                            result.summary["total_anomalies"] += 1

        # Summary
        result.summary["by_type"] = dict(result.summary["by_type"])
        return result

    def detect_in_vendor_history(self, new_invoice: Dict[str, Any], vendor_history: List[Dict[str, Any]]) -> AnomalyResult:
        """
        Detect anomalies for a single invoice against vendor history.

        Args:
            new_invoice: The new invoice to check
            vendor_history: List of past invoices from same vendor

        Returns:
            AnomalyResult
        """
        result = AnomalyResult()

        if not vendor_history:
            return result

        amount = float(new_invoice.get("total_amount", 0) or 0)
        invoice_num = new_invoice.get("invoice_number", "")

        # Check for duplicates in history
        for hist_inv in vendor_history:
            hist_num = hist_inv.get("invoice_number", "")
            if hist_num == invoice_num:
                anomaly = {
                    "type": AnomalyType.DUPLICATE_INVOICE,
                    "invoice_number": invoice_num,
                    "amount": amount,
                    "description": "Duplicate invoice found in vendor history",
                    "severity": "high"
                }
                result.anomalies.append(anomaly)
                result.summary["total_anomalies"] += 1

        # Check threshold
        if amount > self.threshold_amount:
            anomaly = {
                "type": AnomalyType.THRESHOLD_AMOUNT,
                "invoice_number": invoice_num,
                "amount": amount,
                "description": f"Amount ${amount:.2f} exceeds threshold ${self.threshold_amount:.2f}",
                "severity": "high"
            }
            result.anomalies.append(anomaly)
            result.summary["critical_count"] += 1

        result.summary["by_type"] = {"threshold_amount": len(result.anomalies)}
        return result