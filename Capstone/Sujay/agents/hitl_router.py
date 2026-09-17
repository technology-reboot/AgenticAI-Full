"""
HITL Router - Riya Patil

Decides auto-clear vs. human queue using confidence, severity and
amount at risk; builds the approval queue and records decisions
back into state.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class HITLDecision:
    """Decision types for HITL router."""
    AUTO_CLEAR = "auto_clear"
    HUMAN_QUEUE = "human_queue"
    REJECT = "reject"


class HITLRouter:
    """
    HITL Router - Riya Patil

    Decides auto-clear vs. human queue using confidence, severity and
    amount at risk; builds the approval queue and records decisions
    back into state.
    """

    def __init__(self, confidence_cutoff: float = 0.7, severity_cutoff: str = "medium",
                 amount_cutoff: float = 1000.0):
        """
        Initialize the HITLRouter.

        Args:
            confidence_cutoff: Minimum confidence score for auto-clear (0-1)
            severity_cutoff: Minimum severity level for human queue
            amount_cutoff: Amount threshold above which human review required
        """
        self.name = "hitl_router"
        self.version = "1.0.0"
        self.confidence_cutoff = confidence_cutoff
        self.severity_cutoff = severity_cutoff
        self.amount_cutoff = amount_cutoff

    def decide(self, exception: Dict[str, Any], confidence_score: float,
               severity: str = "medium", amount: float = 0.0) -> Dict[str, Any]:
        """
        Decide auto-clear vs. human queue for an exception.

        Args:
            exception: Exception dict from matching/anomaly agent
            confidence_score: Agent confidence score (0-1)
            severity: Severity level (low, medium, high, critical)
            amount: Amount at risk

        Returns:
            Dict with decision and reasoning
        """
        decision = {
            "decision": HITLDecision.HUMAN_QUEUE,  # Default to human queue
            "reason": "",
            "record_for_state": {
                "exception_type": exception.get("type", "unknown"),
                "invoice_number": exception.get("invoice_number", "N/A"),
                "confidence_score": confidence_score,
                "severity": severity,
                "amount": amount
            }
        }

        # Auto-clear if ALL of: high confidence, low severity, low amount
        if (confidence_score >= self.confidence_cutoff and
                severity.lower() == "low" and
                amount < self.amount_cutoff):
            decision["decision"] = HITLDecision.AUTO_CLEAR
            decision["reason"] = (f"Auto-clear: High confidence ({confidence_score:.2f}), "
                                  f"low severity, low amount (${amount:.2f})")
        elif (confidence_score >= 0.5 and
              severity.lower() == "medium" and
              amount < self.amount_cutoff):
            # Medium confidence + medium severity + low amount = human queue
            decision["decision"] = HITLDecision.HUMAN_QUEUE
            decision["reason"] = (f"Human queue: Medium confidence ({confidence_score:.2f}), "
                                  f"medium severity, amount ${amount:.2f} under threshold")
        else:
            # Otherwise human queue
            decision["decision"] = HITLDecision.HUMAN_QUEUE
            if amount >= self.amount_cutoff:
                decision["reason"] = (f"Human queue: Amount ${amount:.2f} exceeds "
                                     f"threshold ${self.amount_cutoff:.2f}")
            elif severity.lower() == "high" or severity.lower() == "critical":
                decision["reason"] = (f"Human queue: Severity {severity} "
                                      f"requires human review")
            else:
                decision["reason"] = (f"Human queue: Exception requires "
                                      f"review (confidence={confidence_score:.2f})")

        # Update record for state
        decision["record_for_state"].update({
            "decision": decision["decision"],
            "reason": decision["reason"],
            "confidence_score": confidence_score,
            "severity": severity,
            "amount": amount
        })

        return decision

    def build_approval_queue(self, exceptions: List[Dict[str, Any]],
                             confidence_scores: List[float],
                             severities: List[str],
                             amounts: List[float]) -> List[Dict[str, Any]]:
        """
        Build approval queue from list of exceptions.

        Args:
            exceptions: List of exception dicts
            confidence_scores: Corresponding confidence scores
            severities: Corresponding severity levels
            amounts: Corresponding amounts at risk

        Returns:
            List of dicts with decision and exception info
        """
        queue = []

        for i, exc in enumerate(exceptions):
            # Ensure lists are aligned
            idx = min(i, len(confidence_scores) - 1 if confidence_scores else 0,
                      len(severities) - 1 if severities else 0,
                      len(amounts) - 1 if amounts else 0)
            cs = confidence_scores[idx] if confidence_scores and i < len(confidence_scores) else 0.9
            sev = severities[idx] if severities and i < len(severities) else "medium"
            amt = amounts[idx] if amounts and i < len(amounts) else 0.0

            d = self.decide(exc, cs, sev, amt)
            queue.append({
                "exception": exc,
                "decision": d["decision"],
                "reason": d["reason"],
                "invoice_number": exc.get("invoice_number", "N/A"),
                "amount": amt
            })

        return queue


    def record_decision(self, state: Dict[str, Any], exception_number: str,
                        decision: str, reason: str) -> Dict[str, Any]:
        """
        Record a decision back into state.

        Args:
            state: Current session state dict
            exception_number: Invoice number
            decision: Decision (auto_clear, human_queue, reject)
            reason: Reason for decision

        Returns:
            Updated state dict
        """
        if "decisions" not in state:
            state["decisions"] = {}

        state["decisions"][exception_number] = {
            "decision": decision,
            "reason": reason,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

        return state