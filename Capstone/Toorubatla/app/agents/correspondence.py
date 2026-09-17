from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.models.schemas import ExceptionItem, TransactionRecord, VendorEmailDraft


project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")
load_dotenv(project_root.parent / ".env")


class CorrespondenceAgent:
    """Create vendor-facing drafts from verified reconciliation exceptions."""

    @staticmethod
    def _value(value: Any, fallback: str = "Not available in the extracted records") -> str:
        if value is None or value == "":
            return fallback
        return str(value)

    @staticmethod
    def _money(value: Any) -> str:
        if value is None or value == "":
            return "Not available in the extracted records"
        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    def _issue_details(self, issue: ExceptionItem) -> list[str]:
        details = [f"Issue: {issue.code.replace('_', ' ').title()}"]
        if issue.explanation:
            details.append(f"Explanation: {issue.explanation}")

        if issue.code == "AMOUNT_MISMATCH":
            details.extend([
                f"Purchase order amount: {self._money(issue.expected)}",
                f"Invoice amount: {self._money(issue.found)}",
                f"Difference: {self._money(issue.amount_at_risk)}",
            ])
        elif issue.code == "VENDOR_MISMATCH":
            details.extend([
                f"Purchase order vendor: {self._value(issue.expected)}",
                f"Invoice vendor: {self._value(issue.found)}",
            ])
        elif issue.code == "PO_NOT_FOUND":
            details.append(f"Purchase order reference provided: {self._value(issue.found)}")
            details.append("Matching purchase order: Not found in the submitted records")
        elif issue.code == "RECEIPT_NOT_FOUND":
            details.append("Goods receipt or proof of delivery: Not found in the submitted records")
        elif issue.code == "DUPLICATE_INVOICE":
            details.append(f"Invoice reference reported as duplicate: {self._value(issue.found)}")
        elif issue.code == "POLICY_THRESHOLD":
            details.extend([
                f"Approval threshold: {self._value(issue.expected)}",
                f"Invoice amount: {self._money(issue.found)}",
            ])
        elif issue.code == "AMOUNT_OUTLIER":
            details.extend([
                f"Expected range: {self._value(issue.expected)}",
                f"Invoice amount: {self._money(issue.found)}",
            ])
        else:
            details.extend([
                f"Expected value: {self._value(issue.expected)}",
                f"Found value: {self._value(issue.found)}",
            ])
        return details

    def _facts(self, r: TransactionRecord, issues: list[ExceptionItem]) -> dict[str, Any]:
        return {
            "vendor_name": self._value(r.vendor_name.value, "Vendor"),
            "invoice_number": self._value(r.invoice_number.value, "[invoice number]"),
            "po_number": self._value(r.po_number.value, "[PO number]"),
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "expected": issue.expected,
                    "found": issue.found,
                    "amount_at_risk": issue.amount_at_risk,
                    "explanation": issue.explanation,
                }
                for issue in issues
            ],
        }

    def _ai_draft(self, r: TransactionRecord, issues: list[ExceptionItem]) -> str | None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_key_here":
            return None

        facts = self._facts(r, issues)
        prompt = (
            "Write a concise, professional vendor clarification email using only the supplied "
            "verified facts. Do not invent or change invoice numbers, PO numbers, vendors, "
            "amounts, or exception details. Do not approve, reject, or send the invoice. "
            "The subject must include the invoice and PO references. The body must state that "
            "this is a draft requiring human approval and that no payment decision has been made."
        )
        try:
            from openai import OpenAI

            response = OpenAI(api_key=api_key).beta.chat.completions.parse(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.2,
                response_format=VendorEmailDraft,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(facts, default=str)},
                ],
            )
            message = response.choices[0].message
            draft = message.parsed
            if draft is None or not draft.requires_human_approval:
                return None
            required = [facts["invoice_number"], facts["po_number"]]
            if any(reference not in f"{draft.subject}\n{draft.body}" for reference in required):
                return None
            return f"Subject: {draft.subject}\n\n{draft.body}"
        except Exception:
            return None

    def _deterministic_draft(self, r: TransactionRecord, issues: list[ExceptionItem]) -> str:
        invoice_number = self._value(r.invoice_number.value, "[invoice number]")
        po_number = self._value(r.po_number.value, "[PO number]")
        vendor_name = self._value(r.vendor_name.value, "Vendor")
        issue_blocks = []
        for index, issue in enumerate(issues, start=1):
            issue_blocks.append(f"{index}.\n" + "\n".join(self._issue_details(issue)))
        summary = "\n\n".join(issue_blocks) or "No specific discrepancy details were provided."

        return f"""Subject: Clarification required for invoice {invoice_number} / PO {po_number}

Dear {vendor_name} Team,

During reconciliation, we identified the following discrepancy or discrepancies for invoice {invoice_number}:

{summary}

Please review these details and provide the corrected document or supporting information.

This email is a draft and requires human approval before sending. No payment decision has been made while this review is open.

Regards,
Accounts Payable Team"""

    def draft(self, r: TransactionRecord, issues: list[ExceptionItem]) -> str:
        return self._ai_draft(r, issues) or self._deterministic_draft(r, issues)
