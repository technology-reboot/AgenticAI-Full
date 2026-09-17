from __future__ import annotations

from pathlib import Path

import fitz


OUTPUT = Path(__file__).with_name("Correspondence_Agent_Presentation.pdf")

SLIDES = [
    ("Correspondence Agent", ["Vendor clarification drafts for invoice exceptions", "Current implementation: FastAPI + Streamlit + structured AI output", "Draft-only communication with human review"]),
    ("Purpose", ["Creates a professional vendor email when an invoice needs clarification", "Uses verified invoice and exception facts", "Never sends an email automatically", "Never makes the payment approval or rejection decision"]),
    ("When It Runs", ["The pipeline receives uploaded documents", "An invoice is successfully extracted", "At least one exception is detected", "The HITL router sends the invoice to human_review", "pipeline.py calls correspondence.draft(record, issues)"]),
    ("Safe Value Formatting", ["_value() converts available values to text", "Missing values use a clear fallback instead of invented data", "_money() formats numeric values as dollars", "Example: 5900 becomes $5,900.00", "Invalid values are displayed safely instead of crashing"]),
    ("Issue Details", ["_issue_details() converts exception codes into readable email lines", "AMOUNT_MISMATCH shows PO amount, invoice amount, and difference", "VENDOR_MISMATCH shows both vendor values", "PO_NOT_FOUND and RECEIPT_NOT_FOUND explain missing records", "Duplicate, threshold, and outlier issues have dedicated details"]),
    ("Verified Facts Sent to AI", ["_facts() prepares a small structured dictionary", "Includes vendor name, invoice number, PO number, and exceptions", "Includes severity, expected value, found value, and amount at risk", "The AI receives verified facts rather than inventing document values"]),
    ("AI Draft Generation", ["OpenAI is used only when OPENAI_API_KEY is configured", "temperature=0.2 keeps wording consistent and professional", "VendorEmailDraft requires subject, body, and human approval status", "The prompt forbids changing amounts, references, or exception details", "The email must state that human approval is required"]),
    ("Validation and Fallback", ["Reject the AI response if it is missing or does not require approval", "Reject it if the invoice number or PO number is missing", "Any API, network, or parsing failure returns None", "The deterministic template then creates a reliable backup draft"]),
    ("Human Review Workflow", ["Streamlit displays the exception evidence and vendor draft", "Reviewer can Approve case, Reject case, or Request clarification", "The decision is recorded through POST /review", "Approval of a case is separate from sending an email", "The current review store is in memory for the running session"]),
    ("Example and Key Message", ["Invoice INV-1001, PO-5001, amount at risk $5,900", "Exception: receipt or proof of delivery was not found", "Correspondence creates a clarification draft for the vendor", "Human review remains the final control", "Key message: AI assists communication, but does not decide or send"]),
]


def main() -> None:
    document = fitz.open()
    for title, bullets in SLIDES:
        page = document.new_page(width=792, height=612)
        page.draw_rect(fitz.Rect(0, 0, 792, 612), color=(0.05, 0.16, 0.22), fill=(0.05, 0.16, 0.22))
        page.insert_text((55, 82), title, fontsize=30, fontname="hebo", color=(0.35, 0.88, 0.82))
        y = 145
        for bullet in bullets:
            page.insert_text((70, y), "-", fontsize=18, fontname="hebo", color=(0.96, 0.68, 0.22))
            page.insert_textbox(fitz.Rect(100, y - 18, 730, y + 35), bullet, fontsize=18, fontname="helv", color=(0.96, 0.97, 0.98))
            y += 62
        page.insert_text((55, 575), f"Correspondence Agent | {len(document)}", fontsize=10, fontname="helv", color=(0.65, 0.73, 0.76))
    document.save(OUTPUT)
    document.close()
    print(OUTPUT)


if __name__ == "__main__":
    main()
